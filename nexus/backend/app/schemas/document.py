from datetime import date, datetime

from app.models.enums import DocumentStatus, DocumentType
from pydantic import BaseModel, ConfigDict


class DocumentVersionOut(BaseModel):
    id: str
    version_number: int
    file_ref: str
    note: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentOut(BaseModel):
    id: str
    type: DocumentType
    label: str
    status: DocumentStatus
    current_file_ref: str | None
    expiry_date: date | None
    extracted_value: str | None
    versions: list[DocumentVersionOut] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentUploadRequest(BaseModel):
    type: DocumentType
    label: str
    file_ref: str  # in production, a storage key from a signed-upload flow
    note: str | None = None
    expiry_date: date | None = None
    extracted_value: str | None = None
