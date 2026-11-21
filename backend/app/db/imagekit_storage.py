import concurrent.futures
import logging
import re
from collections.abc import Sequence
from urllib.parse import unquote, urlsplit
from uuid import UUID

from imagekitio import ImageKit, NotFoundError

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.storage import MANUAL_PREDICTION_FOLDER, PREDICTION_FOLDERS_BY_LABEL, ImageObject, prediction_tag

logger = logging.getLogger(__name__)
PREDICTION_FOLDERS_PATTERN = "|".join(
    map(re.escape, (*PREDICTION_FOLDERS_BY_LABEL.values(), MANUAL_PREDICTION_FOLDER))
)
UPLOAD_DATE = r"\d{4}/\d{2}/\d{2}"
XAI_FILENAME = r"(?:gradcam|spatial_energy)_overlay\.jpg"
NUMBERED_PATH = re.compile(
    rf"/uploads/(?:(?P<folder>{PREDICTION_FOLDERS_PATTERN})/(?P=folder)_[0-9]{{3,}}\.(?:jpg|png|webp)"
    rf"|xai/(?:{PREDICTION_FOLDERS_PATTERN})_[0-9]{{3,}}_{XAI_FILENAME})"
)


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

    def delete_prediction_images(self, prediction_id: str, urls: Sequence[str]) -> None:
        """Resolve stored ImageKit URLs to exact fileIds; retries are idempotent."""
        record_id = str(UUID(prediction_id))
        endpoint = urlsplit(self.url_endpoint)
        prefix = endpoint.path.rstrip("/") + "/"
        file_prefix = rf"{re.escape(record_id)}_"
        dated_prefix = rf"{UPLOAD_DATE}/{file_prefix}"
        pattern = re.compile(
            rf"/uploads/(?:(?:single|batch)/{dated_prefix}[^/]+"
            rf"|xai/(?:{UPLOAD_DATE}/)?{file_prefix}{XAI_FILENAME}"
            rf"|(?:{PREDICTION_FOLDERS_PATTERN})/(?:{UPLOAD_DATE}/)?{file_prefix}original_[^/]+"
            rf"|(?:{PREDICTION_FOLDERS_PATTERN})/{dated_prefix}{XAI_FILENAME})"
        )
        paths: dict[str, bool] = {}
        for url in urls:
            parsed = urlsplit(url)
            if (parsed.scheme, parsed.netloc) != (endpoint.scheme, endpoint.netloc) or not parsed.path.startswith(prefix):
                raise ValueError("Cleanup URL does not belong to configured ImageKit endpoint")
            path = "/" + unquote(parsed.path[len(prefix):])
            numbered = NUMBERED_PATH.fullmatch(path) is not None
            if "\\" in path or not (numbered or pattern.fullmatch(path)):
                raise ValueError("Cleanup path does not belong to deleted prediction")
            paths[path] = numbered

        client = self.client.with_options(timeout=10, max_retries=0)
        file_ids = []
        # Numbered names no longer contain the UUID. Verify ownership before deleting any files.
        expected_tag = prediction_tag(record_id)
        for path, numbered in sorted(paths.items()):
            folder, name = path.rsplit("/", 1)
            skip = 0
            while True:
                assets = client.assets.list(
                    path=folder + "/", type="file", limit=100, skip=skip,
                    extra_query={"name": name},
                )
                match = next((asset for asset in assets if getattr(asset, "file_path", None) == path), None)
                if match is not None:
                    if numbered and expected_tag not in (match.tags or ()):
                        raise ValueError("ImageKit file does not belong to deleted prediction")
                    file_ids.append(match.file_id)
                    break
                if len(assets) < 100:
                    break  # Missing files are already clean.
                skip += len(assets)
        for file_id in file_ids:
            try:
                client.files.delete(file_id)
            except NotFoundError:
                pass  # Another attempt already removed this exact file.

    def upload_images(self, objects: Sequence[ImageObject]) -> list[str]:
        if not objects:
            return []

        def _upload_one(item: ImageObject) -> str:
            parts = item.key.rsplit("/", 1)
            folder = "/" + parts[0] if len(parts) > 1 else "/trash_classification"
            file_name = parts[1] if len(parts) > 1 else item.key
            upload_options = {"tags": [item.ownership_tag]} if item.ownership_tag else {}
            resp = self.client.files.upload(
                file=item.content,
                file_name=file_name,
                folder=folder,
                use_unique_file_name=False,
                overwrite_file=item.ownership_tag is None,
                **upload_options,
            )
            return resp.url

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(objects), 4)) as executor:
            try:
                # executor.map preserves the original order of objects
                return list(executor.map(_upload_one, objects))
            except Exception as exc:
                logger.warning("ImageKit upload failed: %s", exc)
                raise ApiError(503, "storage_unavailable", "Không thể lưu ảnh lên ImageKit lúc này.") from exc
