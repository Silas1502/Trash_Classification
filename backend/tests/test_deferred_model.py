from types import SimpleNamespace
import unittest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.ml.preprocessor import InvalidImage, PreparedImage
from app.ml.types import Explainability, InferenceResult


class DeferredModelTests(unittest.TestCase):
    def test_loads_after_valid_image_only_and_retries_once(self):
        steps = []
        model = SimpleNamespace(checkpoint="verified.onnx")

        def load_model(settings, labels):
            steps.append("load")
            if steps.count("load") == 1:
                raise RuntimeError("temporary load failure")
            return model

        def prepare(contents, mime):
            if contents != b"valid":
                raise InvalidImage("Malformed test image")
            steps.append("prepare")
            return PreparedImage(contents, (0, 0, 1), "image_center", mime, ".jpg")

        def classify(loaded_model, images, settings, safety):
            self.assertIs(loaded_model, model)
            steps.append("classify")
            decision = safety.evaluate([0.97, 0.01, 0.01, 0.01], None)
            return [InferenceResult(decision, Explainability(b"gradcam", b"energy"), 1, 1)]

        app = create_app(
            Settings(_env_file=None), model_loader=load_model, batch_classifier=classify,
            preprocessor_factory=lambda *_: SimpleNamespace(prepare=prepare), defer_model_load=True,
        )
        with TestClient(app) as client:
            app.state.history = SimpleNamespace(insert=AsyncMock(), check=AsyncMock())
            app.state.storage = SimpleNamespace(
                check=lambda: None, upload_images=lambda images: [f"https://example.invalid/{i}" for i in range(3)],
            )
            health = client.get("/api/v1/health")
            self.assertEqual(health.status_code, 200)
            self.assertEqual(health.json()["model"], "pending")
            endpoint = "/api/v1/predict/single"
            invalid = {"file": ("image.jpg", b"invalid", "image/jpeg")}
            valid = {"file": ("image.jpg", b"valid", "image/jpeg")}
            self.assertEqual(client.post(endpoint, files=invalid).status_code, 400)
            self.assertEqual(steps, [])
            self.assertEqual(client.post(endpoint, files=valid).status_code, 503)
            health = client.get("/api/v1/health")
            self.assertEqual(health.status_code, 503)
            self.assertEqual(health.json()["model"], "error")
            self.assertEqual(client.post(endpoint, files=valid).status_code, 200)
            self.assertEqual(client.get("/api/v1/health").json()["model"], "loaded")
            self.assertEqual(client.post(endpoint, files=valid).status_code, 200)
            self.assertEqual(steps, ["prepare", "load", "prepare", "load", "classify", "prepare", "classify"])
