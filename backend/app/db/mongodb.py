import logging
import re
from collections.abc import AsyncIterator
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
from pymongo.errors import PyMongoError

from app.core.errors import ApiError
from app.schemas.history import HistoryFilters, HistoryItem, HistoryQuery

logger = logging.getLogger(__name__)
NEWEST = [("created_at", DESCENDING), ("_id", DESCENDING)]


def _filter(query: HistoryFilters) -> dict:
    result = {}
    for key in ("waste_type", "pipeline_type"):
        if (value := getattr(query, key)) is not None:
            result[key] = value
    if query.search:
        result["file_name"] = {"$regex": re.escape(query.search), "$options": "i"}
    date_range = {}
    if query.start_date:
        date_range["$gte"] = query.start_date
    if query.end_date:
        date_range["$lte"] = query.end_date
    if date_range:
        result["created_at"] = date_range
    return result


def _unavailable(exc: PyMongoError) -> ApiError:
    logger.warning("MongoDB operation failed: %s", type(exc).__name__)
    return ApiError(503, "database_unavailable", "Không thể đọc hoặc ghi lịch sử vào lúc này.")


class MongoHistory:
    def __init__(self, uri: str, database: str) -> None:
        self.client = AsyncIOMotorClient(
            uri, appname="trash-classification-api", tz_aware=True,
            timeoutMS=6000, serverSelectionTimeoutMS=3500, maxPoolSize=15,
        )
        self.collection = self.client[database]["prediction_logs"]
        self.indexes_ready = False

    def close(self) -> None:
        self.client.close()

    async def check(self) -> None:
        await self.client.admin.command("ping")
        if not self.indexes_ready:
            await self.collection.create_indexes([
                IndexModel(NEWEST, name="newest"),
                IndexModel([("id", ASCENDING)], name="prediction_id", unique=True),
                IndexModel([("waste_type", ASCENDING), *NEWEST], name="waste_newest"),
                IndexModel([("pipeline_type", ASCENDING), *NEWEST], name="pipeline_newest"),
                IndexModel([("file_name", TEXT)], name="file_name_text", default_language="none"),
            ])
            self.indexes_ready = True

    async def insert(self, item: HistoryItem) -> None:
        document = item.model_dump(mode="python")
        document["id"] = document["_id"] = str(item.id)
        try:
            await self.collection.insert_one(document)
        except PyMongoError as exc:
            raise _unavailable(exc) from exc

    async def list(self, query: HistoryQuery) -> tuple[list[HistoryItem], int]:
        conditions = _filter(query)
        cursor = self.collection.find(conditions).sort(NEWEST).skip((query.page - 1) * query.limit).limit(query.limit)
        try:
            total = await self.collection.count_documents(conditions)
            documents = await cursor.to_list(length=query.limit)
            return [HistoryItem.model_validate(doc) for doc in documents], total
        except PyMongoError as exc:
            raise _unavailable(exc) from exc
        finally:
            await cursor.close()

    async def get(self, id: UUID) -> HistoryItem | None:
        try:
            doc = await self.collection.find_one({"id": str(id)})
            return HistoryItem.model_validate(doc) if doc else None
        except PyMongoError as exc:
            raise _unavailable(exc) from exc

    async def export(self, query: HistoryFilters) -> AsyncIterator[HistoryItem]:
        cursor = self.collection.find(_filter(query)).sort(NEWEST).batch_size(100)
        try:
            async for doc in cursor:
                yield HistoryItem.model_validate(doc)
        except PyMongoError as exc:
            raise _unavailable(exc) from exc
        finally:
            await cursor.close()
