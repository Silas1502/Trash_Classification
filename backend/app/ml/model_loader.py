import hashlib
import json
import logging
import os
import tempfile
from pathlib import Path
from urllib.request import urlopen
from zipfile import ZipFile

import keras
import numpy as np

from app.core.config import Settings

from .custom_layers import CosineDense, L2Normalize
from .types import DummyPredictor, IMAGE_SIZE, ModelBundle, SPATIAL_LAYER

logger = logging.getLogger(__name__)

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024**2), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prepare_checkpoint(settings: Settings) -> Path | None:
    path = settings.checkpoint_path
    expected = settings.model_sha256.lower() if settings.model_sha256 else None
    if path.suffix != ".keras":
        raise ValueError("MODEL_PATH must point to a .keras file.")
    if not path.is_file():
        if not settings.model_download_url:
            logger.warning("Checkpoint absent at %s. Running the mock predictor with production readiness disabled.", path)
            return None
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=path.parent, suffix=".part", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            with urlopen(str(settings.model_download_url), timeout=30) as response, tmp_path.open("wb") as target:
                if not response.geturl().startswith("https://"):
                    raise ValueError("Checkpoint download must stay on HTTPS.")
                downloaded = 0
                for chunk in iter(lambda: response.read(1024**2), b""):
                    downloaded += len(chunk)
                    if downloaded > 512 * 1024**2:
                        raise ValueError("Checkpoint exceeds maximum download size.")
                    target.write(chunk)
            if _sha256(tmp_path) != expected:
                raise ValueError("Downloaded checkpoint does not match MODEL_SHA256.")
            os.replace(tmp_path, path)
        finally:
            tmp_path.unlink(missing_ok=True)
    elif expected and _sha256(path) != expected:
        raise ValueError("Local checkpoint does not match MODEL_SHA256.")
    return path


def _clean_keras_config(obj: object) -> None:
    if isinstance(obj, dict):
        obj.pop("quantization_config", None)
        for value in obj.values():
            _clean_keras_config(value)
    elif isinstance(obj, list):
        for item in obj:
            _clean_keras_config(item)


def _deserialize_checkpoint(path: Path) -> keras.Model:
    with ZipFile(path) as archive:
        config = json.loads(archive.read("config.json"))
    _clean_keras_config(config)
    custom_objects = {"CosineDense": CosineDense}
    lambda_layers = [layer for layer in config["config"]["layers"] if layer["class_name"] == "Lambda"]
    if not lambda_layers:
        return keras.models.load_model(path, custom_objects=custom_objects, compile=False, safe_mode=True)

    config["compile_config"] = None
    for layer in lambda_layers:
        original = layer["config"]
        if original["name"] != "norm_features" or original.get("output_shape") != [1024]:
            raise ValueError("Unsupported Lambda in checkpoint.")
        # Rebuild the notebook's known stateless operation without executing serialized Python.
        layer.update(module=L2Normalize.__module__, class_name="L2Normalize", registered_name="TrashClassification>L2Normalize")
        layer["config"] = {key: original[key] for key in ("name", "trainable", "dtype")}
    model = keras.saving.deserialize_keras_object(
        config, custom_objects=custom_objects, safe_mode=True,
    )
    model.load_weights(path)
    return model


def load_model(settings: Settings, class_labels: tuple[str, ...]) -> ModelBundle | DummyPredictor:
    path = _prepare_checkpoint(settings)
    if path is None:
        return DummyPredictor(class_labels)
    model = _deserialize_checkpoint(path)
    logits = model.get_layer("cosine_logits")
    features = model.get_layer(SPATIAL_LAYER).output
    if tuple(model.inputs[0].shape[1:]) != (*IMAGE_SIZE, 3) or logits.units != len(class_labels):
        raise ValueError("Checkpoint input shape or output width disagrees with the safety configuration.")
    if path.name == "best_v2_convnext_retrained.keras":
        if class_labels != ("glass", "metal", "paper", "plastic"):
            raise ValueError("Label order for the supplied v2 checkpoint is glass, metal, paper, plastic.")
    # The requested identity tensor is one branch of the final residual Add.
    # Carry its skip tensor into the head so differentiating the logits is exact.
    residual_inputs = None
    for operation in model.operations:
        # ConvNeXt serializes this as keras.ops.Add, outside model.layers.
        if type(operation).__name__ == "Add":
            inputs = keras.tree.flatten(operation.input)
            if len(inputs) == 2 and any(tensor is features for tensor in inputs):
                residual_inputs = inputs
                break
    if residual_inputs is None:
        raise ValueError(f"Could not resolve the skip connection for {SPATIAL_LAYER}.")
    skip = next(tensor for tensor in residual_inputs if tensor is not features)
    bundle = ModelBundle(
        keras.Model(model.inputs[0], logits.output),
        keras.Model(model.inputs[0], [features, skip]),
        keras.Model([features, skip], logits.output),
        path.name,
        class_labels,
    )
    sample = keras.ops.zeros((1, *IMAGE_SIZE, 3), dtype="float32")
    warmup_logits = keras.ops.convert_to_numpy(bundle.sub_logits_model(sample, training=False))
    if not np.isfinite(warmup_logits).all():
        raise ValueError("Checkpoint produced non-finite logits during warmup.")
    head_logits = keras.ops.convert_to_numpy(bundle.head(bundle.spatial(sample, training=False), training=False))
    np.testing.assert_allclose(head_logits, warmup_logits, rtol=1e-6, atol=1e-6)
    logger.info("Loaded checkpoint %s with labels %s", bundle.checkpoint, bundle.class_labels)
    return bundle
