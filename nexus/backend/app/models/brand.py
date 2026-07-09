from sqlalchemy import Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import BrandStage, BusinessStructure


class Brand(UUIDPKMixin, TimestampMixin, Base):
    """The tenant. Doubles as the `BrandProfile` entity from PRD §4.4 — all
    other module data is brand-scoped and reads/writes into the shared
    Brand Context (PRD §10.2)."""

    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    stage: Mapped[BrandStage] = mapped_column(Enum(BrandStage), default=BrandStage.IDEA)
    structure: Mapped[BusinessStructure] = mapped_column(
        Enum(BusinessStructure), default=BusinessStructure.NOT_INCORPORATED
    )
    target_geographies: Mapped[str | None] = mapped_column(String(300), nullable=True)  # comma-separated
    style_descriptors: Mapped[str | None] = mapped_column(String(300), nullable=True)  # e.g. "minimal, earthy"
    team_size: Mapped[int] = mapped_column(Integer, default=1)

    founder_profile: Mapped["FounderProfile | None"] = relationship(
        back_populates="brand", uselist=False, cascade="all, delete-orphan"
    )


class FounderProfile(UUIDPKMixin, TimestampMixin, Base):
    """PRD §4.4 — captured conversationally, drives personalized suggestions
    across every other module."""

    __tablename__ = "founder_profiles"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, unique=True)
    background_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[str | None] = mapped_column(String(500), nullable=True)  # comma-separated
    aspirations_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_appetite: Mapped[str | None] = mapped_column(String(50), nullable=True)  # low/medium/high
    time_availability_hours_per_week: Mapped[int | None] = mapped_column(Integer, nullable=True)

    brand: Mapped["Brand"] = relationship(back_populates="founder_profile")
