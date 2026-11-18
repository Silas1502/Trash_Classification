"""Check decoder equivalence, EXIF, color modes and AREA resize boundaries."""

from io import BytesIO
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))
from app.ml.preprocessor import _decode
from .runtime import area_resize, decode


def main():
    rng = np.random.default_rng(1502)
    rgb = rng.integers(0, 256, (29, 17, 3), dtype=np.uint8)
    checks = 0
    for mode, format in [("RGB", "PNG"), ("RGBA", "PNG"), ("L", "PNG"), ("P", "PNG"), ("CMYK", "JPEG"), ("RGB", "WEBP")]:
        with Image.fromarray(rgb).convert(mode) as image:
            buffer = BytesIO()
            image.save(buffer, format=format)
        contents = buffer.getvalue()
        mime = {"PNG": "image/png", "JPEG": "image/jpeg", "WEBP": "image/webp"}[format]
        a, mime_a, ext_a = _decode(contents, mime, 16_000_000)
        b, mime_b, ext_b = decode(contents, mime)
        np.testing.assert_array_equal(a, b)
        assert (mime_a, ext_a) == (mime_b, ext_b)
        checks += 1
    for orientation in range(1, 9):
        with Image.fromarray(rgb) as image:
            exif = image.getexif()
            exif[274] = orientation
            buffer = BytesIO()
            image.save(buffer, format="JPEG", exif=exif)
        contents = buffer.getvalue()
        np.testing.assert_array_equal(_decode(contents, "image/jpeg", 16_000_000)[0], decode(contents, "image/jpeg")[0])
        checks += 1
    resize_error = None
    if "--tensorflow" in sys.argv:
        import tensorflow as tf
        resize_error = 0.0
        for height, width in [(1, 1), (17, 29), (288, 288), (320, 320), (321, 319), (513, 777), (1024, 683)]:
            source = rng.integers(0, 256, (height, width, 3), dtype=np.uint8)
            expected = tf.image.resize(source, (320, 320), method="area", antialias=True).numpy()
            actual = area_resize(source)
            error = float(np.abs(actual - expected).max())
            resize_error = max(resize_error, error)
            np.testing.assert_allclose(actual, expected, rtol=0, atol=3e-4)
            checks += 1
    print(json.dumps({"passed": True, "checks": checks, "resize_max_abs_error": resize_error}, indent=2))


if __name__ == "__main__":
    main()
