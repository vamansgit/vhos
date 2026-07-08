from app.models.enums import CampaignBriefStatus, CampaignObjective, ContentFormat, MatchStatus
from app.schemas.influencer import InfluencerOut
from pydantic import ConfigDict, BaseModel, Field


class CampaignBriefCreate(BaseModel):
    objective: CampaignObjective
    target_audience_age: str | None = None
    target_audience_gender: str | None = None
    target_audience_geography: str | None = None
    target_audience_interests: str | None = None
    desired_reach: int | None = None
    content_format: ContentFormat
    total_budget: float = Field(gt=0)
    notes: str | None = None


class CampaignBriefOut(BaseModel):
    id: str
    brand_id: str
    objective: CampaignObjective
    target_audience_age: str | None
    target_audience_gender: str | None
    target_audience_geography: str | None
    target_audience_interests: str | None
    desired_reach: int | None
    content_format: ContentFormat
    total_budget: float
    status: CampaignBriefStatus
    notes: str | None

    model_config = ConfigDict(from_attributes=True)


class MatchResultOut(BaseModel):
    id: str
    campaign_brief_id: str
    influencer: InfluencerOut
    fit_score: float
    engagement_quality_score: float
    audience_overlap_score: float
    consistency_score: float
    reason: str
    recommended_bid: float
    projected_reach: int
    tier: str
    status: MatchStatus
    approved_bid: float | None
    rank: int

    model_config = ConfigDict(from_attributes=True)


class MatchReviewRequest(BaseModel):
    status: MatchStatus
    approved_bid: float | None = None
