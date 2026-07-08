from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import AdAccountStatus, AdPlatform


class AdAccount(UUIDPKMixin, TimestampMixin, Base):
    """Represents a read-only OAuth connection to an external ad platform account.

    No credentials are ever stored here — only a token reference handle managed by
    the connector layer (see services/connectors), per PRD 8.3 compliance notes.
    """

    __tablename__ = "ad_accounts"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    platform: Mapped[AdPlatform] = mapped_column(Enum(AdPlatform), nullable=False)
    external_account_id: Mapped[str] = mapped_column(String(200), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[AdAccountStatus] = mapped_column(Enum(AdAccountStatus), default=AdAccountStatus.PENDING)
    token_reference: Mapped[str | None] = mapped_column(String(200), nullable=True)
    last_synced_at: Mapped[str | None] = mapped_column(String(50), nullable=True)

    brand: Mapped["Brand"] = relationship(back_populates="ad_accounts")
    metrics: Mapped[list["AdMetricDaily"]] = relationship(back_populates="ad_account", cascade="all, delete-orphan")
