from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import ChecklistItemStatus


class OnboardingChecklistItem(UUIDPKMixin, TimestampMixin, Base):
    """PRD §4.2D — a conversational checklist for pre-launch founders,
    surfaced one guided step at a time rather than a legal document dump."""

    __tablename__ = "onboarding_checklist_items"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    requirement: Mapped[str] = mapped_column(String(300), nullable=False)
    due_context: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status: Mapped[ChecklistItemStatus] = mapped_column(
        Enum(ChecklistItemStatus), default=ChecklistItemStatus.NOT_STARTED
    )
