from app.models.enums import AdPlatform, InfluencerCategory
from pydantic import ConfigDict, BaseModel


class InfluencerOut(BaseModel):
    id: str
    handle: str
    display_name: str
    platform: AdPlatform
    category: InfluencerCategory
    follower_count: int
    engagement_rate_pct: float
    posting_consistency_score: float
    audience_age_range: str | None
    audience_geography: str | None
    audience_interests: str | None
    indicative_price_min: float
    indicative_price_max: float
    top_content_style: str | None
    historical_avg_engagement_pct: float
    historical_campaigns_count: int

    model_config = ConfigDict(from_attributes=True)


class InfluencerFilter(BaseModel):
    category: InfluencerCategory | None = None
    platform: AdPlatform | None = None
    min_followers: int | None = None
    max_followers: int | None = None
    min_engagement_pct: float | None = None
    max_price: float | None = None
