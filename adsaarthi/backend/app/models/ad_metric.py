from datetime import date as date_type

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import UUIDPKMixin


class AdMetricDaily(UUIDPKMixin, Base):
    """Normalized daily ad performance row — the common schema all platform
    connectors ETL into (PRD 8.2 Data Flow). One row per ad_account/campaign/date.
    """

    __tablename__ = "ad_metrics_daily"

    ad_account_id: Mapped[str] = mapped_column(ForeignKey("ad_accounts.id"), nullable=False, index=True)
    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    date: Mapped[date_type] = mapped_column(Date, nullable=False, index=True)
    campaign_name: Mapped[str] = mapped_column(String(200), nullable=False)

    spend: Mapped[float] = mapped_column(Float, default=0.0)
    impressions: Mapped[int] = mapped_column(Integer, default=0)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    conversions: Mapped[int] = mapped_column(Integer, default=0)
    revenue: Mapped[float] = mapped_column(Float, default=0.0)

    ad_account: Mapped["AdAccount"] = relationship(back_populates="metrics")

    @property
    def cac(self) -> float | None:
        if self.conversions <= 0:
            return None
        return round(self.spend / self.conversions, 2)

    @property
    def roas(self) -> float | None:
        if self.spend <= 0:
            return None
        return round(self.revenue / self.spend, 2)
