import asyncio
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.endpoints.predict import router
from app.core.safety_gate import SafetyFilter
from app.ml.preprocessor import PreparedImage
from app.ml.types import Explainability, InferenceResult


class PredictionStorageTests(unittest.TestCase):
    def test_single_and_batch_store_originals_by_group_and_xai_separately(self):
        safety = SafetyFilter.load(Path(__file__).resolve().parents[1] / "app/core/safety_thresholds.json")
        cases = {
            b"glass": ([0.97, 0.01, 0.01, 0.01], "Thủy tinh", "glass"),
            b"metal": ([0.01, 0.97, 0.01, 0.01], "Kim loại", "metal"),
            b"paper": ([0.01, 0.01, 0.97, 0.01], "Giấy", "paper"),
            b"plastic": ([0.01, 0.01, 0.01, 0.97], "Nhựa", "plastic"),
            b"review": ([0.10, 0.10, 0.15, 0.65], "Nhựa", "manual"),
        }
        base = "https://ik.imagekit.io/test/"
        uploaded = {}
        xai = Explainability(b"gradcam", b"energy")

        def classify(model, images, settings, safety_filter):
            return [
                InferenceResult(safety_filter.evaluate(cases[image.model_rgb][0], None), xai, 1, 1)
                for image in images
            ]

        def prepare(contents, mime):
            return PreparedImage(contents, (0, 0, 1), "image_center", mime, ".jpg")

        def upload_images(images):
            uploaded.update({image.key: image.content for image in images})
            return [base + image.key for image in images]

        app = FastAPI()
        app.include_router(router)
        app.state.settings = SimpleNamespace(
            max_upload_bytes=100, max_batch_files=4, max_batch_bytes=400, inference_batch_size=1, tta_views=5,
        )
        app.state.model = SimpleNamespace(checkpoint="model.onnx")
        app.state.safety = safety
        app.state.preprocessor = SimpleNamespace(prepare=prepare)
        app.state.batch_classifier = classify
        app.state.ml_slot = asyncio.Lock()
        app.state.storage_slots = asyncio.Semaphore(1)
        app.state.storage = SimpleNamespace(upload_images=upload_images)
        app.state.history = SimpleNamespace(insert=AsyncMock())

        def check_result(result, contents):
            _, label, category = cases[contents]
            self.assertEqual(result["waste_type"], label)
            self.assertEqual(result["pipeline_type"], "Thủ công" if category == "manual" else "Tự động")
            for field, folder, suffix, data in (
                ("image_url", category, "original_gradcam_overlay.jpg", contents),
                ("xai_overlay_url", "xai", "gradcam_overlay.jpg", b"gradcam"),
                ("xai_energy_overlay_url", "xai", "spatial_energy_overlay.jpg", b"energy"),
            ):
                key = f"uploads/{folder}/{result['id']}_{suffix}"
                self.assertEqual(result[field], base + key)
                self.assertEqual(uploaded[key], data)

        with TestClient(app) as client:
            for contents in cases:
                with self.subTest(single=contents):
                    response = client.post(
                        "/predict/single", files={"file": ("gradcam_overlay.jpg", contents, "image/jpeg")},
                    )
                    self.assertEqual(response.status_code, 200, response.text)
                    check_result(response.json(), contents)

            batch = (b"plastic", b"review", b"glass")
            files = [("files", ("gradcam_overlay.jpg", contents, "image/jpeg")) for contents in batch]
            response = client.post("/predict/batch", files=files)
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["errors"], [])
            for result, contents in zip(response.json()["results"], batch, strict=True):
                check_result(result, contents)

        self.assertEqual(app.state.history.insert.await_count, len(cases) + len(batch))
        for call in app.state.history.insert.await_args_list:
            entry = call.args[0]
            self.assertIn(entry.image_url.removeprefix(base), uploaded)
            self.assertIn(entry.xai_overlay_url.removeprefix(base), uploaded)
            self.assertIn(entry.xai_energy_overlay_url.removeprefix(base), uploaded)
