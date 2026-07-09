from datetime import date

from sqlalchemy import Date, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin, UUIDPKMixin
from app.models.enums import DocumentStatus, DocumentType


class Document(UUIDPKMixin, TimestampMixin, Base):
    """The Onboard document vault (PRD §4.2C) — the authoritative source
    Finance & Compliance reads from; no duplicate uploads across modules."""

    __tablename__ = "documents"

    brand_id: Mapped[str] = mapped_column(ForeignKey("brands.id"), nullable=False, index=True)
    type: Mapped[DocumentType] = mapped_column(Enum(DocumentType), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    status: Mapped[DocumentStatus] = mapped_column(Enum(DocumentStatus), default=DocumentStatus.MISSING)
    current_file_ref: Mapped[str | None] = mapped_column(String(500), nullable=True)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Free-text extracted values relevant to compliance, e.g. GSTIN for a GST doc.
    extracted_value: Mapped[str | None] = mapped_column(String(200), nullable=True)

    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", cascade="all, delete-orphan", order_by="DocumentVersion.version_number"
    )


class DocumentVersion(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "document_versions"

    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_ref: Mapped[str] = mapped_column(String(500), nullable=False)
    note: Mapped[str | None] = mapped_column(String(300), nullable=True)

    document: Mapped["Document"] = relationship(back_populates="versions")
