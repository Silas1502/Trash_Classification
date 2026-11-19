"""U²-NetP foreground masks using the same ONNX weights as rembg's u2netp session."""

import hashlib
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

import numpy as np
from PIL import Image


MODEL_NAME = "u2netp.onnx"
MODEL_URL = "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
MODEL_SHA256 = "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8"
MODEL_BYTES = 4_574_861
MASK_SIZE = (320, 320)
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


class U2NetP:
    def __init__(self) -> None:
        import onnxruntime as ort

        options = ort.SessionOptions()
        options.intra_op_num_threads = 1
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        # Avoid the larger activation buffers from the CPU layout optimizations.
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_EXTENDED
        self.session = ort.InferenceSession(str(_model_path()), options, providers=["CPUExecutionProvider"])
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name

    def __call__(self, rgb: np.ndarray) -> np.ndarray:
        image = Image.fromarray(rgb)
        pixels = np.asarray(image.resize(MASK_SIZE, Image.Resampling.LANCZOS))
        # Match the normalization in rembg's U2netpSession.
        channels = (pixels / max(pixels.max(), 1e-6) - MEAN) / STD
        tensor = channels.transpose(2, 0, 1)[None].astype(np.float32)
        output, = self.session.run([self.output_name], {self.input_name: tensor})
        prediction = output[0, 0]
        minimum, maximum = prediction.min(), prediction.max()
        if not maximum > minimum:
            return np.zeros(rgb.shape[:2], dtype=np.uint8)
        mask = ((prediction - minimum) / (maximum - minimum) * 255).astype(np.uint8)
        return np.asarray(Image.fromarray(mask).resize(image.size, Image.Resampling.LANCZOS))
