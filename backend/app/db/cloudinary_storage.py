import logging
from collections.abc import Sequence
from dataclasses import dataclass

import cloudinary
import cloudinary.uploader
import cloudinary.api

from app.core.config import Settings
from app.core.errors import ApiError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImageObject:
    key: str
    content: bytes
    mime_type: str


class CloudinaryStorage:
    def __init__(self, settings: Settings) -> None:
        self.cloud_name = settings.cloudinary_cloud_name
        self.api_key = settings.cloudinary_api_key.get_secret_value() if settings.cloudinary_api_key else ""
        self.api_secret = settings.cloudinary_api_secret.get_secret_value() if settings.cloudinary_api_secret else ""
        cloudinary.config(
            cloud_name=self.cloud_name,
            api_key=self.api_key,
            api_secret=self.api_secret,
            secure=True,
        )

    def close(self) -> None:
        pass

    def check(self) -> None:
        try:
            res = cloudinary.api.ping()
            if res.get("status") != "ok":
                raise RuntimeError(f"Cloudinary ping failed: {res}")
        except Exception as exc:
            logger.warning("Cloudinary ping check failed: %s", exc)
            raise

    def upload_images(self, objects: Sequence[ImageObject]) -> list[str]:
        urls = []
        for item in objects:
            try:
                public_id = item.key.rsplit(".", 1)[0]
                resp = cloudinary.uploader.upload(
                    item.content,
                    public_id=public_id,
                    overwrite=True,
                    resource_type="image",
                )
                urls.append(resp["secure_url"])
            except Exception as exc:
                logger.warning("Cloudinary upload failed for %s: %s", item.key, exc)
                raise ApiError(503, "storage_unavailable", "Không thể lưu ảnh lên Cloudinary lúc này.") from exc
        return urls
