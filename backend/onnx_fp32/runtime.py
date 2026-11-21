"""TensorFlow-free FP32 inference and Grad-CAM using two ONNX graphs."""

from dataclasses import dataclass
from functools import lru_cache
from io import BytesIO
import hashlib
import json
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from PIL import Image, ImageOps

from .memory import release_file_cache, trim_heap

SIZE = 320


@lru_cache(maxsize=32)
def _area_spans(length, output):
    # Coordinate/overlap rules follow TensorFlow 2.20 ResizeAreaOp:
    # tensorflow/core/kernels/image/resize_area_op.cc (Apache-2.0).
    scale = np.float32(length / output)
    spans = []
    for i in range(output):
        start, end = np.float32(i) * scale, np.float32(i + 1) * scale
        low, high = int(np.floor(start)), int(np.ceil(end))
        positions = np.arange(low, high, dtype=np.float32)
        # TF uses scale (not end-start) when the entire output interval lies
        # inside one source pixel. This matters for very small inputs.
        weights = np.where(
            positions < start,
            np.where(positions + 1 > end, scale, positions + 1 - start),
            np.where(positions + 1 > end, end - positions, np.float32(1)),
        ).astype(np.float32)
        indices = np.clip(np.arange(low, high), 0, length - 1)
        spans.append((indices, weights / scale))
    return spans


def area_resize(rgb, height=SIZE, width=SIZE):
    """Box/area resampling with TensorFlow's asymmetric float32 coordinates.

    OpenCV INTER_AREA uses different upsampling rules. In particular it must
    not replace the AREA resize of the 288x288 fifth TTA view.
    """
    # Keep the decoded uint8 image compact. Casting a 16 MP RGB image wholesale
    # would allocate another 192 MB before resizing. Each small stripe is
    # promoted by its float32 weights instead, without changing the arithmetic.
    rgb = np.asarray(rgb)
    if rgb.shape[:2] == (height, width):
        return np.ascontiguousarray(rgb, dtype=np.float32)
    intermediate = np.empty((height, rgb.shape[1], 3), dtype=np.float32)
    for i, (indices, weights) in enumerate(_area_spans(rgb.shape[0], height)):
        intermediate[i] = np.sum(rgb[indices] * weights[:, None, None], axis=0, dtype=np.float32)
    output = np.empty((height, width, 3), dtype=np.float32)
    for i, (indices, weights) in enumerate(_area_spans(rgb.shape[1], width)):
        output[:, i] = np.sum(intermediate[:, indices] * weights[None, :, None], axis=1, dtype=np.float32)
    return output


@dataclass(frozen=True)
class Prepared:
    model_rgb: np.ndarray
    crop_box: tuple[int, int, int]
    crop_strategy: str = "image_center"


def decode(contents, mime=None, max_pixels=16_000_000, *, crop_box=None):
    with Image.open(BytesIO(contents), formats=["JPEG", "PNG", "WEBP"]) as image:
        actual = Image.MIME[image.format]
        if mime is not None and mime != actual:
            raise ValueError("Image contents disagree with MIME type.")
        if image.width * image.height > max_pixels:
            raise ValueError("Image exceeds the configured pixel limit.")
        if getattr(image, "is_animated", False):
            raise ValueError("Animated images are unsupported.")
        image.verify()
    with Image.open(BytesIO(contents)) as image:
        # Match EXIF orientation and RGB conversion without holding several
        # full-resolution PIL images plus a full tobytes() copy simultaneously.
        ImageOps.exif_transpose(image, in_place=True)
        if crop_box is None:
            left, top = 0, 0
            width, height = image.size
        else:
            left, top, side = crop_box
            width = height = side
        rgb = np.empty((height, width, 3), dtype=np.uint8)
        for y in range(0, height, 128):
            end = min(y + 128, height)
            with image.crop((left, top + y, left + width, top + end)) as stripe:
                if stripe.mode == "RGB":
                    rgb[y:end] = np.asarray(stripe)
                else:
                    with stripe.convert("RGB") as converted:
                        rgb[y:end] = np.asarray(converted)
    extension = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}[actual]
    return rgb, actual, extension


def prepare(contents, mime=None, max_pixels=16_000_000):
    rgb, _, _ = decode(contents, mime, max_pixels)
    height, width = rgb.shape[:2]
    side = min(height, width)
    x, y = (width - side) // 2, (height - side) // 2
    return Prepared(area_resize(rgb[y:y + side, x:x + side]), (x, y, side))


def normalize_map(values):
    low, high = float(values.min()), float(values.max())
    if not np.isfinite([low, high]).all():
        raise ValueError("Non-finite XAI activations.")
    if high - low < 1e-8:
        return np.zeros_like(values, dtype=np.float32)
    return ((values - low) / (high - low)).astype(np.float32)


def heatmaps(features, gradients):
    energy = np.sqrt(np.mean(np.square(features), axis=-1))
    weights = gradients.mean(axis=(1, 2))
    raw = np.einsum("bhwc,bc->bhw", features, weights)
    relu = np.maximum(raw, 0)
    cams = [normalize_map(np.abs(a) if float(b.max()) < 1e-8 else b) for a, b in zip(raw, relu)]
    return np.stack(cams), np.stack([normalize_map(a) for a in energy])


def overlay_jpeg(rgb, heat):
    heat = cv2.resize(heat, (SIZE, SIZE), interpolation=cv2.INTER_CUBIC)
    heat = np.uint8(np.round(np.clip(heat, 0, 1) * 255))
    jet = cv2.applyColorMap(heat, cv2.COLORMAP_JET)
    base = cv2.cvtColor(np.clip(rgb, 0, 255).astype(np.uint8), cv2.COLOR_RGB2BGR)
    overlay = cv2.addWeighted(base, 0.52, jet, 0.48, 0)
    ok, encoded = cv2.imencode(".jpg", overlay, [cv2.IMWRITE_JPEG_QUALITY, 90])
    if not ok:
        raise RuntimeError("Could not encode explanation.")
    return encoded.tobytes()


class Runtime:
    def __init__(self, directory=None, threads=2, *, reclaim_memory=False):
        import onnxruntime as ort

        directory = Path(directory or Path(__file__).with_name("artifacts"))
        self.manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
        if self.manifest["precision"] != "float32":
            raise ValueError("This runtime requires the validated FP32 export.")
        for name in ("forward.onnx", "gradient.onnx"):
            path = directory / name
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            if digest.hexdigest() != self.manifest["files"][name]["sha256"]:
                raise ValueError(f"ONNX artifact disagrees with manifest: {name}")
            if reclaim_memory:
                release_file_cache(path)
        options = ort.SessionOptions()
        options.intra_op_num_threads = threads
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        # Do not retain a large CPU arena after a request completes.
        options.enable_cpu_mem_arena = False
        self.forward = ort.InferenceSession(str(directory / "forward.onnx"), options, providers=["CPUExecutionProvider"])
        if reclaim_memory:
            release_file_cache(directory / "forward.onnx")
            trim_heap()
        self.gradient = ort.InferenceSession(str(directory / "gradient.onnx"), options, providers=["CPUExecutionProvider"])
        if reclaim_memory:
            release_file_cache(directory / "gradient.onnx")
            trim_heap()
        self.forward_names = [value.name for value in self.forward.get_outputs()]
        self.rgb_name = self.forward.get_inputs()[0].name
        self.gradient_names = [value.name for value in self.gradient.get_inputs()]

    def predict(self, rgb, views=5):
        if views not in (1, 5):
            raise ValueError("Only the original 1-view or 5-view TTA is supported.")
        started = perf_counter()
        rgb = np.asarray(rgb, dtype=np.float32)
        if rgb.shape != (SIZE, SIZE, 3) or not np.isfinite(rgb).all():
            raise ValueError("Expected one finite 320x320 RGB float32 image.")
        first = self.forward.run(None, {self.rgb_name: rgb[None]})
        logits, features, skip = first
        logits_by_view = [logits]
        transforms = [] if views == 1 else [
            lambda: np.flip(rgb, axis=1), lambda: np.rot90(rgb, 1),
            lambda: np.rot90(rgb, 3), lambda: area_resize(rgb[16:304, 16:304]),
        ]
        for transform in transforms:
            image = np.ascontiguousarray(transform()[None], dtype=np.float32)
            logits_by_view.append(self.forward.run(self.forward_names[:1], {self.rgb_name: image})[0])
        logits_by_view = np.stack(logits_by_view)
        exp = np.exp(logits_by_view - logits_by_view.max(axis=-1, keepdims=True))
        by_view = exp / exp.sum(axis=-1, keepdims=True)
        probabilities = by_view.mean(axis=0)[0]
        target = int(probabilities.argmax())
        stability = None if views == 1 else float((by_view.argmax(axis=-1) == target).mean(dtype=np.float32))
        after_inference = perf_counter()
        # The graph includes the ORIGINAL TF gradient expression, not an XAI substitute.
        gradient_inputs = dict(zip(self.gradient_names, [features, skip, np.array([target], dtype=np.int32)]))
        _, gradients = self.gradient.run(None, gradient_inputs)
        cam, energy = heatmaps(features, gradients)
        after_xai = perf_counter()
        return {
            "probabilities": probabilities, "tta_stability": stability, "target": target,
            "logits_by_view": logits_by_view[:, 0], "features": features, "gradients": gradients,
            "gradcam": cam[0], "spatial_energy": energy[0],
            "inference_time_ms": (after_inference - started) * 1000,
            "xai_time_ms": (after_xai - after_inference) * 1000,
        }
