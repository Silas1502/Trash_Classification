"""Opt-in adapter for the existing FastAPI routes, history and image storage."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from time import perf_counter

import numpy as np

from PIL import Image, UnidentifiedImageError

from app.ml.preprocessor import ImagePreprocessor, InvalidImage, PreparedImage
from app.ml.types import Explainability, InferenceResult

from .runtime import Runtime, area_resize, decode, overlay_jpeg


@dataclass(frozen=True)
class OnnxBundle:
    runtime: Runtime
    checkpoint: str
    class_labels: tuple[str, ...]


def load_model(settings, class_labels):
    if settings.smart_crop:
        raise ValueError("The validated ONNX experiment requires SMART_CROP=false.")
    directory = Path(os.environ.get("ONNX_MODEL_DIR", Path(__file__).with_name("artifacts")))
    runtime = Runtime(directory, threads=int(os.environ.get("ONNX_THREADS", "2")))
    if tuple(runtime.manifest["labels"]) != tuple(class_labels):
        raise ValueError("ONNX label order disagrees with the configured safety thresholds.")
    if hashlib.sha256(settings.thresholds_path.read_bytes()).hexdigest() != runtime.manifest["thresholds_sha256"]:
        raise ValueError("Safety thresholds changed since this export was validated.")
    runtime.predict(np.zeros((320, 320, 3), dtype=np.float32), views=1)
    return OnnxBundle(runtime, "convnext_tiny_onnx_fp32.keras", tuple(class_labels))


class OnnxPreprocessor(ImagePreprocessor):
    def __init__(self, max_pixels, smart_crop):
        if smart_crop:
            raise ValueError("SMART_CROP is not part of this ONNX validation.")
        super().__init__(max_pixels, smart_crop)

    def prepare(self, contents, claimed_type):
        try:
            rgb, mime, extension = decode(contents, claimed_type, self.max_pixels)
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
            raise InvalidImage(str(exc) or "Không đọc được ảnh JPEG, PNG hoặc WebP hợp lệ.") from exc
        x, y, side, _ = self._square(rgb)
        return PreparedImage(area_resize(rgb[y:y + side, x:x + side]), (x, y, side), "image_center", mime, extension)


def classify_batch(model, images, settings, safety):
    results = []
    # Batch API contract is retained, but each image is computed sequentially.
    for image in images:
        output = model.runtime.predict(image.model_rgb, views=int(settings.tta_views))
        decision = safety.evaluate(output["probabilities"], output["tta_stability"],
                                   adaptive_enabled=settings.adaptive_assessment_enabled)
        rendering_started = perf_counter()
        xai = Explainability(
            overlay_jpeg(image.model_rgb, output["gradcam"]),
            overlay_jpeg(image.model_rgb, output["spatial_energy"]),
        )
        results.append(InferenceResult(decision, xai, output["inference_time_ms"],
                                       output["xai_time_ms"] + (perf_counter() - rendering_started) * 1000))
    return results
