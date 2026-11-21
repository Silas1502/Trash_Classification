"""U²-NetP foreground masks using the same ONNX weights as rembg's u2netp session."""

import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import numpy as np
from PIL import Image

from .memory import release_file_cache, trim_heap


MODEL_NAME = "u2netp.onnx"
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
MODEL_SHA256 = "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8"
MODEL_BYTES = 4_574_861
MASK_SIZE = (320, 320)
# The pinned ONNX graph uses shape-driven resize operators. These positions are
# the two spatial dimensions on its input and two fixed-shape outputs.
MASK256_DIMENSION_OFFSETS = (4574282, 4574287, 4574316, 4574321, 4574350, 4574355)
MASK256_SHA256 = "0e66cb83fa3b858ef267d040032e0b56f389b39f064c7c791e2830d4742bf61c"
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


def _verify_model(path: Path) -> None:
    with path.open("rb") as model:
        if hashlib.file_digest(model, "sha256").hexdigest() != MODEL_SHA256:
            raise ValueError(f"Invalid U²-NetP checksum: {path}")


def _model_path() -> Path:
    configured_home = os.environ.get("U2NET_HOME")
    if configured_home:
        candidates = (Path(configured_home).expanduser() / MODEL_NAME,)
    else:
        rembg_home = Path(os.environ.get("REMBG_HOME") or Path.home() / ".rembg").expanduser()
        candidates = (rembg_home / "models" / "u2netp" / MODEL_NAME, Path.home() / ".u2net" / MODEL_NAME)

    for path in candidates:
        if path.is_file():
            _verify_model(path)
            return path

    path = candidates[0]
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            with urlopen(MODEL_URL, timeout=30) as response:
                data = response.read(MODEL_BYTES + 1)
            if len(data) != MODEL_BYTES:
                raise ValueError("Unexpected U²-NetP model download size.")
            output.write(data)
            output.close()
            _verify_model(temporary)
            temporary.replace(path)
        finally:
            output.close()
            temporary.unlink(missing_ok=True)
    return path


def _mask256_path(original: Path) -> Path:
    path = original.with_name("u2netp-256.onnx")
    if path.is_file():
        with path.open("rb") as cached:
            if hashlib.file_digest(cached, "sha256").hexdigest() == MASK256_SHA256:
                return path
    # 320 and 256 are both two-byte protobuf varints. Changing their metadata
    # leaves the original graph operators and all weight bytes intact.
    model = bytearray(original.read_bytes())
    for offset in MASK256_DIMENSION_OFFSETS:
        model[offset:offset + 2] = b"\x80\x02"
    if hashlib.sha256(model).hexdigest() != MASK256_SHA256:
        raise ValueError("Unexpected ONNX graph when preparing U²-NetP at 256 × 256")
    with NamedTemporaryFile(dir=path.parent, delete=False) as output:
        temporary = Path(output.name)
        try:
            output.write(model)
            output.close()
            temporary.replace(path)
        finally:
            output.close()
            temporary.unlink(missing_ok=True)
    return path


class U2NetP:
    def __init__(self, size: int = MASK_SIZE[0], *, reclaim_memory: bool = False) -> None:
        import onnxruntime as ort

        if size not in (256, 320):
            raise ValueError("U²-NetP input size must be 256 or 320")
        self.size = size
        self.reclaim_memory = reclaim_memory
        original = _model_path()
        path = _mask256_path(original) if size == 256 else original
        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        # Avoid the larger activation buffers from the CPU layout optimizations.
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        self.session = ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        if reclaim_memory:
            release_file_cache(original, sync=True)
            if path != original:
                release_file_cache(path, sync=True)
            trim_heap()

    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        image = Image.fromarray(rgb)
        pixels = np.asarray(image.resize((self.size, self.size), Image.Resampling.LANCZOS))
        # Match the normalization in rembg's U2netpSession.
        channels = (pixels / max(pixels.max(), 1e-6) - MEAN) / STD
        tensor = channels.transpose(2, 0, 1)[None].astype(np.float32)
        if self.reclaim_memory:
            trim_heap()
        output, = self.session.run([self.output_name], {self.input_name: tensor})
        prediction = output[0, 0]
        minimum, maximum = prediction.min(), prediction.max()
        if not maximum > minimum:
            return np.zeros(rgb.shape[:2], dtype=np.uint8)
        mask = ((prediction - minimum) / (maximum - minimum) * 255).astype(np.uint8)
        return np.asarray(Image.fromarray(mask).resize(image.size, Image.Resampling.LANCZOS))
