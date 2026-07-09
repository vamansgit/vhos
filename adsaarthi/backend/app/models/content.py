from sqlalchemy import Date, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import ContentDraftStatus, ContentDraftType


class ContentDraft(UUIDPKMixin, TimestampMixin, Base):
    """AI Content Studio output (PRD 6.4) and per-creator drafts (PRD 6.2 Step 4).
    All drafts require human review before publish — see PRD 6.2 human checkpoint
    and 11. Risks & Assumptions (content quality / brand voice consistency).
    """

    __tablename__ = "content_drafts"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    match_result_id: Mapped[str | None] = mapped_column(ForeignKey("match_results.id"), nullable=True, index=True)

    type: Mapped[ContentDraftType] = mapped_column(Enum(ContentDraftType), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str | None] = mapped_column(String(300), nullable=True)
    platform_variant: Mapped[str | None] = mapped_column(String(50), nullable=True)  # instagram/youtube/google_search
    status: Mapped[ContentDraftStatus] = mapped_column(Enum(ContentDraftStatus), default=ContentDraftStatus.DRAFT)
    scheduled_date: Mapped[Date | None] = mapped_column(Date, nullable=True)
    generated_by: Mapped[str] = mapped_column(String(50), default="template")  # template | llm
