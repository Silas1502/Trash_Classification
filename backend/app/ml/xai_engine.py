
import cv2
import numpy as np
import tensorflow as tf

from .model_loader import IMAGE_SIZE, ModelBundle
from .preprocessor import PreparedImage, normalize_for_convnext
from .types import Explainability

ALPHA = 0.48


def normalize_map(values: np.ndarray) -> np.ndarray:
    lo, hi = float(values.min()), float(values.max())
    if not np.isfinite([lo, hi]).all():
        raise ValueError("XAI produced non-finite activations.")
    if hi - lo < 1e-8:
        return np.zeros_like(values, dtype=np.float32)
    return ((values - lo) / (hi - lo)).astype(np.float32)


def _overlay_jpeg(rgb: np.ndarray, heat: np.ndarray) -> bytes:
    # Match Cell 12: display the heatmap on the 320×320 RGB model input before normalization.
    heat = cv2.resize(heat, IMAGE_SIZE, interpolation=cv2.INTER_CUBIC)
    heat = np.uint8(np.round(np.clip(heat, 0, 1) * 255))
    jet = cv2.applyColorMap(heat, cv2.COLORMAP_JET)
    crop = np.clip(rgb, 0, 255).astype(np.uint8)
    base = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)
    overlay = cv2.addWeighted(base, 1 - ALPHA, jet, ALPHA, 0)
    ok, encoded = cv2.imencode(".jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise RuntimeError("Failed to encode the XAI overlay.")
    return encoded.tobytes()


def explain_batch(model: ModelBundle, images: list[PreparedImage], targets: list[int]) -> list[Explainability]:
    inputs = normalize_for_convnext(tf.stack([image.model_rgb for image in images]))
    features, skip = model.spatial(inputs, training=False)
    with tf.GradientTape(watch_accessed_variables=False) as tape:
        tape.watch(features)
        logits = model.head([features, skip], training=False)
        # Each row describes an independent image; no batch-coupled layers run in inference mode.
        target_scores = tf.gather(logits, targets, axis=1, batch_dims=1)
        total_score = tf.reduce_sum(target_scores)
    gradients = tape.gradient(total_score, features)
    if gradients is None:
        raise RuntimeError("Classifier logits are disconnected from the spatial layer.")

    return render_explanations(
        [image.model_rgb.numpy() for image in images],
        tf.cast(features, tf.float32).numpy(),
        tf.cast(gradients, tf.float32).numpy(),
    )


def render_explanations(
    images: list[np.ndarray], features: np.ndarray, gradients: np.ndarray,
) -> list[Explainability]:
    energy = np.sqrt(np.mean(np.square(features), axis=-1))
    weights = gradients.mean(axis=(1, 2))
    cam = np.einsum("bhwc,bc->bhw", features, weights)
    relu = np.maximum(cam, 0)
    results = []
    for image, energy_map, raw_cam, relu_cam in zip(images, energy, cam, relu, strict=True):
        # Notebook Cell 12 uses absolute evidence if no positive region exists.
        if float(relu_cam.max()) < 1e-8:
            relu_cam = np.abs(raw_cam)
        results.append(Explainability(
            _overlay_jpeg(image, normalize_map(relu_cam)),
            _overlay_jpeg(image, normalize_map(energy_map)),
        ))
    return results
