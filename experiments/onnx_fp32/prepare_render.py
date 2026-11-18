"""Package exported ONNX artifacts for the native Render backend."""

import base64
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from backend.onnx_fp32.render_model import CHUNK_BYTES, FILES, part_name, unpack

ROOT = Path(__file__).resolve().parents[2]
EXPERIMENT = Path(__file__).resolve().parent
OUTPUT = ROOT / ".venv" / "render-model-parts"
KEY_PATH = OUTPUT.parent / "render-onnx-model-key.txt"


def main():
    if OUTPUT.exists():
        raise SystemExit(f"Output already exists: {OUTPUT}")
    if not KEY_PATH.is_file():
        raise SystemExit("The existing Render model key is required.")
    cipher = AESGCM(base64.b64decode(KEY_PATH.read_bytes().strip(), validate=True))
    artifacts = EXPERIMENT / "artifacts"
    with TemporaryDirectory(dir=OUTPUT.parent) as staging:
        staged = Path(staging)
        parts = staged / "model-parts"
        parts.mkdir()
        shutil.copyfile(artifacts / "manifest.json", parts / "manifest.json")
        for name in FILES:
            with (artifacts / name).open("rb") as source:
                for index, chunk in enumerate(iter(lambda: source.read(CHUNK_BYTES), b"")):
                    part = part_name(name, index)
                    nonce = os.urandom(12)
                    (parts / part).write_bytes(nonce + cipher.encrypt(nonce, chunk, part.encode("ascii")))
        unpack(parts, staged / "recovered", KEY_PATH)
        parts.rename(OUTPUT)
    print(f"Verified the decrypted model hashes. Encrypted model parts: {OUTPUT}")


if __name__ == "__main__":
    main()
