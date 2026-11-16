from typing import Annotated

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
