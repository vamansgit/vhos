from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class BudgetRecommendation(UUIDPKMixin, TimestampMixin, Base):
    """Rules-based nudge from the Budget & Channel Optimizer (PRD 6.5)."""

    __tablename__ = "budget_recommendations"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    trend: Mapped[str] = mapped_column(String(20), nullable=False)  # improving | worsening | stable
    message: Mapped[str] = mapped_column(Text, nullable=False)
    suggested_paid_pct: Mapped[float] = mapped_column(default=60.0)
    suggested_influencer_pct: Mapped[float] = mapped_column(default=25.0)
    suggested_content_pct: Mapped[float] = mapped_column(default=15.0)


class CollaborationLog(UUIDPKMixin, TimestampMixin, Base):
    """Manually logged influencer collaborations that happened outside the
    platform (PRD 7.2), so their cost still flows into CAC tracking.
    """

    __tablename__ = "collaboration_logs"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    influencer_id: Mapped[str | None] = mapped_column(ForeignKey("influencers.id"), nullable=True)
    influencer_name: Mapped[str] = mapped_column(String(200), nullable=False)
    cost: Mapped[float] = mapped_column(nullable=False)
    conversions_attributed: Mapped[int] = mapped_column(default=0)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
