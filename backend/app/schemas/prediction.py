from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

WasteType = Literal["Nhựa", "Giấy", "Kim loại", "Thủy tinh", "Hữu cơ", "Khác"]
PipelineType = Literal["Tự động", "Thủ công", "Chưa thẩm định"]
DecisionCode = Literal["Tu_Dong_Gap", "Chuyen_Khay_Thu_Cong", "Khong_Tham_Dinh"]
PredictionStatus = Literal["Thành công", "Cần kiểm tra", "Chưa thẩm định"]
Percent = Annotated[float, Field(ge=0, le=100)]
DurationMs = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class PredictionResult(BaseModel):
    id: UUID
    file_name: str
    image_url: str | None
    xai_overlay_url: str | None
    xai_energy_overlay_url: str | None = None
    waste_type: WasteType
    confidence: Percent
    checkpoint_1: Percent
    checkpoint_2: Percent
    margin: Percent
    confidence_gate_passed: bool
    margin_gate_passed: bool
    composite_score: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None = None
    tta_stability: Percent | None = None
    decision_tier: str | None = None
    decision: DecisionCode | None = None
    reason: str | None = None
    is_mock: bool = False
    pipeline_type: PipelineType
    status: PredictionStatus
    suggestion: str
    created_at: datetime


class PredictionResponse(PredictionResult):
    processing_time_ms: DurationMs


class PredictionMetadata(BaseModel):
    file_size: int
    mime_type: str
    inference_time_ms: float
    xai_time_ms: float
    model_version: str
    tta_views: Literal[1, 5]
    crop_box: tuple[int, int, int]  # x, y, side in the decoded original
    crop_strategy: Literal["subject_center", "image_center"]
    processing_time_ms: DurationMs | None = None


class BatchError(BaseModel):
    index: int
    file_name: str
    code: str
    message: str


class BatchResult(BaseModel):
    batch_id: UUID
    total_images: int
    processed_images: int  # Successful results and terminal errors.
    pending_images: int
    succeeded_images: int
    failed_images: int
    completion_rate: Percent
    results: list[PredictionResponse]
    errors: list[BatchError]
