from datetime import date
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, Field, StringConstraints, model_validator

from .prediction import PipelineType, PredictionMetadata, PredictionResult, WasteType


class HistoryFilters(BaseModel):
    waste_type: WasteType | None = None
    pipeline_type: PipelineType | None = None
    search: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=150)] | None = None
    start_date: AwareDatetime | None = None
    end_date: AwareDatetime | None = None

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("start_date phải nhỏ hơn hoặc bằng end_date.")
        return self


class HistoryQuery(HistoryFilters):
    page: int = Field(default=1, ge=1, le=100_000)
    limit: int = Field(default=20, ge=1, le=100)


class HistoryItem(PredictionResult):
    metadata: PredictionMetadata


class HistoryPage(BaseModel):
    items: list[HistoryItem]
    total: int
    page: int
    limit: int
    total_pages: int


class HistoryStatisticsRange(BaseModel):
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def dates_in_order(self):
        if self.start_date > self.end_date:
            raise ValueError("Ngày bắt đầu phải trước hoặc trùng ngày kết thúc.")
        return self


class HistoryDailyQuery(HistoryStatisticsRange):
    page: int = Field(default=1, ge=1)


class HistoryStatistics(BaseModel):
    total: int
    by_waste_type: dict[WasteType, int]
    by_pipeline: dict[PipelineType, int]


HistoryTrendPeriod = Literal["today", "week", "month", "quarter"]


class HistoryTrendPoint(BaseModel):
    start_date: date
    end_date: date
    total: int = 0
    automatic: int = 0
    needs_review: int = 0
    start_at: AwareDatetime | None = None
    end_at: AwareDatetime | None = None
    is_future: bool = False


class HistoryTrends(BaseModel):
    unit: Literal["hour", "day", "week"]
    points: list[HistoryTrendPoint]
    by_waste_type: dict[WasteType, int]


class HistoryDailyPage(BaseModel):
    points: list[HistoryTrendPoint]
    page: int
    total_days: int
    total_pages: int
