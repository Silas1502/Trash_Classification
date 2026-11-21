"""Best-effort reclamation of unused heap pages and model file cache on Linux."""

from contextlib import suppress
import ctypes
import os
from pathlib import Path
import sys


_trim = None
if sys.platform == "linux":
    _trim = getattr(ctypes.CDLL(None), "malloc_trim", None)
    if _trim is not None:
        _trim.argtypes = [ctypes.c_size_t]
        _trim.restype = ctypes.c_int


def trim_heap() -> None:
    if _trim is not None:
        _trim(0)


def release_file_cache(path: Path, *, sync: bool = False) -> None:
    if not hasattr(os, "posix_fadvise"):
        return
    with suppress(OSError), path.open("r+b" if sync else "rb") as file:
        if sync:
            os.fdatasync(file.fileno())
        os.posix_fadvise(file.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)
