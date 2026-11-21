import asyncio
import logging
from collections.abc import Callable
from contextlib import AsyncExitStack, asynccontextmanager, suppress

import anyio
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import Headers
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Receive, Scope, Send

from app.api.router import router
from app.core.config import Settings
from app.core.errors import ApiError
from app.core.safety_gate import SafetyFilter
from app.db.imagekit_storage import ImageKitStorage
from app.db.imagekit_cleanup import watch_imagekit_cleanup
from app.db.supabase_db import SupabaseHistory
from app.db.supabase_storage import SupabaseStorage
from app.ml.types import BatchClassifier, DummyPredictor, ModelBundle
from app.ml.preprocessor import ImagePreprocessor

logger = logging.getLogger(__name__)


def _payload(code: str, message: str, **extra) -> dict:
    return {"detail": message, "error": {"code": code, "message": message, **extra}}


class UploadLimits:
    """Bound multipart bytes before files can accumulate in the parser or spool device."""

    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.limits = {
            "/api/v1/predict/single": settings.max_upload_bytes + 128 * 1024,
            "/api/v1/predict/batch": settings.max_batch_bytes + 128 * 1024,
        }

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] != "POST":
            await self.app(scope, receive, send)
            return
        limit = self.limits.get(scope["path"].rstrip("/"))
        if limit is None:
            await self.app(scope, receive, send)
            return
        too_large = "Dữ liệu tải lên vượt giới hạn cho phép."
        declared = Headers(scope=scope).get("content-length")
        if declared is not None and declared.isdecimal() and (len(declared) > 15 or int(declared) > limit):
            await JSONResponse(_payload("upload_too_large", too_large), 413)(scope, receive, send)
            return
        slots = scope["app"].state.prediction_slots
        try:
            slots.acquire_nowait()
        except anyio.WouldBlock:
            busy = JSONResponse(
                _payload("prediction_busy", "Máy chủ đang xử lý các yêu cầu khác. Hãy thử lại."),
                503, headers={"Retry-After": "2"},
            )
            await busy(scope, receive, send)
            return
        received = 0

        async def receive_limited():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise HTTPException(413, too_large)
            return message

        try:
            await self.app(scope, receive_limited, send)
        finally:
            slots.release()


def _health(model: str, db: str, storage: str) -> dict:
    cloud_ok = db in ("connected", "not_configured") and storage in ("reachable", "not_configured")
    is_healthy = model in ("loaded", "pending", "mock") and cloud_ok
    return {
        "status": "healthy" if is_healthy else "degraded",
        "model": model, "database": db, "storage": storage,
        "mongodb": db, "r2": storage,  # Backward compatibility
    }


async def _watch_dependencies(app: FastAPI) -> None:
    state = app.state

    async def check(probe: Callable, name: str, ok: str, failure: str) -> str:
        try:
            await probe()
        except Exception as exc:
            if state.health.get(name) != failure:
                logger.warning("%s health probe failed: %s", name, type(exc).__name__)
            return failure
        return ok

    async def check_db() -> str:
        if state.history is None:
            return "not_configured"
        return await check(state.history.check, "database", "connected", "disconnected")

    async def check_storage() -> str:
        if state.storage is None:
            return "not_configured"
        return await check(lambda: run_in_threadpool(state.storage.check), "storage", "reachable", "unreachable")

    while True:
        db, storage = await asyncio.gather(check_db(), check_storage())
        state.health = _health(state.health["model"], db, storage)
        await asyncio.sleep(state.settings.health_probe_interval_seconds)


def create_app(
    settings: Settings | None = None, *,
    model: ModelBundle | DummyPredictor | None = None,
    batch_classifier: BatchClassifier | None = None,
    model_loader: Callable | None = None,
    preprocessor_factory: Callable = ImagePreprocessor,
    defer_model_load: bool = False,
) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        state = app.state
        state.settings = settings
        state.safety = await run_in_threadpool(SafetyFilter.load, settings.thresholds_path)
        loader = model_loader
        if model is None and loader is None:
            from app.ml.model_loader import load_model
            loader = load_model
        state.model = model

        def load_model_when_needed():
            # Prediction calls this after preprocessing, while holding the ML slot.
            try:
                loaded = loader(settings, state.safety.thresholds.classes.labels)
            except Exception as exc:
                logger.exception("Deferred prediction model failed to load")
                state.health = _health("error", state.health["database"], state.health["storage"])
                raise ApiError(503, "model_unavailable", "Chưa thể nạp mô hình phân loại. Hãy thử lại.") from exc
            state.model = loaded
            state.health = _health("loaded", state.health["database"], state.health["storage"])

        state.load_model_when_needed = load_model_when_needed
        if model is None and not defer_model_load:
            state.model = await run_in_threadpool(loader, settings, state.safety.thresholds.classes.labels)
        classifier = batch_classifier
        if classifier is None:
            from app.ml.inference import classify_batch
            classifier = classify_batch
        state.batch_classifier = classifier
        state.preprocessor = await run_in_threadpool(
            preprocessor_factory, settings.max_image_pixels, settings.smart_crop,
        )
        state.ml_slot = anyio.Semaphore(1)
        state.prediction_slots = anyio.Semaphore(settings.max_prediction_requests)
        state.storage_slots = anyio.Semaphore(settings.storage_concurrency)
        state.history = state.storage = None

        async with AsyncExitStack() as cleanup:
            if settings.supabase_url and settings.supabase_key:
                state.history = SupabaseHistory(settings.supabase_url, settings.supabase_key.get_secret_value())
                cleanup.callback(state.history.close)

            if settings.imagekit_private_key and settings.imagekit_url_endpoint:
                state.storage = ImageKitStorage(settings)
                cleanup.callback(state.storage.close)
            elif settings.supabase_url and settings.supabase_key:
                state.storage = SupabaseStorage(settings)
                cleanup.callback(state.storage.close)

            state.health = _health(
                "mock" if isinstance(state.model, DummyPredictor)
                else "pending" if state.model is None and defer_model_load else "loaded",
                "checking" if state.history else "not_configured",
                "checking" if state.storage else "not_configured",
            )
            cleanup_watcher = None
            if settings.imagekit_cleanup_token:
                if state.history is None or not isinstance(state.storage, ImageKitStorage):
                    raise RuntimeError("IMAGEKIT_CLEANUP_TOKEN requires Supabase and ImageKit configuration")
                cleanup_watcher = asyncio.create_task(watch_imagekit_cleanup(
                    state.history, state.storage, settings.imagekit_cleanup_token.get_secret_value(),
                    settings.imagekit_cleanup_interval_seconds,
                ))
            watcher = asyncio.create_task(_watch_dependencies(app))
            try:
                yield
            finally:
                watcher.cancel()
                if cleanup_watcher is not None:
                    cleanup_watcher.cancel()
                    with suppress(asyncio.CancelledError):
                        await cleanup_watcher
                with suppress(asyncio.CancelledError):
                    await watcher

    app = FastAPI(title="Trash Classification API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(UploadLimits, settings=settings)
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=False,
        allow_methods=["GET", "HEAD", "POST"], allow_headers=["*"], expose_headers=["Content-Disposition"],
    )

    @app.exception_handler(ApiError)
    async def service_error(_: Request, exc: ApiError):
        return JSONResponse(_payload(exc.code, exc.message), exc.status)

    @app.exception_handler(HTTPException)
    async def http_error(_: Request, exc: HTTPException):
        code = "upload_too_large" if exc.status_code == 413 else "http_error"
        return JSONResponse(_payload(code, str(exc.detail)), exc.status_code, headers=exc.headers)

    @app.exception_handler(RequestValidationError)
    async def validation_error(_: Request, exc: RequestValidationError):
        errors = [{"loc": entry["loc"], "msg": entry["msg"], "type": entry["type"]} for entry in exc.errors()]
        return JSONResponse(_payload("validation_error", "Dữ liệu yêu cầu không hợp lệ.", fields=errors), 422)

    @app.exception_handler(Exception)
    async def unexpected_error(request: Request, exc: Exception):
        logger.error("Unhandled API error for %s", request.method, exc_info=exc)
        response = JSONResponse(_payload("internal_error", "Có lỗi khi xử lý yêu cầu."), 500)
        # ServerErrorMiddleware sits outside CORS for unhandled exceptions.
        origin = request.headers.get("origin")
        if origin and ("*" in settings.cors_origins or origin in settings.cors_origins):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
        return response

    app.include_router(router)
    return app


app = create_app()
