import concurrent.futures
import logging
from collections.abc import Sequence

from imagekitio import ImageKit

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.storage import ImageObject

logger = logging.getLogger(__name__)


class ImageKitStorage:
    def __init__(self, settings: Settings) -> None:
        self.private_key = settings.imagekit_private_key.get_secret_value() if settings.imagekit_private_key else ""
        self.public_key = settings.imagekit_public_key.get_secret_value() if settings.imagekit_public_key else ""
        self.url_endpoint = settings.imagekit_url_endpoint.rstrip("/")
        self.client = ImageKit(private_key=self.private_key)

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass

    def check(self) -> None:
        try:
            self.client.assets.list(limit=1)
        except Exception as exc:
            logger.warning("ImageKit health check failed: %s", exc)
            raise

    def upload_images(self, objects: Sequence[ImageObject]) -> list[str]:
        if not objects:
            return []

        def _upload_one(item: ImageObject) -> str:
            parts = item.key.rsplit("/", 1)
            folder = "/" + parts[0] if len(parts) > 1 else "/trash_classification"
            file_name = parts[1] if len(parts) > 1 else item.key
            resp = self.client.files.upload(
                file=item.content,
                file_name=file_name,
                folder=folder,
                use_unique_file_name=False,
                overwrite_file=True,
            )
            return resp.url

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(objects), 4)) as executor:
            try:
                # executor.map preserves the original order of objects
                return list(executor.map(_upload_one, objects))
            except Exception as exc:
                logger.warning("ImageKit upload failed: %s", exc)
                raise ApiError(503, "storage_unavailable", "Không thể lưu ảnh lên ImageKit lúc này.") from exc
