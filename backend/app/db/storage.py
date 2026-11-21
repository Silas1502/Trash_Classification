from dataclasses import dataclass


PREDICTION_FOLDERS_BY_LABEL = {
    "Nhựa": "plastic",
    "Giấy": "paper",
    "Kim loại": "metal",
    "Thủy tinh": "glass",
}
MANUAL_PREDICTION_FOLDER = "manual"


def prediction_tag(prediction_id: str) -> str:
    return f"prediction-{prediction_id}"


@dataclass(frozen=True)
class ImageObject:
    key: str
    content: bytes
    mime_type: str
    ownership_tag: str | None = None
