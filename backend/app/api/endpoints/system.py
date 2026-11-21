from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from app.ml.types import DummyPredictor, IMAGE_SIZE, SPATIAL_LAYER

router = APIRouter(tags=["System"])


@router.get("/health")
@router.head("/health", include_in_schema=False)
async def health(request: Request) -> Response:
    report = request.app.state.health
    # Trả về 200 OK khi mô hình đã nạp sẵn sàng (kể cả khi chưa cấu hình cloud storage lúc test local)
    status_code = 200 if report.get("model") in ("loaded", "pending", "mock") and report.get("status") != "error" else 503
    if request.method == "HEAD":
        return Response(status_code=status_code, headers={"Cache-Control": "no-store"})
    return JSONResponse(report, status_code=status_code, headers={"Cache-Control": "no-store"})


@router.get("/model-info")
async def model_info(request: Request) -> dict:
    model = request.app.state.model
    settings = request.app.state.settings
    safety = request.app.state.safety
    classes = safety.thresholds.classes
    is_mock = isinstance(model, DummyPredictor)
    return {
        "architecture": "ConvNeXt-Tiny",
        "model_version": None if is_mock else model.checkpoint.removesuffix(".keras"),
        "checkpoint": None if is_mock else model.checkpoint,
        "is_mock": is_mock,
        "input_size": list(IMAGE_SIZE),
        "class_labels": list(model.class_labels),
        "waste_types": [classes.details[label].name_vi for label in classes.labels],
        "confidence_thresholds": safety.thresholds.confidence_by_name(),
        "margin_threshold": safety.thresholds.gate_thresholds.tau_margin,
        "safety_thresholds": safety.source,
        "threshold_unit": "probability",
        "adaptive_assessment_enabled": settings.adaptive_assessment_enabled,
        "tta_views": None if is_mock else int(settings.tta_views),
        "smart_crop": settings.smart_crop,
        "spatial_layer": None if is_mock else SPATIAL_LAYER,
    }
