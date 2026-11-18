import csv
import io
from datetime import datetime, time, timedelta, timezone
from math import ceil
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse
from starlette.background import BackgroundTask

from app.core.errors import ApiError
from app.db.supabase_db import SupabaseHistory
from app.schemas.history import (
    HistoryFilters, HistoryItem, HistoryPage, HistoryQuery, HistoryStatistics, HistoryStatisticsRange,
    HistoryDailyPage, HistoryDailyQuery, HistoryTrendPeriod, HistoryTrends,
)

router = APIRouter(prefix="/history", tags=["History"])
VIETNAM_TIMEZONE = timezone(timedelta(hours=7))
TREND_DAYS = {"today": 1, "week": 7, "month": 30, "quarter": 90}
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


@router.get("/statistics")
async def history_statistics(request: Request, dates: Annotated[HistoryStatisticsRange, Query()]) -> HistoryStatistics:
    start = datetime.combine(dates.start_date, time.min, tzinfo=VIETNAM_TIMEZONE)
    end = datetime.combine(dates.end_date, time.max, tzinfo=VIETNAM_TIMEZONE)
    return await get_history(request).statistics(start, end)


@router.get("/trends")
async def history_trends(request: Request, period: HistoryTrendPeriod = "week") -> HistoryTrends:
    end = datetime.now(VIETNAM_TIMEZONE)
    first_day = end.date() - timedelta(days=TREND_DAYS[period] - 1)
    start = datetime.combine(first_day, time.min, tzinfo=VIETNAM_TIMEZONE)
    unit = {"today": "hour", "quarter": "week"}.get(period, "day")
    return await get_history(request).trends(start, end, unit=unit)


@router.get("/daily")
async def history_daily(
    request: Request, dates: Annotated[HistoryDailyQuery, Query()],
) -> HistoryDailyPage:
    page_size = 5
    page = dates.page
    total_days = (dates.end_date - dates.start_date).days + 1
    total_pages = ceil(total_days / page_size)
    if page > total_pages:
        return HistoryDailyPage(points=[], page=page, total_days=total_days, total_pages=total_pages)
    first_day = dates.start_date + timedelta(days=(page - 1) * page_size)
    last_day = first_day + timedelta(days=min(page_size - 1, (dates.end_date - first_day).days))
    start = datetime.combine(first_day, time.min, tzinfo=VIETNAM_TIMEZONE)
    end = datetime.combine(last_day, time.max, tzinfo=VIETNAM_TIMEZONE)
    data = await get_history(request).trends(start, end, unit="day")
    return HistoryDailyPage(points=data.points, page=page, total_days=total_days, total_pages=total_pages)


@router.get("/{id}", response_model=HistoryItem)
async def history_detail(id: UUID, request: Request) -> HistoryItem:
    item = await get_history(request).get(id)
    if item is None:
        raise ApiError(404, "prediction_not_found", "Không tìm thấy bản ghi phân loại.")
    return item
