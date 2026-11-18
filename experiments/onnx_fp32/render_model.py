"""Open the encrypted model chunks during the Render build."""

import base64
import hashlib
import json
import os
from contextlib import suppress
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CHUNK_BYTES = 16 * 1024 * 1024
FILES = ("forward.onnx", "gradient.onnx")


def part_name(name: str, index: int) -> str:
    return f"{name}.{index:03}.enc"


def unpack(source: Path, destination: Path, key_file: Path) -> None:
    cipher = AESGCM(base64.b64decode(key_file.read_bytes().strip(), validate=True))
    manifest_bytes = (source / "manifest.json").read_bytes()
    manifest = json.loads(manifest_bytes)
    destination.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        expected = manifest["files"][name]
        digest = hashlib.sha256()
        remaining = expected["bytes"]
        target = destination / name
        with target.open("wb") as output:
            for index in range((remaining + CHUNK_BYTES - 1) // CHUNK_BYTES):
                part = part_name(name, index)
                with (source / part).open("rb") as encrypted:
                    sealed = encrypted.read()
                    if hasattr(os, "posix_fadvise"):
                        # The encrypted chunks are used once at startup.
                        with suppress(OSError):
                            os.posix_fadvise(encrypted.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
                data = cipher.decrypt(sealed[:12], sealed[12:], part.encode("ascii"))
                if len(data) != min(remaining, CHUNK_BYTES):
                    raise ValueError(f"Unexpected length in {part}")
                remaining -= len(data)
                digest.update(data)
                output.write(data)
        if remaining or digest.hexdigest() != expected["sha256"]:
            raise ValueError(f"Model verification failed for {name}")
    (destination / "manifest.json").write_bytes(manifest_bytes)


if __name__ == "__main__":
    import sys

    unpack(*(Path(arg) for arg in sys.argv[1:]))
