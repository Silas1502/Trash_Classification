from __future__ import annotations

import os
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Callable, Literal, TYPE_CHECKING

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from .types import IMAGE_SIZE

if TYPE_CHECKING:
    import tensorflow as tf

IMAGE_TYPES = {"JPEG": ("image/jpeg", ".jpg"), "PNG": ("image/png", ".png"), "WEBP": ("image/webp", ".webp")}


class InvalidImage(ValueError):
    pass


@dataclass(frozen=True)
class PreparedImage:
    model_rgb: tf.Tensor
    crop_box: tuple[int, int, int]
    crop_strategy: Literal["subject_center", "image_center"]
    mime_type: str
    extension: str


def _decode(contents: bytes, claimed_type: str, max_pixels: int) -> tuple[np.ndarray, str, str]:
    try:
        with Image.open(BytesIO(contents), formats=list(IMAGE_TYPES)) as image:
            expected, ext = IMAGE_TYPES[image.format]
            if expected != claimed_type:
                raise InvalidImage("Nội dung ảnh không khớp với định dạng khai báo.")
            if image.width * image.height > max_pixels:
                raise InvalidImage(f"Ảnh vượt giới hạn {max_pixels:,} pixel.")
            if getattr(image, "is_animated", False):
                raise InvalidImage("Không hỗ trợ ảnh động.")
            image.verify()
        with Image.open(BytesIO(contents), formats=list(IMAGE_TYPES)) as image:
            rgb = np.asarray(ImageOps.exif_transpose(image).convert("RGB"))
        return rgb, expected, ext
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, SyntaxError, ValueError) as exc:
        if isinstance(exc, InvalidImage):
            raise
        raise InvalidImage("Không đọc được ảnh JPEG, PNG hoặc WebP hợp lệ.") from exc


def area_resize(image: tf.Tensor) -> tf.Tensor:
    import tensorflow as tf

    return tf.image.resize(image, IMAGE_SIZE, method=tf.image.ResizeMethod.AREA, antialias=True)


class ImagePreprocessor:
    def __init__(self, max_pixels: int, smart_crop: bool) -> None:
        self.max_pixels = max_pixels
        self._predict_mask: Callable[[np.ndarray], np.ndarray] | None = None
        if smart_crop:
            asset = Path(os.environ.get("U2NET_HOME") or Path.home() / ".u2net") / "u2netp.onnx"
            if not asset.is_file():
                raise FileNotFoundError(f"SMART_CROP requires a local u2netp.onnx at {asset}.")
            from rembg import new_session, remove
            session = new_session("u2netp", providers=["CPUExecutionProvider"])
            self._predict_mask = lambda rgb: np.asarray(remove(rgb, session=session, only_mask=True))

    def _square(self, rgb: np.ndarray) -> tuple[int, int, int, bool]:
        height, width = rgb.shape[:2]
        if self._predict_mask is not None and height != width:
            preview, scale = self._subject_preview(rgb)
            return self._subject_square(height, width, preview, scale)
        side = min(height, width)
        return (width - side) // 2, (height - side) // 2, side, False

    @staticmethod
    def _subject_preview(rgb: np.ndarray) -> tuple[np.ndarray, float]:
        height, width = rgb.shape[:2]
        scale = min(1.0, 320.0 / max(height, width))
        if scale == 1.0:
            return rgb, scale
        if min(height, width) * scale <= 0.5:
            # OpenCV cannot round an extremely narrow image down to zero pixels.
            size = (max(1, round(width * scale)), max(1, round(height * scale)))
            return cv2.resize(rgb, size), scale
        return cv2.resize(rgb, (0, 0), fx=scale, fy=scale), scale

    def _subject_square(
        self, height: int, width: int, preview: np.ndarray, scale: float,
    ) -> tuple[int, int, int, bool]:
        side = min(height, width)
        predict_mask = self._predict_mask
        assert predict_mask is not None
        mask = predict_mask(preview)
        _, binary = cv2.threshold(mask, 10, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contour = max(contours, key=cv2.contourArea, default=None)
        if contour is not None and cv2.contourArea(contour) > 20:
            x, y, w, h = cv2.boundingRect(contour)
            cx = int((x + w // 2) / scale)
            cy = int((y + h // 2) / scale)
            left = max(0, min(cx - side // 2, width - side))
            top = max(0, min(cy - side // 2, height - side))
            return left, top, side, True
        return (width - side) // 2, (height - side) // 2, side, False

    def prepare(self, contents: bytes, claimed_type: str) -> PreparedImage:
        import tensorflow as tf

        rgb, mime_type, extension = _decode(contents, claimed_type, self.max_pixels)
        x, y, side, found = self._square(rgb)
        model_rgb = area_resize(tf.convert_to_tensor(rgb[y:y + side, x:x + side]))
        return PreparedImage(
            model_rgb, (x, y, side),
            "subject_center" if found else "image_center", mime_type, extension,
        )


def normalize_for_convnext(image: tf.Tensor) -> tf.Tensor:
    import tensorflow as tf
    from tensorflow.keras.applications.convnext import preprocess_input as preprocess_convnext

    # Keras ConvNeXt preprocess_input keeps [0, 255]; the checkpoint normalizes in its stem.
    return preprocess_convnext(tf.cast(image, tf.float32))
