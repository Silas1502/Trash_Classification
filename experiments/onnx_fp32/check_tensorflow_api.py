"""Regression check for the default API after making shared imports lazy."""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from fastapi.testclient import TestClient
from app.core.config import Settings
from app.main import create_app
from app.ml.types import DummyPredictor


def main():
    labels = ("glass", "metal", "paper", "plastic")
    settings = Settings(_env_file=None, supabase_url="", supabase_key=None,
                        imagekit_private_key=None, imagekit_url_endpoint="")
    app = create_app(settings, model=DummyPredictor(labels))
    with TestClient(app) as client:
        assert client.get("/api/v1/health").status_code == 200
        info = client.get("/api/v1/model-info").json()
        assert info["is_mock"] is True
        path = next((ROOT / "data/datasets/MyTrashNet_Test_10Percent/glass").glob("*.jpg"))
        response = client.post("/api/v1/predict/single", files={"file": ("a.jpg", path.read_bytes(), "image/jpeg")})
        assert response.status_code == 200, response.text
        assert response.json()["is_mock"] is True
        assert "tensorflow" in sys.modules
    print("Default TensorFlow API regression passed; no cloud writes.")


if __name__ == "__main__":
    main()
