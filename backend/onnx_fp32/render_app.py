"""Render probe. Run representative synthetic images once, before serving traffic."""

from io import BytesIO
import json
import os
from pathlib import Path
from shutil import disk_usage
from tempfile import gettempdir
from time import perf_counter, process_time

from PIL import Image, ImageDraw

from app.core.config import Settings
from app.core.safety_gate import SafetyFilter
from app.main import create_app

from .adapter import OnnxPreprocessor, classify_batch, load_model


def counters() -> dict:
    root = Path("/sys/fs/cgroup")
    readings = {}
    for name in ("memory.current", "memory.peak", "memory.max"):
        path = root / name
        if path.is_file():
            value = path.read_text().strip()
            readings[name] = int(value) if value.isdecimal() else value
    for name, keys in (("memory.stat", {"anon", "file"}), ("memory.events", {"oom", "oom_kill"})):
        path = root / name
        if path.is_file():
            for line in path.read_text().splitlines():
                key, value = line.split()
                if key in keys:
                    readings[f"{name}.{key}"] = int(value)
    readings["filesystem_free_bytes"] = disk_usage(gettempdir()).free
    return readings


def load_with_probe(settings, class_labels):
    started = perf_counter()
    model = load_model(settings, class_labels)
    print("RENDER_ONNX " + json.dumps({
        "stage": "loaded", "wall_seconds": round(perf_counter() - started, 3), **counters(),
    }), flush=True)
    if os.environ.get("ONNX_STARTUP_PROBE") == "1":
        processor = OnnxPreprocessor(settings.max_image_pixels, settings.smart_crop)
        safety = SafetyFilter.load(settings.thresholds_path)
        for width, height, mode, fmt, mime in ((720, 720, "RGB", "JPEG", "image/jpeg"),
                                                (5000, 3200, "RGBA", "PNG", "image/png")):
            with BytesIO() as stream, Image.new(mode, (width, height), "#617b9c") as image:
                ImageDraw.Draw(image).rectangle((width // 8, height // 4, width // 2, height * 3 // 4), fill="#754445")
                image.save(stream, format=fmt)
                contents = stream.getvalue()
            started, cpu_started = perf_counter(), process_time()
            before = counters()
            prepared = processor.prepare(contents, mime)
            result, = classify_batch(model, [prepared], settings, safety)
            print("RENDER_ONNX " + json.dumps({
                "stage": "prediction", "pixels": width * height, "format": fmt,
                "crop_strategy": prepared.crop_strategy,
                "wall_seconds": round(perf_counter() - started, 3),
                "python_cpu_seconds": round(process_time() - cpu_started, 3),
                "gradcam_bytes": len(result.xai.gradcam_jpeg),
                "spatial_energy_bytes": len(result.xai.spatial_energy_jpeg),
                "before": before, "after": counters(),
            }), flush=True)
    return model


class UploadMemoryLog:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if (scope["type"] != "http" or scope["method"] != "POST"
                or scope["path"].rstrip("/") not in ("/api/v1/predict/single", "/api/v1/predict/batch")):
            await self.app(scope, receive, send)
            return
        before = counters()
        started = perf_counter()
        try:
            await self.app(scope, receive, send)
        finally:
            print("RENDER_ONNX " + json.dumps({
                "stage": "upload_finished", "path": scope["path"],
                "wall_seconds": round(perf_counter() - started, 3),
                "before": before, "after": counters(),
            }), flush=True)


app = create_app(
    Settings(), batch_classifier=classify_batch, model_loader=load_with_probe,
    preprocessor_factory=OnnxPreprocessor,
)
if os.environ.get("ONNX_UPLOAD_MEMORY_LOG") == "1":
    app.add_middleware(UploadMemoryLog)
