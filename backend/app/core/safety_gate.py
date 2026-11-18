import json
from collections.abc import Sequence
from dataclasses import dataclass
from math import isclose, isfinite
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

from app.schemas.prediction import DecisionCode, PipelineType, PredictionStatus, WasteType

Fraction = Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)]
Threshold = Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)]


class WasteDetail(BaseModel):
    index: int
    name_vi: WasteType
    suggestion: str = Field(min_length=1)


class WasteClasses(BaseModel):
    labels: tuple[str, ...]
    details: dict[str, WasteDetail]

    @model_validator(mode="after")
    def check_order(self):
        if len(self.labels) < 2 or len(set(self.labels)) != len(self.labels):
            raise ValueError("classes.labels must contain distinct labels.")
        if set(self.details) != set(self.labels) or any(
            self.details[label].index != index for index, label in enumerate(self.labels)
        ):
            raise ValueError("classes.details must match the labels and their order.")
        return self


class GateThresholds(BaseModel):
    tau_conf_by_idx: dict[int, Threshold] | None = None
    tau_conf_by_name: dict[str, Threshold] | None = None
    tau_margin: Threshold


class AdaptiveRules(BaseModel):
    w_conf: Fraction
    w_margin: Fraction
    conf_floor_tier1: Fraction
    conf_floor_tier2: Fraction
    tolerance_score: Fraction
    tta_stability_threshold: Threshold = 0.999

    @model_validator(mode="after")
    def check_weights(self):
        if not isclose(self.w_conf + self.w_margin, 1.0):
            raise ValueError("Adaptive weights must sum to 1.")
        return self


class SafetyThresholds(BaseModel):
    classes: WasteClasses
    gate_thresholds: GateThresholds
    adaptive_safety_rules: AdaptiveRules

    @model_validator(mode="after")
    def check_thresholds(self):
        labels = self.classes.labels
        by_name = self.gate_thresholds.tau_conf_by_name
        by_index = self.gate_thresholds.tau_conf_by_idx
        if by_name is None and by_index is None:
            raise ValueError("At least one confidence threshold map is required.")
        if by_name is not None and set(by_name) != set(labels):
            raise ValueError("tau_conf_by_name must cover all model classes.")
        if by_index is not None and set(by_index) != set(range(len(labels))):
            raise ValueError("tau_conf_by_idx must cover all model class indices.")
        if by_name is not None and by_index is not None and any(
            not isclose(by_name[label], by_index[index]) for index, label in enumerate(labels)
        ):
            raise ValueError("Confidence thresholds by name and index disagree.")
        return self

    def confidence_for(self, index: int) -> float:
        by_index = self.gate_thresholds.tau_conf_by_idx
        if by_index is not None:
            return by_index[index]
        return self.gate_thresholds.tau_conf_by_name[self.classes.labels[index]]

    def confidence_by_name(self) -> dict[str, float]:
        return {label: self.confidence_for(index) for index, label in enumerate(self.classes.labels)}


@dataclass(frozen=True)
class SafetyDecision:
    top_index: int
    waste_type: WasteType
    confidence: float
    runner_up_type: WasteType
    runner_up_probability: float
    margin: float
    confidence_threshold: float
    margin_threshold: float
    confidence_gate_passed: bool
    margin_gate_passed: bool
    composite_score: float
    tta_stability: float | None
    decision_tier: str
    decision: DecisionCode
    reason: str
    pipeline_type: PipelineType
    status: PredictionStatus
    suggestion: str


@dataclass(frozen=True)
class SafetyFilter:
    thresholds: SafetyThresholds
    source: dict

    @classmethod
    def load(cls, path: Path) -> "SafetyFilter":
        try:
            source = json.loads(path.read_text(encoding="utf-8-sig"))
            return cls(SafetyThresholds.model_validate(source), source)
        except (OSError, ValueError) as exc:
            raise ValueError(f"Không thể nạp cấu hình an toàn tại {path}: {exc}") from exc

    def evaluate(
        self, probabilities: Sequence[float], tta_stability: float | None, *, adaptive_enabled: bool = False,
        is_mock: bool = False,
    ) -> SafetyDecision:
        scores = [float(value) for value in probabilities]
        cfg = self.thresholds
        if (
            len(scores) != len(cfg.classes.labels)
            or any(not isfinite(value) or not 0 <= value <= 1 for value in scores)
            or not isclose(sum(scores), 1.0, abs_tol=1e-5)
        ):
            raise ValueError("Invalid model probability vector.")

        first, second, *_ = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)
        confidence = scores[first]
        margin = confidence - scores[second]
        tau_conf = cfg.confidence_for(first)
        tau_margin = cfg.gate_thresholds.tau_margin
        detail = cfg.classes.details[cfg.classes.labels[first]]
        rules = cfg.adaptive_safety_rules
        s_conf, s_margin = confidence / tau_conf, margin / tau_margin
        composite = rules.w_conf * s_conf + rules.w_margin * s_margin
        confidence_passed = confidence >= tau_conf
        margin_passed = margin >= tau_margin

        automatic = not is_mock
        if is_mock:
            tier = "Mock: Dự đoán mô phỏng"
            reason = "Thiếu checkpoint. Xác suất được tạo ngẫu nhiên để kiểm thử API."
        elif confidence_passed and margin_passed:
            tier = "Tier 1: Đạt chuẩn cơ sở"
            reason = f"Đạt cả hai chốt (Chốt 1: {s_conf:.2f}x | Chốt 2: {s_margin:.2f}x)."
        elif adaptive_enabled and composite >= 1.0 and confidence >= rules.conf_floor_tier1:
            tier = "Tier 2: Cứu nguy bù trừ"
            reason = f"Điểm bù trừ {composite:.1%} đạt ngưỡng 100%."
        elif (
            adaptive_enabled and composite >= rules.tolerance_score and tta_stability is not None
            and tta_stability >= rules.tta_stability_threshold and confidence >= rules.conf_floor_tier2
        ):
            tier = "Tier 3: Bảo lãnh đồng thuận TTA"
            reason = f"Điểm bù trừ {composite:.1%}, đồng thuận TTA {tta_stability:.1%}."
        else:
            automatic = False
            tier = "Thủ công"
            violations = []
            if not confidence_passed:
                violations.append(f"Chốt 1 ({detail.name_vi}): {confidence:.2%} < {tau_conf:.2%}")
            if not margin_passed:
                violations.append(f"Chốt 2 (biên): {margin:.2%} < {tau_margin:.2%}")
            reason = " | ".join(violations)

        suggestion = detail.suggestion
        if not automatic:
            suggestion = f"Kiểm tra thủ công loại rác trước khi xử lý. Nếu xác nhận là {detail.name_vi.lower()}: {suggestion}"
        return SafetyDecision(
            top_index=first, waste_type=detail.name_vi, confidence=confidence,
            runner_up_type=cfg.classes.details[cfg.classes.labels[second]].name_vi,
            runner_up_probability=scores[second], margin=margin,
            confidence_threshold=tau_conf, margin_threshold=tau_margin, confidence_gate_passed=confidence_passed,
            margin_gate_passed=margin_passed, composite_score=composite, tta_stability=tta_stability,
            decision_tier=tier, reason=reason, decision="Tu_Dong_Gap" if automatic else "Chuyen_Khay_Thu_Cong",
            pipeline_type="Tự động" if automatic else "Thủ công",
            status="Thành công" if automatic else "Cần kiểm tra", suggestion=suggestion,
        )
