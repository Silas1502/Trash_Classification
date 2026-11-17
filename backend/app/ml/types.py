"""Shared inference contracts, importable without a training framework."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import numpy as np

from app.core.safety_gate import SafetyDecision

IMAGE_SIZE = (320, 320)
SPATIAL_LAYER = "convnext_tiny_stage_3_block_2_identity"


@dataclass(frozen=True)
class ModelBundle:
    sub_logits_model: Any
    spatial: Any
    head: Any
    checkpoint: str
    class_labels: tuple[str, ...]


@dataclass(frozen=True)
class DummyPredictor:
    class_labels: tuple[str, ...]

    def probabilities(self, image_count: int) -> np.ndarray:
        return np.random.default_rng().dirichlet(np.ones(len(self.class_labels)), size=image_count)


@dataclass(frozen=True)
class Explainability:
    gradcam_jpeg: bytes
    spatial_energy_jpeg: bytes


@dataclass(frozen=True)
class InferenceResult:
    decision: SafetyDecision
    xai: Explainability | None
    inference_time_ms: float
    xai_time_ms: float


BatchClassifier = Callable[..., list[InferenceResult]]
