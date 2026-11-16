import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from uuid import UUID

from supabase import create_client, Client

from app.core.errors import ApiError
from app.schemas.history import HistoryFilters, HistoryItem, HistoryQuery

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
