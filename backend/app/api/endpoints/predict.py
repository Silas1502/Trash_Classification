import asyncio
import logging
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import PurePosixPath
from time import perf_counter
from typing import Annotated, Literal
from uuid import uuid4

from fastapi import APIRouter, File, Request, UploadFile
from starlette.concurrency import run_in_threadpool

from app.core.config import Settings
from app.core.errors import ApiError
from app.db.storage import ImageObject
from app.ml.types import DummyPredictor, InferenceResult
from app.ml.preprocessor import IMAGE_TYPES, InvalidImage, PreparedImage
from app.schemas.history import HistoryItem
from app.schemas.prediction import BatchError, BatchResult, PredictionMetadata, PredictionResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/predict", tags=["Prediction"])
MIME_TYPES = {value[0] for value in IMAGE_TYPES.values()}
Mode = Literal["single", "batch"]


@dataclass(frozen=True)
class ImageInput:
    index: int
    file_name: str
    contents: bytes
    mime_type: str


def _file_name(file: UploadFile) -> str:
    raw = (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1]
    name = unicodedata.normalize("NFC", raw)
    name = "".join(c for c in name if not unicodedata.category(c).startswith("C")).strip(" .")
    return name[:180] or "image"


async def _read(file: UploadFile, index: int, settings: Settings) -> ImageInput:
    try:
        mime = (file.content_type or "").lower().split(";", 1)[0].strip()
        if mime not in MIME_TYPES:
            raise ApiError(415, "unsupported_image_type", "Chỉ hỗ trợ ảnh JPEG, PNG hoặc WebP.")
        limit = settings.max_upload_bytes
        if file.size is not None and file.size > limit:
            raise ApiError(413, "image_too_large", f"Ảnh vượt giới hạn {limit:,} byte.")
        contents = await file.read(limit + 1)
        if not contents:
            raise ApiError(400, "empty_image", "Tệp ảnh không có dữ liệu.")
        if len(contents) > limit:
            raise ApiError(413, "image_too_large", f"Ảnh vượt giới hạn {limit:,} byte.")
        return ImageInput(index, _file_name(file), contents, mime)
    finally:
        await file.close()


def _require_cloud(request: Request) -> None:
    if isinstance(request.app.state.model, DummyPredictor):
        return
    if request.app.state.history is None or request.app.state.storage is None:
        raise ApiError(503, "cloud_not_configured", "Cần cấu hình Supabase Database và ImageKit hoặc Supabase Storage để lưu kết quả.")


def _compute(state, inputs: list[ImageInput]):
    valid: list[tuple[ImageInput, PreparedImage, float]] = []
    errors = []
    for source in inputs:
        started = perf_counter()
        try:
            image = state.preprocessor.prepare(source.contents, source.mime_type)
        except InvalidImage as exc:
            errors.append(BatchError(
                index=source.index, file_name=source.file_name, code="invalid_image", message=str(exc),
            ))
        else:
            preprocessing_ms = (perf_counter() - started) * 1000
            valid.append((source, image, preprocessing_ms))
    if not valid:
        return [], errors
    predictions = state.batch_classifier(state.model, [image for _, image, _ in valid], state.settings, state.safety)
    computed = [
        (source, image, output, round(preprocessing_ms + output.inference_time_ms + output.xai_time_ms, 2))
        for (source, image, preprocessing_ms), output in zip(valid, predictions, strict=True)
    ]
    return computed, errors


async def _persist(
    state, source: ImageInput, image: PreparedImage, output: InferenceResult, processing_time_ms: float, mode: Mode,
) -> PredictionResponse:
    id = uuid4()
    now = datetime.now(timezone.utc)
    is_mock = isinstance(state.model, DummyPredictor)
    original_url = gradcam_url = energy_url = None
    if not is_mock:
        if output.xai is None:
            raise RuntimeError("Missing explanation for a real model prediction.")
        day = now.strftime("%Y/%m/%d")
        stem = PurePosixPath(source.file_name).stem or "image"
        objects = (
            ImageObject(f"uploads/{mode}/{day}/{id}_{stem}{image.extension}", source.contents, image.mime_type),
            ImageObject(f"uploads/xai/{day}/{id}_gradcam_overlay.jpg", output.xai.gradcam_jpeg, "image/jpeg"),
            ImageObject(f"uploads/xai/{day}/{id}_spatial_energy_overlay.jpg", output.xai.spatial_energy_jpeg, "image/jpeg"),
        )
        async with state.storage_slots:
            original_url, gradcam_url, energy_url = await run_in_threadpool(state.storage.upload_images, objects)
    decision = output.decision
    result = PredictionResponse(
        id=id, file_name=source.file_name, image_url=original_url, xai_overlay_url=gradcam_url,
        xai_energy_overlay_url=energy_url, waste_type=decision.waste_type,
        confidence=round(decision.confidence * 100, 4), margin=round(decision.margin * 100, 4),
        checkpoint_1=round(decision.confidence_threshold * 100, 4),
        checkpoint_2=round(decision.margin_threshold * 100, 4),
        confidence_gate_passed=decision.confidence_gate_passed, margin_gate_passed=decision.margin_gate_passed,
        composite_score=round(decision.composite_score * 100, 4),
        tta_stability=None if decision.tta_stability is None else round(decision.tta_stability * 100, 4),
        decision_tier=decision.decision_tier, decision=decision.decision, reason=decision.reason, is_mock=is_mock,
        pipeline_type=decision.pipeline_type, status=decision.status, suggestion=decision.suggestion,
        created_at=now, processing_time_ms=processing_time_ms,
    )
    if is_mock:
        return result
    history = HistoryItem(
        **result.model_dump(exclude={"processing_time_ms"}),
        metadata=PredictionMetadata(
            file_size=len(source.contents), mime_type=image.mime_type,
            inference_time_ms=round(output.inference_time_ms, 2), xai_time_ms=round(output.xai_time_ms, 2),
            processing_time_ms=processing_time_ms,
            model_version=state.model.checkpoint.removesuffix(".keras"), tta_views=int(state.settings.tta_views),
            crop_box=image.crop_box, crop_strategy=image.crop_strategy,
        ),
    )
    await state.history.insert(history)
    return result


@router.post("/single", response_model=PredictionResponse)
async def predict_single(request: Request, file: Annotated[UploadFile, File()]) -> PredictionResponse:
    state = request.app.state
    source = await _read(file, 0, state.settings)
    _require_cloud(request)
    async with state.ml_slot:
        results, errors = await run_in_threadpool(_compute, state, [source])
    if errors:
        raise ApiError(400, errors[0].code, errors[0].message)
    return await _persist(state, *results[0], "single")


@router.post("/batch", response_model=BatchResult)
async def predict_batch(request: Request, files: Annotated[list[UploadFile], File()]) -> BatchResult:
    state = request.app.state
    settings = state.settings
    if not 1 <= len(files) <= settings.max_batch_files:
        raise ApiError(413, "too_many_files", f"Mỗi lô chỉ nhận tối đa {settings.max_batch_files} ảnh.")
    if sum(file.size or 0 for file in files) > settings.max_batch_bytes:
        raise ApiError(413, "batch_too_large", f"Lô ảnh vượt giới hạn {settings.max_batch_bytes:,} byte.")
    _require_cloud(request)
    results: list[PredictionResponse] = []
    errors: list[BatchError] = []

    async def save(source: ImageInput, image: PreparedImage, prediction: InferenceResult, processing_time_ms: float):
        try:
            return await _persist(state, source, image, prediction, processing_time_ms, "batch")
        except ApiError as exc:
            return BatchError(index=source.index, file_name=source.file_name, code=exc.code, message=exc.message)

    step = settings.inference_batch_size
    for start in range(0, len(files), step):
        inputs = []
        for index, file in enumerate(files[start:start + step], start=start):
            try:
                inputs.append(await _read(file, index, settings))
            except ApiError as exc:
                errors.append(BatchError(index=index, file_name=_file_name(file), code=exc.code, message=exc.message))
        if not inputs:
            continue
        try:
            async with state.ml_slot:
                computed, invalid = await run_in_threadpool(_compute, state, inputs)
        except ApiError as exc:
            errors.extend(BatchError(
                index=source.index, file_name=source.file_name, code=exc.code, message=exc.message,
            ) for source in inputs)
            continue
        except Exception:
            logger.exception("Batch inference failed")
            errors.extend(BatchError(
                index=source.index, file_name=source.file_name, code="inference_failed",
                message="Không thể phân loại ảnh vào lúc này.",
            ) for source in inputs)
            continue
        finally:
            inputs.clear()
        errors.extend(invalid)
        try:
            outcomes = await asyncio.gather(*(save(*item) for item in computed))
        finally:
            computed.clear()
        for outcome in outcomes:
            if isinstance(outcome, BatchError):
                errors.append(outcome)
            else:
                results.append(outcome)
    if not results and errors and all(item.code in {"storage_unavailable", "database_unavailable"} for item in errors):
        raise ApiError(503, "cloud_unavailable", "Không thể lưu kết quả lô ảnh vào lúc này.")
    return BatchResult(
        batch_id=uuid4(), total_images=len(files), processed_images=len(files), pending_images=0,
        succeeded_images=len(results), failed_images=len(errors), completion_rate=100,
        results=results, errors=sorted(errors, key=lambda item: item.index),
    )
