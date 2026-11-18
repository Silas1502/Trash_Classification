"""Compare independent TensorFlow and ONNX processes on a stratified test set."""

import argparse
from dataclasses import asdict
import json
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def cases(per_class):
    dataset = ROOT / "data/datasets/MyTrashNet_Test_10Percent"
    output = []
    for label in ("glass", "metal", "paper", "plastic"):
        files = sorted(p for p in (dataset / label).rglob("*") if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
        if not files:
            raise ValueError(f"No test images for {label}: {dataset}")
        count = min(per_class, len(files))
        indices = [round(i * (len(files) - 1) / max(1, count - 1)) for i in range(count)]
        output.extend({"path": str(files[i].relative_to(ROOT)), "label": label} for i in indices)
    return output


def safety_filter():
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.safety_gate import SafetyFilter
    return SafetyFilter.load(ROOT / "backend/app/core/safety_thresholds.json")


def worker(args):
    import numpy as np
    from PIL import Image
    from .runtime import overlay_jpeg

    selected = json.loads((args.results / "cases.json").read_text(encoding="utf-8"))
    safety = safety_filter()
    if args.worker == "tensorflow":
        os.environ["KERAS_BACKEND"] = "tensorflow"
        os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
        os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
        import tensorflow as tf
        tf.config.threading.set_intra_op_parallelism_threads(args.threads)
        tf.config.threading.set_inter_op_parallelism_threads(1)
        from app.core.config import Settings
        from app.ml.model_loader import load_model
        from app.ml.preprocessor import ImagePreprocessor
        from app.ml.inference import _probabilities
        from app.ml.xai_engine import normalize_map, render_explanations
        settings = Settings(_env_file=None, model_path=args.checkpoint.resolve())
        model = load_model(settings, safety.thresholds.classes.labels)
        processor = ImagePreprocessor(settings.max_image_pixels, False)
    else:
        from .runtime import Runtime, prepare
        model = Runtime(args.artifacts, threads=args.threads)
    records = []
    for index, case in enumerate(selected):
        path = ROOT / case["path"]
        contents = path.read_bytes()
        with Image.open(path) as image:
            mime = Image.MIME[image.format]
        started = perf_counter()
        if args.worker == "tensorflow":
            prepared = processor.prepare(contents, mime)
            rgb = prepared.model_rgb.numpy()
            probabilities, votes = _probabilities(model, tf.convert_to_tensor(rgb[None]), 5)
            probabilities, stability = probabilities[0], float(votes[0])
            target = int(probabilities.argmax())
            features, skip = model.spatial(rgb[None], training=False)
            with tf.GradientTape(watch_accessed_variables=False) as tape:
                tape.watch(features)
                logits = model.head([features, skip], training=False)
                score = tf.reduce_sum(tf.gather(logits, [target], axis=1, batch_dims=1))
            gradients = tape.gradient(score, features).numpy()
            features = features.numpy()
            # Use the production TF renderer and its own normalization as the reference.
            raw_cam = np.einsum("bhwc,bc->bhw", features, gradients.mean(axis=(1, 2)))[0]
            positive = np.maximum(raw_cam, 0)
            cam = normalize_map(np.abs(raw_cam) if float(positive.max()) < 1e-8 else positive)
            energy = normalize_map(np.sqrt(np.mean(np.square(features), axis=-1))[0])
            result = {"probabilities": probabilities, "gradcam": cam, "spatial_energy": energy,
                      "features": features, "gradients": gradients}
            explanation = render_explanations([rgb], features, gradients)[0]
        else:
            prepared = prepare(contents, mime)
            rgb = prepared.model_rgb
            result = model.predict(rgb)
            probabilities, stability, target = result["probabilities"], result["tta_stability"], result["target"]
        # Include JPEG rendering in timing, as the application does.
        cam_jpeg = explanation.gradcam_jpeg if args.worker == "tensorflow" else overlay_jpeg(rgb, result["gradcam"])
        energy_jpeg = explanation.spatial_energy_jpeg if args.worker == "tensorflow" else overlay_jpeg(rgb, result["spatial_energy"])
        milliseconds = (perf_counter() - started) * 1000
        decisions = [asdict(safety.evaluate(probabilities, stability, adaptive_enabled=enabled)) for enabled in (False, True)]
        record = {"path": case["path"], "label": case["label"], "target": target, "tta_stability": stability,
                  "milliseconds": milliseconds, "decisions": decisions}
        records.append(record)
        arrays = {key: result[key] for key in ("probabilities", "gradcam", "spatial_energy", "features", "gradients")}
        arrays["rgb"] = rgb
        np.savez(args.results / f"{args.worker}-{index:03}.npz", **arrays)
        if index < 4:
            (args.results / f"{args.worker}-{index:03}-gradcam.jpg").write_bytes(cam_jpeg)
            (args.results / f"{args.worker}-{index:03}-energy.jpg").write_bytes(energy_jpeg)
        print(f"{args.worker} {index + 1}/{len(selected)}: {path.name} ({milliseconds:.0f} ms)", flush=True)
    (args.results / f"{args.worker}.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.worker == "onnx":
        if any(name == "tensorflow" or name.startswith("tensorflow.") or name == "torch" for name in sys.modules):
            raise RuntimeError("The ONNX process unexpectedly imported a heavyweight training runtime.")


def compare(results):
    import numpy as np
    reference = json.loads((results / "tensorflow.json").read_text(encoding="utf-8"))
    candidate = json.loads((results / "onnx.json").read_text(encoding="utf-8"))
    rows = []
    mismatches = {"top1": [], "tta_stability": [], "safety_decision": []}
    fields = ("top_index", "decision", "decision_tier", "confidence_gate_passed", "margin_gate_passed", "pipeline_type", "status")
    maximum = {key: 0.0 for key in ("probabilities", "gradcam", "spatial_energy", "rgb", "features", "gradients")}
    for index, (a, b) in enumerate(zip(reference, candidate, strict=True)):
        for key in ("target", "tta_stability"):
            if a[key] != b[key]:
                mismatches["top1" if key == "target" else key].append(a["path"])
        for enabled in (0, 1):
            if any(a["decisions"][enabled][key] != b["decisions"][enabled][key] for key in fields):
                mismatches["safety_decision"].append({"path": a["path"], "adaptive": bool(enabled)})
        row = {"path": a["path"]}
        with np.load(results / f"tensorflow-{index:03}.npz") as source, np.load(results / f"onnx-{index:03}.npz") as target:
            for key in maximum:
                difference = np.abs(source[key] - target[key])
                row[key + "_max_abs"] = float(difference.max())
                row[key + "_mae"] = float(difference.mean())
                maximum[key] = max(maximum[key], row[key + "_max_abs"])
        rows.append(row)
    # Declared acceptance gates; these are numerical equivalence, not a claim
    # that a finite sample proves accuracy on every future image.
    tolerances = {"probabilities": 1e-4, "gradcam": 5e-3, "spatial_energy": 1e-3}
    passed = not any(mismatches.values()) and all(maximum[key] <= limit for key, limit in tolerances.items())
    accuracy = {}
    macro_f1 = {}
    labels = ("glass", "metal", "paper", "plastic")
    for name, records in (("tensorflow", reference), ("onnx", candidate)):
        accuracy[name] = sum(labels[r["target"]] == r["label"] for r in records) / len(records)
        scores = []
        for index, label in enumerate(labels):
            tp = sum(r["label"] == label and r["target"] == index for r in records)
            fp = sum(r["label"] != label and r["target"] == index for r in records)
            fn = sum(r["label"] == label and r["target"] != index for r in records)
            scores.append(2 * tp / max(1, 2 * tp + fp + fn))
        macro_f1[name] = sum(scores) / len(scores)
    report = {
        "passed": passed, "images": len(reference), "tta_views": 5, "precision": "float32",
        "max_absolute_errors": maximum, "tolerances": tolerances, "mismatches": mismatches,
        "subset_top1_accuracy": accuracy, "subset_macro_f1": macro_f1, "per_image": rows,
        "mean_ms": {"tensorflow": float(np.mean([r["milliseconds"] for r in reference])),
                    "onnx": float(np.mean([r["milliseconds"] for r in candidate]))},
        "scope": "Stratified local held-out subset, center crop, 5-view TTA, both adaptive gate settings. Windows CPU, two threads. Not a full-dataset accuracy guarantee.",
    }
    (results / "comparison.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "per_image"}, indent=2))
    if not passed:
        raise SystemExit("Numerical or decision equivalence gates failed. Do not deploy this export.")


def main():
    from .export import DEFAULT_CHECKPOINT, DEFAULT_OUTPUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifacts", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--results", type=Path, default=HERE / "results")
    parser.add_argument("--per-class", type=int, default=16)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--onnx-python", type=Path, help="Optional clean Python environment without TensorFlow.")
    parser.add_argument("--worker", choices=("tensorflow", "onnx"))
    parser.add_argument("--compare-only", action="store_true")
    args = parser.parse_args()
    args.results.mkdir(parents=True, exist_ok=True)
    if args.worker:
        worker(args)
    elif args.compare_only:
        compare(args.results)
    else:
        (args.results / "cases.json").write_text(json.dumps(cases(args.per_class), indent=2), encoding="utf-8")
        for engine in ("tensorflow", "onnx"):
            subprocess.run([
                str(args.onnx_python) if engine == "onnx" and args.onnx_python else sys.executable,
                "-m", "experiments.onnx_fp32.verify", "--worker", engine,
                "--artifacts", str(args.artifacts), "--checkpoint", str(args.checkpoint),
                "--results", str(args.results), "--threads", str(args.threads),
            ], cwd=ROOT, check=True)
        compare(args.results)


if __name__ == "__main__":
    main()
