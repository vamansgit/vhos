from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin


class Brand(UUIDPKMixin, TimestampMixin, Base):
    """A tenant workspace. All brand-scoped data isolates on brand_id."""

    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_audience: Mapped[str | None] = mapped_column(String(500), nullable=True)
    brand_voice: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    cac_alert_threshold_pct: Mapped[float] = mapped_column(Float, default=15.0)

    users: Mapped[list["User"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
    ad_accounts: Mapped[list["AdAccount"]] = relationship(back_populates="brand", cascade="all, delete-orphan")
