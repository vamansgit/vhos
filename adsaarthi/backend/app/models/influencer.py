from sqlalchemy import Enum, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import AdPlatform, InfluencerCategory


class Influencer(UUIDPKMixin, TimestampMixin, Base):
    """Directory entry sourced from official platform APIs / partner feeds
    (PRD 6.2, 8.3). Not brand-scoped — shared across the platform.
    """

    __tablename__ = "influencers"

    handle: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    platform: Mapped[AdPlatform] = mapped_column(Enum(AdPlatform), nullable=False)
    category: Mapped[InfluencerCategory] = mapped_column(Enum(InfluencerCategory), nullable=False, index=True)

    follower_count: Mapped[int] = mapped_column(Integer, default=0)
    engagement_rate_pct: Mapped[float] = mapped_column(Float, default=0.0)
    posting_consistency_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100
    audience_age_range: Mapped[str | None] = mapped_column(String(50), nullable=True)
    audience_geography: Mapped[str | None] = mapped_column(String(200), nullable=True)
    audience_interests: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma-separated tags

    indicative_price_min: Mapped[float] = mapped_column(Float, default=0.0)
    indicative_price_max: Mapped[float] = mapped_column(Float, default=0.0)

    top_content_style: Mapped[str | None] = mapped_column(String(500), nullable=True)
    historical_avg_engagement_pct: Mapped[float] = mapped_column(Float, default=0.0)
    historical_campaigns_count: Mapped[int] = mapped_column(Integer, default=0)

    opted_in: Mapped[bool] = mapped_column(default=False)  # Phase 2 self-serve profile opt-in
