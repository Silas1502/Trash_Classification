import os
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
import tensorflow as tf
from PIL import Image, ImageOps, UnidentifiedImageError
from tensorflow.keras.applications.convnext import preprocess_input as preprocess_convnext

from .model_loader import IMAGE_SIZE

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
    return tf.image.resize(image, IMAGE_SIZE, method=tf.image.ResizeMethod.AREA, antialias=True)


class ImagePreprocessor:
    def __init__(self, max_pixels: int, smart_crop: bool) -> None:
        self.max_pixels = max_pixels
        self.session = None
        if smart_crop:
            asset = Path(os.environ.get("U2NET_HOME") or Path.home() / ".u2net") / "u2netp.onnx"
            if not asset.is_file():
                raise FileNotFoundError(f"SMART_CROP requires a local u2netp.onnx at {asset}.")
            from rembg import new_session, remove
            self.session = new_session("u2netp", providers=["CPUExecutionProvider"])
            self.remove = remove

    def _square(self, rgb: np.ndarray) -> tuple[int, int, int, bool]:
        height, width = rgb.shape[:2]
        side = min(height, width)
        if self.session is not None and height != width:
            scale = min(1.0, 320.0 / max(height, width))
            small = cv2.resize(
                rgb, (max(1, round(width * scale)), max(1, round(height * scale))),
                interpolation=cv2.INTER_AREA,
            )
            mask = self.remove(small, session=self.session, only_mask=True)
            _, binary = cv2.threshold(np.asarray(mask), 10, 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            contour = max(contours, key=cv2.contourArea, default=None)
            if contour is not None and cv2.contourArea(contour) > 20:
                x, y, w, h = cv2.boundingRect(contour)
                cx = int((x + w // 2) * width / small.shape[1])
                cy = int((y + h // 2) * height / small.shape[0])
                return max(0, min(cx - side // 2, width - side)), max(0, min(cy - side // 2, height - side)), side, True
        return (width - side) // 2, (height - side) // 2, side, False

    def prepare(self, contents: bytes, claimed_type: str) -> PreparedImage:
        rgb, mime_type, extension = _decode(contents, claimed_type, self.max_pixels)
        x, y, side, found = self._square(rgb)
        model_rgb = area_resize(tf.convert_to_tensor(rgb[y:y + side, x:x + side]))
        return PreparedImage(
            model_rgb, (x, y, side),
            "subject_center" if found else "image_center", mime_type, extension,
        )


def normalize_for_convnext(image: tf.Tensor) -> tf.Tensor:
    # Keras ConvNeXt preprocess_input keeps [0, 255]; the checkpoint normalizes in its stem.
    return preprocess_convnext(tf.cast(image, tf.float32))
