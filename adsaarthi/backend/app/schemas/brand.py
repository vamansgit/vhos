from pydantic import ConfigDict, BaseModel, Field


class BrandOut(BaseModel):
    id: str
    name: str
    category: str | None
    target_audience: str | None
    brand_voice: str | None
    cac_alert_threshold_pct: float

    model_config = ConfigDict(from_attributes=True)


class BrandUpdate(BaseModel):
    category: str | None = None
    target_audience: str | None = None
    brand_voice: str | None = None
    cac_alert_threshold_pct: float | None = Field(default=None, ge=0, le=100)
