"""Opt-in adapter for the existing FastAPI routes, history and image storage."""

from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np

from PIL import Image, UnidentifiedImageError

from app.ml.preprocessor import ImagePreprocessor, InvalidImage, PreparedImage
from app.ml.types import Explainability, InferenceResult

from .runtime import Runtime, area_resize, decode, overlay_jpeg
from .u2netp import U2NetP


LARGE_RGB_BYTES = 8 * 1024 * 1024


@dataclass(frozen=True)
class OnnxBundle:
    runtime: Runtime
    checkpoint: str
    class_labels: tuple[str, ...]


def load_model(settings, class_labels, *, reclaim_memory=False):
    directory = Path(os.environ.get("ONNX_MODEL_DIR", Path(__file__).with_name("artifacts")))
    runtime = Runtime(directory, threads=int(os.environ.get("ONNX_THREADS", "2")), reclaim_memory=reclaim_memory)
    if tuple(runtime.manifest["labels"]) != tuple(class_labels):
        raise ValueError("ONNX label order disagrees with the configured safety thresholds.")
    if hashlib.sha256(settings.thresholds_path.read_bytes()).hexdigest() != runtime.manifest["thresholds_sha256"]:
        raise ValueError("Safety thresholds changed since this export was validated.")
    runtime.predict(np.zeros((320, 320, 3), dtype=np.float32), views=1)
    return OnnxBundle(runtime, "convnext_tiny_onnx_fp32.keras", tuple(class_labels))


class OnnxPreprocessor(ImagePreprocessor):
    def __init__(self, max_pixels, smart_crop, *, mask_size=320, reclaim_memory=False):
        super().__init__(max_pixels, smart_crop=False)
        if smart_crop:
            self._predict_mask = U2NetP(mask_size, reclaim_memory=reclaim_memory)

    def prepare(self, contents, claimed_type):
        try:
            rgb, mime, extension = decode(contents, claimed_type, self.max_pixels)
        except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
            raise InvalidImage(str(exc) or "Không đọc được ảnh JPEG, PNG hoặc WebP hợp lệ.") from exc
        height, width = rgb.shape[:2]
        if self._predict_mask is not None and height != width and rgb.nbytes >= LARGE_RGB_BYTES:
            # Release the full RGB image before U²-NetP allocates its activations.
            preview, scale = self._subject_preview(rgb)
            del rgb
            x, y, side, found = self._subject_square(height, width, preview, scale)
            crop, _, _ = decode(contents, claimed_type, self.max_pixels, crop_box=(x, y, side))
        else:
            x, y, side, found = self._square(rgb)
            crop = rgb[y:y + side, x:x + side]
        if self._predict_mask is not None:
            pixels = cv2.resize(crop, (320, 320), interpolation=cv2.INTER_AREA).astype(np.float32)
        else:
            pixels = area_resize(crop)
        return PreparedImage(pixels, (x, y, side), "subject_center" if found else "image_center", mime, extension)


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
