from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, HttpUrl, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
CHECKPOINT_DIR = BACKEND_DIR / "checkpoints"
DEFAULT_MODEL = CHECKPOINT_DIR / "best_v2_convnext_retrained.keras"
DEFAULT_THRESHOLDS = Path(__file__).with_name("safety_thresholds.json")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=BACKEND_DIR / ".env", extra="ignore")

    model_path: Path | None = None
    model_download_url: HttpUrl | None = None
    model_sha256: str | None = Field(default=None, pattern=r"^[a-fA-F0-9]{64}$")
    safety_thresholds_path: Path = DEFAULT_THRESHOLDS
    adaptive_assessment_enabled: bool = False
    tta_views: Literal["1", "5"] = "5"
    smart_crop: bool = False

    mongodb_uri: SecretStr | None = None
    mongodb_db_name: str = "trash_classification_db"
    supabase_url: str = ""
    supabase_key: SecretStr | None = None

    r2_account_id: str = Field(default="", pattern=r"^(?:[a-fA-F0-9]{32})?$")
    r2_access_key_id: SecretStr | None = None
    r2_secret_access_key: SecretStr | None = None
    r2_bucket_name: str = "trash-classification-images"
    r2_public_domain: str = ""

    imagekit_public_key: SecretStr | None = None
    imagekit_private_key: SecretStr | None = None
    imagekit_url_endpoint: str = ""

    cloudinary_cloud_name: str = ""
    cloudinary_api_key: SecretStr | None = None
    cloudinary_api_secret: SecretStr | None = None

    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    max_upload_bytes: int = Field(default=8 * 1024**2, ge=1024, le=32 * 1024**2)
    max_image_pixels: int = Field(default=16_000_000, ge=320**2, le=32_000_000)
    max_batch_files: int = Field(default=20, ge=1, le=100)
    max_batch_bytes: int = Field(default=32 * 1024**2, ge=1024, le=128 * 1024**2)
    inference_batch_size: int = Field(default=2, ge=1, le=8)
    max_prediction_requests: int = Field(default=2, ge=1, le=16)
    storage_concurrency: int = Field(default=4, ge=1, le=32)
    health_probe_interval_seconds: int = Field(default=30, ge=5, le=300)

    @model_validator(mode="after")
    def validate_settings(self) -> "Settings":
        if self.model_download_url and (
            self.model_download_url.scheme != "https" or not self.model_sha256
        ):
            raise ValueError("MODEL_DOWNLOAD_URL yêu cầu HTTPS và MODEL_SHA256.")
        r2_values = (self.r2_account_id, self.r2_access_key_id, self.r2_secret_access_key, self.r2_public_domain)
        if any(r2_values) and not all(r2_values):
            raise ValueError("Cần cấu hình đủ R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY và R2_PUBLIC_DOMAIN.")
        if self.r2_public_domain:
            parsed = urlsplit(self.r2_public_domain)
            if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.path.rstrip("/") or parsed.query or parsed.fragment:
                raise ValueError("R2_PUBLIC_DOMAIN phải là HTTPS origin của bucket.")
            self.r2_public_domain = self.r2_public_domain.rstrip("/")
        if self.supabase_url:
            self.supabase_url = self.supabase_url.strip().rstrip("/")
            if self.supabase_url.endswith("/rest/v1"):
                self.supabase_url = self.supabase_url[:-len("/rest/v1")].rstrip("/")
        if self.max_batch_bytes < self.max_upload_bytes:
            raise ValueError("MAX_BATCH_BYTES phải lớn hơn hoặc bằng MAX_UPLOAD_BYTES.")
        return self

    @property
    def thresholds_path(self) -> Path:
        return BACKEND_DIR / self.safety_thresholds_path

    @property
    def checkpoint_path(self) -> Path:
        if self.model_path is not None:
            if self.model_path.is_absolute():
                return self.model_path
            # Configured paths are relative to backend/, independent of the working directory.
            return BACKEND_DIR / self.model_path
        if DEFAULT_MODEL.is_file() or self.model_download_url:
            return DEFAULT_MODEL
        local_artifact = REPO_DIR / "checkpoints" / "convnext_tiny" / DEFAULT_MODEL.name
        if local_artifact.is_file():
            return local_artifact
        return DEFAULT_MODEL
