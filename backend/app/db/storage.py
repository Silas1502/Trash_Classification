from dataclasses import dataclass


PREDICTION_FOLDERS_BY_LABEL = {
    "Nhựa": "plastic",
    "Giấy": "paper",
    "Kim loại": "metal",
    "Thủy tinh": "glass",
}
MANUAL_PREDICTION_FOLDER = "manual"


@dataclass(frozen=True)
class ImageObject:
    key: str
    content: bytes
    mime_type: str
