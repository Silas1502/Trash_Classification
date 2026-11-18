"""Alternate entrypoint. The production app.main:app still defaults to TensorFlow."""

from app.core.config import Settings
from app.main import create_app

from .adapter import OnnxPreprocessor, classify_batch, load_model


def create_onnx_app(settings=None):
    return create_app(
        settings or Settings(), batch_classifier=classify_batch,
        model_loader=load_model, preprocessor_factory=OnnxPreprocessor,
    )


app = create_onnx_app()
