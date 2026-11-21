import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from typing import Literal, get_args
from uuid import UUID

from supabase import create_client, Client

from app.core.errors import ApiError
from app.schemas.history import HistoryFilters, HistoryItem, HistoryQuery, HistoryStatistics, HistoryTrendPoint, HistoryTrends
from app.schemas.prediction import PipelineType, WasteType

logger = logging.getLogger(__name__)


class SupabaseHistory:
    def __init__(self, url: str, key: str) -> None:
        self.url = url
        self.key = key
        self.client: Client = create_client(url, key)

    def close(self) -> None:
        pass

    async def check(self) -> None:
        # Check connection by querying 1 record from prediction_logs
        def _sync_check():
            res = self.client.table("prediction_logs").select("id").limit(1).execute()
            if hasattr(res, "error") and res.error:
                raise RuntimeError(f"Supabase check failed: {res.error}")
            return res

        try:
            await asyncio.to_thread(_sync_check)
        except Exception as exc:
            logger.warning("Supabase health check failed: %s", exc)
            raise

    async def insert(self, item: HistoryItem) -> None:
        doc = item.model_dump(mode="json")
        doc["id"] = str(item.id)
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()

        def _sync_insert():
            return self.client.table("prediction_logs").insert(doc).execute()

        try:
            await asyncio.to_thread(_sync_insert)
        except Exception as exc:
            logger.warning("Supabase insert failed: %s", exc)
            raise ApiError(503, "database_unavailable", "Không thể ghi lịch sử vào Supabase lúc này.") from exc

    async def next_image_number(self, category: str, token: str) -> int:
        def allocate() -> int:
            number = self.client.rpc("imagekit_next_number", {"p_group": category, "p_token": token}).execute().data
            if type(number) is not int or number < 1:
                raise ValueError("Expected a positive image number")
            return number

        try:
            return await asyncio.to_thread(allocate)
        except Exception as exc:
            logger.warning("Supabase image numbering failed: %s", type(exc).__name__)
            raise ApiError(503, "database_unavailable", "Không thể cấp số thứ tự cho ảnh lúc này.") from exc

    async def list(self, query: HistoryQuery) -> tuple[list[HistoryItem], int]:
        def _sync_list():
            q = self.client.table("prediction_logs").select("*", count="exact")
            if query.waste_type:
                q = q.eq("waste_type", query.waste_type)
            if query.pipeline_type:
                q = q.eq("pipeline_type", query.pipeline_type)
            if query.search:
                q = q.ilike("file_name", f"%{query.search}%")
            if query.start_date:
                q = q.gte("created_at", query.start_date.isoformat())
            if query.end_date:
                q = q.lte("created_at", query.end_date.isoformat())

            offset = (query.page - 1) * query.limit
            q = q.order("created_at", desc=True).range(offset, offset + query.limit - 1)
            res = q.execute()
            total = res.count or 0
            items = [HistoryItem.model_validate(row) for row in res.data]
            return items, total

        try:
            return await asyncio.to_thread(_sync_list)
        except Exception as exc:
            logger.warning("Supabase list failed: %s", exc)
            raise ApiError(503, "database_unavailable", "Không thể đọc lịch sử từ Supabase.") from exc

    async def get(self, id: UUID) -> HistoryItem | None:
        def _sync_get():
            res = self.client.table("prediction_logs").select("*").eq("id", str(id)).execute()
            if res.data:
                return HistoryItem.model_validate(res.data[0])
            return None

        try:
            return await asyncio.to_thread(_sync_get)
        except Exception as exc:
            logger.warning("Supabase get failed: %s", exc)
            raise ApiError(503, "database_unavailable", "Không thể lấy chi tiết bản ghi từ Supabase.") from exc

    async def statistics(self, start: datetime, end: datetime) -> HistoryStatistics:
        def _sync_statistics() -> HistoryStatistics:
            table = self.client.table("prediction_logs")

            def count(column: str | None = None, value: str | None = None) -> int:
                query = table.select("id", count="exact", head=True)
                query = query.gte("created_at", start.isoformat()).lte("created_at", end.isoformat())
                if column is not None:
                    query = query.eq(column, value)
                result = query.execute()
                if result.count is None:
                    raise RuntimeError("Supabase did not return the requested row count.")
                return result.count

            return HistoryStatistics(
                total=count(),
                by_waste_type={label: count("waste_type", label) for label in get_args(WasteType)},
                by_pipeline={label: count("pipeline_type", label) for label in get_args(PipelineType)},
            )

        try:
            return await asyncio.to_thread(_sync_statistics)
        except Exception as exc:
            logger.warning("Supabase history statistics failed: %s", exc)
            raise ApiError(503, "database_unavailable", "Không thể tải thống kê lịch sử. Vui lòng thử lại.") from exc

    async def trends(self, start: datetime, end: datetime, *, unit: Literal["hour", "day", "week"]) -> HistoryTrends:
        def _sync_trends() -> HistoryTrends:
            first_day, last_day = start.date(), end.date()
            step = 7 if unit == "week" else 1
            points = [
                HistoryTrendPoint(
                    start_date=first_day + timedelta(days=offset),
                    end_date=min(first_day + timedelta(days=offset + step - 1), last_day),
                )
                for offset in range(0, (last_day - first_day).days + 1, step)
            ]
            if unit == "hour":
                points = []
                for hour in range(24):
                    hour_start = start + timedelta(hours=hour)
                    hour_end = hour_start + timedelta(hours=1, microseconds=-1)
                    is_future = hour_start > end
                    if not is_future:
                        hour_end = min(hour_end, end)
                    points.append(HistoryTrendPoint(
                        start_date=first_day,
                        end_date=first_day,
                        start_at=hour_start,
                        end_at=hour_end,
                        is_future=is_future,
                    ))
            by_waste_type = dict.fromkeys(get_args(WasteType), 0)
            table = self.client.table("prediction_logs")
            cursor: tuple[str, str] | None = None

            while True:
                query = table.select("id,created_at,waste_type,pipeline_type")
                query = query.gte("created_at", start.isoformat()).lte("created_at", end.isoformat())
                if cursor:
                    created_at, id = cursor
                    query = query.or_(f"created_at.gt.{created_at},and(created_at.eq.{created_at},id.gt.{id})")
                rows = query.order("created_at").order("id").limit(500).execute().data
                if not rows:
                    break

                for row in rows:
                    local_time = datetime.fromisoformat(row["created_at"]).astimezone(start.tzinfo)
                    index = int((local_time - start).total_seconds() // 3600) if unit == "hour" else (
                        (local_time.date() - first_day).days // step
                    )
                    point = points[index]
                    point.total += 1
                    point.automatic += row["pipeline_type"] == "Tự động"
                    point.needs_review += row["pipeline_type"] == "Thủ công"
                    waste_type = row["waste_type"]
                    if waste_type in by_waste_type:
                        by_waste_type[waste_type] += 1
                cursor = (rows[-1]["created_at"], rows[-1]["id"])

            return HistoryTrends(unit=unit, points=points, by_waste_type=by_waste_type)

        try:
            return await asyncio.to_thread(_sync_trends)
        except Exception as exc:
            logger.warning("Supabase history trends failed: %s", exc)
            raise ApiError(503, "database_unavailable", "Không thể tải biểu đồ lịch sử. Vui lòng thử lại.") from exc

    async def export(self, query: HistoryFilters) -> AsyncIterator[HistoryItem]:
        def _sync_export():
            q = self.client.table("prediction_logs").select("*")
            if query.waste_type:
                q = q.eq("waste_type", query.waste_type)
            if query.pipeline_type:
                q = q.eq("pipeline_type", query.pipeline_type)
            if query.search:
                q = q.ilike("file_name", f"%{query.search}%")
            if query.start_date:
                q = q.gte("created_at", query.start_date.isoformat())
            if query.end_date:
                q = q.lte("created_at", query.end_date.isoformat())

            q = q.order("created_at", desc=True).limit(5000)
            return q.execute()

        try:
            res = await asyncio.to_thread(_sync_export)
            for row in res.data:
                yield HistoryItem.model_validate(row)
        except Exception as exc:
            logger.warning("Supabase export failed: %s", exc)
            raise ApiError(503, "database_unavailable", "Không thể xuất lịch sử từ Supabase.") from exc
