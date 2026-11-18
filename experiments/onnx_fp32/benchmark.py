"""Measure separate Python processes, including model load, TTA, XAI and JPEGs."""

import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from .export import DEFAULT_CHECKPOINT, DEFAULT_OUTPUT, ROOT


def worker(args):
    worker_started = time.perf_counter()
    from PIL import Image
    selected = json.loads((args.results / "cases.json").read_text(encoding="utf-8"))
    selected = [selected[i + offset] for i in range(0, len(selected), len(selected)//4)
                for offset in range(args.images_per_class)]
    if args.engine == "tensorflow":
        os.environ["KERAS_BACKEND"] = "tensorflow"
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        import tensorflow as tf
        tf.config.threading.set_intra_op_parallelism_threads(args.threads)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        sys.path.insert(0, str(ROOT / "backend"))
        from app.core.config import Settings
        from app.core.safety_gate import SafetyFilter
        from app.ml.model_loader import load_model
        from app.ml.preprocessor import ImagePreprocessor
        from app.ml.inference import classify_batch
        settings = Settings(_env_file=None, model_path=args.checkpoint.resolve(), inference_batch_size=1)
        safety = SafetyFilter.load(settings.thresholds_path)
        model = load_model(settings, safety.thresholds.classes.labels)
        processor = ImagePreprocessor(settings.max_image_pixels, False)
        def predict(contents, mime):
            return classify_batch(model, [processor.prepare(contents, mime)], settings, safety)
    else:
        from .runtime import Runtime, prepare, overlay_jpeg
        model = Runtime(args.artifacts, args.threads)
        def predict(contents, mime):
            rgb = prepare(contents, mime).model_rgb
            result = model.predict(rgb)
            return overlay_jpeg(rgb, result["gradcam"]), overlay_jpeg(rgb, result["spatial_energy"])
    import psutil
    process = psutil.Process()
    loaded_rss = process.memory_info().rss
    load_seconds = time.perf_counter() - worker_started
    times = []
    cpu_before = process.cpu_times()
    for _ in range(args.repeat):
        for case in selected:
            path = ROOT / case["path"]
            with Image.open(path) as image:
                mime = Image.MIME[image.format]
            started = time.perf_counter()
            prediction = predict(path.read_bytes(), mime)
            times.append(time.perf_counter() - started)
            del prediction
    cpu_after = process.cpu_times()
    import statistics
    package = "tensorflow" if args.engine == "tensorflow" else "onnxruntime"
    location = Path(importlib.metadata.distribution(package).locate_file(package))
    disk_bytes = sum(p.stat().st_size for p in location.rglob("*") if p.is_file())
    memory = process.memory_info()
    report = {
        "engine": args.engine, "platform": sys.platform, "threads": args.threads,
        "requests": len(times), "tta_views": 5, "xai": ["Grad-CAM", "Spatial Energy"],
        "loaded_rss_bytes": loaded_rss, "final_rss_bytes": memory.rss,
        "load_seconds": load_seconds,
        "os_peak_working_set_bytes": getattr(memory, "peak_wset", None),
        "median_request_ms": statistics.median(times) * 1000,
        "mean_request_ms": statistics.mean(times) * 1000,
        "inference_cpu_seconds": cpu_after.user + cpu_after.system - cpu_before.user - cpu_before.system,
        "process_cpu_seconds": cpu_after.user + cpu_after.system,
        "runtime_package_directory_bytes": disk_bytes,
        "runtime_package_version": importlib.metadata.version(package),
        "tensorflow_imported": "tensorflow" in sys.modules,
    }
    (args.results / f"benchmark-{args.engine}.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", choices=("tensorflow", "onnx"), required=True)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--results", type=Path, default=Path(__file__).with_name("results"))
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--images-per-class", type=int, choices=(1, 2), default=2)
    args = parser.parse_args()
    worker(args)


if __name__ == "__main__":
    main()
