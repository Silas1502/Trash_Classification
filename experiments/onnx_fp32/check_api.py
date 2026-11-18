"""Exercise real API routes using in-memory storage; no external requests."""

import faulthandler
import json
from io import BytesIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from PIL import Image
from app.core.config import Settings
from app.schemas.prediction import PredictionResult
from .app import create_onnx_app


class History:
    def __init__(self):
        self.rows = []

    async def check(self):
        pass

    async def insert(self, item):
        self.rows.append(item)


class Storage:
    def __init__(self):
        self.objects = []

    def check(self):
        pass

    def upload_images(self, objects):
        self.objects.extend(objects)
        return ["https://example.invalid/" + obj.key for obj in objects]


def main():
    faulthandler.dump_traceback_later(45, repeat=False)
    # Explicitly disable reading the real cloud credentials for this check.
    settings = Settings(_env_file=None, supabase_url="", supabase_key=None,
                        imagekit_private_key=None, imagekit_url_endpoint="", inference_batch_size=2)
    app = create_onnx_app(settings)
    path = ROOT / "data/datasets/MyTrashNet_Test_10Percent/glass"
    sample = next(path.glob("*.jpg")).read_bytes()
    print("API check: starting ONNX lifespan", flush=True)
    with TestClient(app) as client:
        print("API check: health and model-info", flush=True)
        assert client.get("/api/v1/health").status_code == 200
        assert client.head("/api/v1/health").status_code == 200
        info = client.get("/api/v1/model-info").json()
        assert info["is_mock"] is False and info["tta_views"] == 5
        assert client.post("/api/v1/predict/single", files={"file": ("a.jpg", sample, "image/jpeg")}).status_code == 503
        history, storage = History(), Storage()
        app.state.history, app.state.storage = history, storage
        print("API check: single prediction", flush=True)
        response = client.post("/api/v1/predict/single", files={"file": ("a.jpg", sample, "image/jpeg")})
        assert response.status_code == 200, response.text
        result = PredictionResult.model_validate(response.json())
        assert result.is_mock is False and result.xai_overlay_url and result.xai_energy_overlay_url
        assert len(history.rows) == 1 and len(storage.objects) == 3
        assert storage.objects[1].content[:2] == b"\xff\xd8"
        print("API check: mixed valid/invalid batch", flush=True)
        batch = client.post("/api/v1/predict/batch", files=[
            ("files", ("a.jpg", sample, "image/jpeg")),
            ("files", ("b.jpg", sample, "image/jpeg")),
            ("files", ("invalid.jpg", b"not an image", "image/jpeg")),
        ])
        assert batch.status_code == 200, batch.text
        payload = batch.json()
        assert len(payload["results"]) == 2 and len(payload["errors"]) == 1, payload
        assert client.post("/api/v1/predict/single", files={"file": ("a.txt", b"x", "text/plain")}).status_code == 415
        print("API check: maximum allowed 16-megapixel image", flush=True)
        source = BytesIO()
        with Image.new("RGB", (4000, 4000), (90, 140, 200)) as image:
            image.save(source, format="JPEG")
        large = client.post("/api/v1/predict/single", files={"file": ("large.jpg", source.getvalue(), "image/jpeg")})
        assert large.status_code == 200, large.text
        print("API check: maximum allowed RGBA PNG", flush=True)
        source = BytesIO()
        with Image.new("RGBA", (4000, 4000), (90, 140, 200, 100)) as image:
            image.save(source, format="PNG")
        large = client.post("/api/v1/predict/single", files={"file": ("large.png", source.getvalue(), "image/png")})
        assert large.status_code == 200, large.text
        assert "tensorflow" not in sys.modules and "keras" not in sys.modules and "torch" not in sys.modules
        import psutil
        memory = psutil.Process().memory_info()
        print(json.dumps({"passed": True, "routes": ["health GET/HEAD", "model-info", "predict/single", "predict/batch"],
                          "real_cloud_writes": 0, "tensorflow_imported": False, "history_rows": len(history.rows),
                          "largest_image_pixels": 16_000_000,
                          "rss_bytes": memory.rss, "peak_working_set_bytes": getattr(memory, "peak_wset", None)}, indent=2), flush=True)
    faulthandler.cancel_dump_traceback_later()


if __name__ == "__main__":
    main()
