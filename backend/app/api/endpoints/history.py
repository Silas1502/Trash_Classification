import csv
import io
from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.core.errors import ApiError
from app.db.supabase_db import SupabaseHistory
from app.schemas.history import HistoryFilters, HistoryItem, HistoryPage, HistoryQuery

router = APIRouter(prefix="/history", tags=["History"])
CSV_COLUMNS = (
    "id", "file_name", "waste_type", "confidence", "checkpoint_1", "checkpoint_2", "margin",
    "composite_score", "tta_stability", "decision_tier", "decision", "reason",
    "pipeline_type", "status", "created_at", "image_url", "xai_overlay_url",
    "xai_energy_overlay_url", "suggestion",
)


def get_history(request: Request) -> SupabaseHistory:
    history = request.app.state.history
    if history is None:
        raise ApiError(503, "database_unavailable", "Chưa cấu hình kết nối Supabase.")
    return history


@router.get("", response_model=HistoryPage)
async def list_history(request: Request, query: Annotated[HistoryQuery, Query()]) -> HistoryPage:
    items, total = await get_history(request).list(query)
    return HistoryPage(
        items=items, total=total, page=query.page, limit=query.limit, total_pages=ceil(total / query.limit),
    )


def _csv_cell(value):
    if isinstance(value, str) and (
        value.lstrip()[:1] in ("=", "+", "-", "@") or value.startswith(("\t", "\r", "\n"))
    ):
        return "'" + value
    return value


@router.get("/export", response_class=StreamingResponse)
async def export_history(request: Request, query: Annotated[HistoryFilters, Query()]) -> StreamingResponse:
    records = get_history(request).export(query)
    try:
        # Run the initial query before committing the response status.
        first = await anext(records, None)
    except BaseException:
        await records.aclose()
        raise

    async def generate():
        buffer = io.StringIO(newline="")
        writer = csv.writer(buffer)

        def encode(values):
            writer.writerow(values)
            chunk = buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            return chunk

        def row(item: HistoryItem):
            data = item.model_dump(mode="json")
            return encode(_csv_cell(data[field]) for field in CSV_COLUMNS)

        try:
            yield "\ufeff" + encode(CSV_COLUMNS)
            if first is not None:
                yield row(first)
            async for record in records:
                yield row(record)
        finally:
            await records.aclose()

    return StreamingResponse(
        generate(), media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="prediction-history.csv"'},
        background=BackgroundTask(records.aclose),
    )


@router.get("/{id}", response_model=HistoryItem)
async def history_detail(id: UUID, request: Request) -> HistoryItem:
    item = await get_history(request).get(id)
    if item is None:
        raise ApiError(404, "prediction_not_found", "Không tìm thấy bản ghi phân loại.")
    return item
