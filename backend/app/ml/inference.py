from dataclasses import dataclass
from time import perf_counter

import tensorflow as tf

from app.core.config import Settings
from app.core.safety_gate import SafetyDecision, SafetyFilter

from .model_loader import DummyPredictor, ModelBundle
from .preprocessor import PreparedImage, area_resize, normalize_for_convnext
from .xai_engine import Explainability, explain_batch


@dataclass(frozen=True)
class InferenceResult:
    decision: SafetyDecision
    xai: Explainability | None
    inference_time_ms: float
    xai_time_ms: float


def _probabilities(model: ModelBundle, batch: tf.Tensor, views: int):
    transforms = [lambda x: x]
    if views == 5:
        transforms.extend((
            tf.image.flip_left_right, lambda x: tf.image.rot90(x, k=1), lambda x: tf.image.rot90(x, k=3),
            lambda x: area_resize(x[:, 16:304, 16:304, :]),
        ))
    # One bounded forward pass per view keeps accelerator and CPU memory independent of TTA count.
    probabilities = []
    for transform in transforms:
        inputs = normalize_for_convnext(transform(batch))
        logits = model.sub_logits_model(inputs, training=False)
        probabilities.append(tf.nn.softmax(tf.cast(logits, tf.float32), axis=-1))
    by_view = tf.stack(probabilities)
    mean = tf.reduce_mean(by_view, axis=0)
    if views == 1:
        return mean.numpy(), [None] * int(batch.shape[0])
    winners = tf.argmax(mean, axis=-1)
    agreement = tf.cast(tf.argmax(by_view, axis=-1) == winners[None, :], tf.float32)
    return mean.numpy(), tf.reduce_mean(agreement, axis=0).numpy().tolist()


def classify_batch(
    model: ModelBundle | DummyPredictor, images: list[PreparedImage], settings: Settings, safety: SafetyFilter,
) -> list[InferenceResult]:
    start = perf_counter()
    if isinstance(model, DummyPredictor):
        decisions = [
            safety.evaluate(p, None, is_mock=True)
            for p in model.probabilities(len(images))
        ]
        time_ms = (perf_counter() - start) * 1000 / len(images)
        return [InferenceResult(decision, None, time_ms, 0.0) for decision in decisions]

    probs, stability = _probabilities(model, tf.stack([image.model_rgb for image in images]), int(settings.tta_views))
    decisions = [
        safety.evaluate(p, vote, adaptive_enabled=settings.adaptive_assessment_enabled)
        for p, vote in zip(probs, stability, strict=True)
    ]
    after_inference = perf_counter()
    explanations = explain_batch(model, images, [item.top_index for item in decisions])
    after_xai = perf_counter()
    return [
        InferenceResult(decision, explanation,
                        (after_inference - start) * 1000 / len(images),
                        (after_xai - after_inference) * 1000 / len(images))
        for decision, explanation in zip(decisions, explanations, strict=True)
    ]
