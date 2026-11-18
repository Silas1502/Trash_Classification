"""Export the original FP32 forward pass AND exact classifier gradient.

Run from the repository root: python -m experiments.onnx_fp32.export
Conversions run in separate processes so TensorFlow can release graph memory.
"""

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
from types import MethodType

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CHECKPOINT = ROOT / "checkpoints/convnext_tiny/best_v2_convnext_retrained_inference.keras"
DEFAULT_OUTPUT = Path(__file__).with_name("artifacts")


def custom_handlers():
    """Lower two missing converter ops to ordinary ONNX FP32 arithmetic."""
    import numpy as np
    from tf2onnx import utils

    def replace(ctx, node, emit):
        output, shape, dtype = node.output[0], ctx.get_shape(node.output[0]), ctx.get_dtype(node.output[0])
        inputs = list(node.input)
        ctx.remove_node(node.name)
        value = emit(ctx, inputs)
        ctx.make_node("Identity", [value], outputs=[output], shapes=[shape], dtypes=[dtype])

    def erfc(ctx, node, name, args):
        def emit(ctx, inputs):
            one = ctx.make_const(utils.make_name("erfc_one"), np.array(1, dtype=np.float32)).output[0]
            erf = ctx.make_node("Erf", inputs).output[0]
            return ctx.make_node("Sub", [one, erf]).output[0]
        replace(ctx, node, emit)

    def rsqrt_grad(ctx, node, name, args):
        def emit(ctx, inputs):
            value, upstream = inputs
            half = ctx.make_const(utils.make_name("negative_half"), np.array(-0.5, dtype=np.float32)).output[0]
            square = ctx.make_node("Mul", [value, value]).output[0]
            cube = ctx.make_node("Mul", [square, value]).output[0]
            derivative = ctx.make_node("Mul", [cube, half]).output[0]
            return ctx.make_node("Mul", [upstream, derivative]).output[0]
        replace(ctx, node, emit)

    return {"Erfc": (erfc, []), "RsqrtGrad": (rsqrt_grad, [])}


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def convert_part(checkpoint, output, part):
    os.environ["KERAS_BACKEND"] = "tensorflow"
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
    import tensorflow as tf
    import tf2onnx

    tf.config.threading.set_intra_op_parallelism_threads(2)
    tf.config.threading.set_inter_op_parallelism_threads(1)
    sys.path.insert(0, str(ROOT / "backend"))
    from app.core.config import Settings
    from app.core.safety_gate import SafetyFilter
    from app.ml.model_loader import load_model

    settings = Settings(_env_file=None, model_path=checkpoint)
    safety = SafetyFilter.load(settings.thresholds_path)
    model = load_model(settings, safety.thresholds.classes.labels)

    if part == "forward":
        # Keras routes grouped Conv2D through an XLA StatefulPartitionedCall,
        # which tf2onnx cannot inline on TF 2.20. ConvNeXt's groups==channels,
        # multiplier==1 convolutions are exactly depthwise convolutions.
        # Express that operation directly for export, retaining every weight.
        def depthwise_call(layer, inputs):
            output = tf.nn.depthwise_conv2d(
                inputs, tf.transpose(layer.kernel, (0, 1, 3, 2)),
                strides=(1, *layer.strides, 1), padding=layer.padding.upper(),
                dilations=layer.dilation_rate,
            )
            if layer.use_bias:
                output = tf.nn.bias_add(output, layer.bias)
            return layer.activation(output)

        import keras
        count = 0
        for layer in model.sub_logits_model.layers:
            if isinstance(layer, keras.layers.Normalization):
                mean, variance = layer.mean.numpy(), layer.variance.numpy()
                invert, epsilon = layer.invert, keras.backend.epsilon()

                def normalization_call(layer, inputs, mean=mean, variance=variance, invert=invert, epsilon=epsilon):
                    # Bake eager normalization constants into the graph rather
                    # than accidentally exporting them as extra user inputs.
                    center = tf.constant(mean, dtype=inputs.dtype)
                    scale = tf.maximum(tf.sqrt(tf.constant(variance, dtype=inputs.dtype)), epsilon)
                    return center + inputs * scale if invert else (inputs - center) / scale

                layer.call = MethodType(normalization_call, layer)
            if isinstance(layer, keras.layers.Conv2D) and layer.groups > 1:
                if layer.groups != layer.filters or int(layer.kernel.shape[2]) != 1 or layer.data_format != "channels_last":
                    raise ValueError("Only multiplier-one NHWC depthwise convolutions may be lowered.")
                layer.call = MethodType(depthwise_call, layer)
                count += 1
        if count != 18:
            raise ValueError(f"Expected ConvNeXt-Tiny's 18 depthwise blocks, found {count}.")
        signature = [tf.TensorSpec((1, 320, 320, 3), tf.float32, name="rgb")]

        @tf.function(input_signature=signature, autograph=False)
        def function(rgb):
            # A single shared graph, not three separately loaded backbones.
            return combined(rgb, training=False)

        combined = keras.Model(
            model.sub_logits_model.input,
            [model.sub_logits_model.output, *model.spatial.outputs],
        )
    else:
        feature_shape = tuple(model.head.inputs[0].shape)
        skip_shape = tuple(model.head.inputs[1].shape)
        signature = [
            tf.TensorSpec((1, *feature_shape[1:]), tf.float32, name="features"),
            tf.TensorSpec((1, *skip_shape[1:]), tf.float32, name="skip"),
            tf.TensorSpec((1,), tf.int32, name="targets"),
        ]

        @tf.function(input_signature=signature, autograph=False)
        def function(features, skip, targets):
            with tf.GradientTape(watch_accessed_variables=False) as tape:
                tape.watch(features)
                logits = model.head([features, skip], training=False)
                scores = tf.gather(logits, targets, axis=1, batch_dims=1)
                total = tf.reduce_sum(scores)
            gradients = tape.gradient(total, features)
            if gradients is None:
                raise RuntimeError("The exported classifier lost its spatial gradient.")
            return logits, gradients

    destination = output / f"{part}.onnx"
    tf2onnx.convert.from_function(
        function, input_signature=signature, opset=18, output_path=str(destination),
        custom_op_handlers=custom_handlers(),
    )
    import onnx
    graph = onnx.load(destination)
    onnx.checker.check_model(graph)
    expected_inputs = {"rgb"} if part == "forward" else {"features", "skip", "targets"}
    if {value.name for value in graph.graph.input} != expected_inputs:
        raise ValueError("Export contains unexpected captures instead of constant weights.")
    print(f"Exported {part}: {destination.stat().st_size:,} bytes", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--part", choices=("all", "forward", "gradient", "manifest"), default="all")
    args = parser.parse_args()
    checkpoint, output = args.checkpoint.resolve(), args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if args.part in ("forward", "gradient"):
        convert_part(checkpoint, output, args.part)
        return
    if args.part == "all":
        for part in ("gradient", "forward"):
            subprocess.run([
                sys.executable, "-m", "experiments.onnx_fp32.export", "--part", part,
                "--checkpoint", str(checkpoint), "--output", str(output),
            ], cwd=ROOT, check=True)
    thresholds = ROOT / "backend/app/core/safety_thresholds.json"
    manifest = {
        "format_version": 1, "precision": "float32", "opset": 18,
        "input_shape": [1, 320, 320, 3], "tta_views": 5,
        "labels": json.loads(thresholds.read_text(encoding="utf-8-sig"))["classes"]["labels"],
        "checkpoint_sha256": sha256(checkpoint), "checkpoint_bytes": checkpoint.stat().st_size,
        "thresholds_sha256": sha256(thresholds),
        "spatial_layer": "convnext_tiny_stage_3_block_2_identity",
        "converter_lowerings": {"Erfc(x)": "1 - Erf(x)", "RsqrtGrad(y, dy)": "-0.5 * dy * y**3",
                                "grouped Conv2D, groups=channels": "multiplier-one depthwise_conv2d, identical kernel"},
        "files": {
            name: {"sha256": sha256(output / name), "bytes": (output / name).stat().st_size}
            for name in ("forward.onnx", "gradient.onnx")
        },
        "export_versions": {
            name: importlib.metadata.version(name)
            for name in ("tensorflow", "keras", "tf2onnx", "onnx", "numpy")
        },
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Both FP32 graphs exported. No quantization, retraining or threshold changes.")


if __name__ == "__main__":
    main()
