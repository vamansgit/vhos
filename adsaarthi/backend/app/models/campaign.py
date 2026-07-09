from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import CampaignBriefStatus, CampaignObjective, ContentFormat, MatchStatus


class CampaignBrief(UUIDPKMixin, TimestampMixin, Base):
    """Step 1 — Campaign Intent Input (PRD 6.2)."""

    __tablename__ = "campaign_briefs"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    objective: Mapped[CampaignObjective] = mapped_column(Enum(CampaignObjective), nullable=False)
    target_audience_age: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_audience_gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    target_audience_geography: Mapped[str | None] = mapped_column(String(200), nullable=True)
    target_audience_interests: Mapped[str | None] = mapped_column(String(500), nullable=True)
    desired_reach: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content_format: Mapped[ContentFormat] = mapped_column(Enum(ContentFormat), nullable=False)
    total_budget: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[CampaignBriefStatus] = mapped_column(Enum(CampaignBriefStatus), default=CampaignBriefStatus.DRAFT)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    match_results: Mapped[list["MatchResult"]] = relationship(
        back_populates="campaign_brief", cascade="all, delete-orphan"
    )


class MatchResult(UUIDPKMixin, TimestampMixin, Base):
    """Step 2/3 output — ranked creator shortlist + recommended bid (PRD 6.2)."""

    __tablename__ = "match_results"

    campaign_brief_id: Mapped[str] = mapped_column(ForeignKey("campaign_briefs.id"), nullable=False, index=True)
    influencer_id: Mapped[str] = mapped_column(ForeignKey("influencers.id"), nullable=False, index=True)

    fit_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100 composite
    engagement_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    audience_overlap_score: Mapped[float] = mapped_column(Float, default=0.0)
    consistency_score: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    recommended_bid: Mapped[float] = mapped_column(Float, nullable=False)
    projected_reach: Mapped[int] = mapped_column(Integer, default=0)
    tier: Mapped[str] = mapped_column(String(20), default="micro")  # macro | micro

    status: Mapped[MatchStatus] = mapped_column(Enum(MatchStatus), default=MatchStatus.PENDING_REVIEW)
    approved_bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    rank: Mapped[int] = mapped_column(Integer, default=0)

    campaign_brief: Mapped["CampaignBrief"] = relationship(back_populates="match_results")
    influencer: Mapped["Influencer"] = relationship()
