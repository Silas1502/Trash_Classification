from dataclasses import dataclass


@dataclass(frozen=True)
class ImageObject:
    key: str
    content: bytes
    mime_type: str
