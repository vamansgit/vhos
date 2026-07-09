from pydantic import ConfigDict, BaseModel, Field


class BudgetRecommendationOut(BaseModel):
    id: str
    trend: str
    message: str
    suggested_paid_pct: float
    suggested_influencer_pct: float
    suggested_content_pct: float

    model_config = ConfigDict(from_attributes=True)


class CollaborationLogCreate(BaseModel):
    influencer_id: str | None = None
    influencer_name: str
    cost: float = Field(gt=0)
    conversions_attributed: int = 0
    notes: str | None = None


class CollaborationLogOut(BaseModel):
    id: str
    influencer_name: str
    cost: float
    conversions_attributed: int
    notes: str | None

    model_config = ConfigDict(from_attributes=True)
