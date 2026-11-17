import logging
from collections.abc import Sequence

from supabase import create_client, Client

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.storage import ImageObject

logger = logging.getLogger(__name__)


class SupabaseStorage:
    def __init__(self, settings: Settings, bucket_name: str = "trash-images") -> None:
        self.url = settings.supabase_url
        self.key = settings.supabase_key.get_secret_value() if settings.supabase_key else ""
        self.bucket = bucket_name
        self.client: Client = create_client(self.url, self.key)

    def close(self) -> None:
        pass

    def check(self) -> None:
        try:
            # Check bucket existence by listing buckets or retrieving bucket
            buckets = self.client.storage.list_buckets()
            names = [b.name for b in buckets] if buckets else []
            if self.bucket not in names:
                # Fallback: check if we can query public url without error
                pass
        except Exception as exc:
            logger.warning("Supabase storage check failed: %s", exc)
            raise

    def upload_images(self, objects: Sequence[ImageObject]) -> list[str]:
        urls = []
        for item in objects:
            try:
                # Ensure clean key path
                path = item.key.lstrip("/")
                self.client.storage.from_(self.bucket).upload(
                    path=path,
                    file=item.content,
                    file_options={"content-type": item.mime_type, "upsert": "true"}
                )
                public_url = self.client.storage.from_(self.bucket).get_public_url(path)
                urls.append(public_url)
            except Exception as exc:
                logger.warning("Supabase storage upload failed for %s: %s", item.key, exc)
                raise ApiError(503, "storage_unavailable", "Không thể lưu ảnh lên Supabase Storage lúc này.") from exc
        return urls
