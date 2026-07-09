from sqlalchemy import JSON, Enum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import ChatRole, ModuleName


class ChatMessage(UUIDPKMixin, TimestampMixin, Base):
    """PRD §10.1 — the unified conversational layer. Every user/assistant
    turn is persisted per brand so the orchestrator has session context and
    the interaction is auditable (PRD §11)."""

    __tablename__ = "chat_messages"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    role: Mapped[ChatRole] = mapped_column(Enum(ChatRole), nullable=False)
    module: Mapped[ModuleName] = mapped_column(Enum(ModuleName), default=ModuleName.NONE)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    structured_payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
