from datetime import date

from sqlalchemy import Date, Enum, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import LedgerEntryType


class LedgerEntry(UUIDPKMixin, TimestampMixin, Base):
    """PRD §7.4 — single source of truth; materialized from SourcedOrder /
    Order / ad spend records, never a duplicate manual re-entry system."""

    __tablename__ = "ledger_entries"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    type: Mapped[LedgerEntryType] = mapped_column(Enum(LedgerEntryType), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)
    source_ref: Mapped[str | None] = mapped_column(String(100), nullable=True)  # e.g. "sourced_order:<id>"


class TaxProfile(UUIDPKMixin, TimestampMixin, Base):
    """PRD §7.4 — sourced from Onboard's Document/BrandProfile records, not
    re-entered by the user."""

    __tablename__ = "tax_profiles"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, unique=True)
    gstin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    applicable_schemes: Mapped[str | None] = mapped_column(String(300), nullable=True)
