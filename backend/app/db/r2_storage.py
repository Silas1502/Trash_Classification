import logging
from collections.abc import Sequence
from dataclasses import dataclass
from urllib.parse import quote

from boto3 import session
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import Settings
from app.core.errors import ApiError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ImageObject:
    key: str
    content: bytes
    mime_type: str


class R2Storage:
    def __init__(self, settings: Settings) -> None:
        assert settings.r2_access_key_id and settings.r2_secret_access_key
        self.bucket = settings.r2_bucket_name
        self.public_domain = settings.r2_public_domain
        self.client = session.Session().client(
            "s3", region_name="auto",
            endpoint_url=f"https://{settings.r2_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=settings.r2_access_key_id.get_secret_value(),
            aws_secret_access_key=settings.r2_secret_access_key.get_secret_value(),
            config=Config(
                connect_timeout=3, read_timeout=7, max_pool_connections=settings.storage_concurrency + 1,
                retries={"mode": "standard", "total_max_attempts": 3},
                signature_version="s3v4", s3={"addressing_style": "path"},
                request_checksum_calculation="when_required", response_checksum_validation="when_required",
            ),
        )

    def close(self) -> None:
        self.client.close()

    def check(self) -> None:
        self.client.head_bucket(Bucket=self.bucket)

    def upload_images(self, objects: Sequence[ImageObject]) -> list[str]:
        attempted = []
        try:
            for item in objects:
                attempted.append(item.key)
                self.client.put_object(
                    Bucket=self.bucket, Key=item.key, Body=item.content, ContentType=item.mime_type,
                    CacheControl="public, max-age=86400",
                )
        except (BotoCoreError, ClientError) as exc:
            logger.warning("R2 upload failed: %s", type(exc).__name__)
            for key in attempted:
                try:
                    self.client.delete_object(Bucket=self.bucket, Key=key)
                except (BotoCoreError, ClientError):
                    logger.warning("Could not clean up an incomplete R2 upload: %s", key)
            raise ApiError(503, "storage_unavailable", "Không thể lưu ảnh lên bộ lưu trữ lúc này.") from exc
        return [f"{self.public_domain}/{quote(item.key, safe='/')}" for item in objects]
