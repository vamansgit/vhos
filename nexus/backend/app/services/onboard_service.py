"""Onboard module services (PRD §4) — brand/founder intake, document vault,
and the guided checklist that seeds every other module's defaults."""

from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.checklist import OnboardingChecklistItem
from app.models.document import Document, DocumentVersion
from app.models.enums import (
    BusinessStructure,
    ChecklistItemStatus,
    DocumentStatus,
    DocumentType,
)

_EXPIRY_WARNING_DAYS = 30

# Baseline checklist every pre-launch founder needs, regardless of category.
_BASE_CHECKLIST: list[tuple[str, str]] = [
    ("Decide a business structure", "Proprietorship is fastest to start; LLP/Pvt Ltd add liability protection."),
    ("Register for GST", "Required once turnover crosses the threshold, or immediately if selling cross-state."),
    ("Open a current bank account", "Needed before payment gateway KYC can be completed."),
]

_CATEGORY_CHECKLIST: dict[str, list[tuple[str, str]]] = {
    "food": [("Get FSSAI registration", "Mandatory for any food business before you can legally sell.")],
    "cosmetics": [("Get BIS/Cosmetics registration", "Required for cosmetics and personal-care products sold in India.")],
    "beauty": [("Get BIS/Cosmetics registration", "Required for cosmetics and personal-care products sold in India.")],
    "electronics": [("Check BIS certification requirements", "Many electronics categories require mandatory BIS certification.")],
}


def seed_checklist_for_brand(db: Session, brand: Brand) -> list[OnboardingChecklistItem]:
    """Generates a starter checklist tailored to the brand's category and
    incorporation status (PRD §4.2D). Idempotent — skips if already seeded."""
    existing = db.query(OnboardingChecklistItem).filter(OnboardingChecklistItem.brand_id == brand.id).count()
    if existing:
        return db.query(OnboardingChecklistItem).filter(OnboardingChecklistItem.brand_id == brand.id).all()

    items: list[tuple[str, str]] = []
    if brand.structure == BusinessStructure.NOT_INCORPORATED:
        items.extend(_BASE_CHECKLIST)
    else:
        items.extend(_BASE_CHECKLIST[1:])  # already incorporated, skip that step

    if brand.category:
        items.extend(_CATEGORY_CHECKLIST.get(brand.category.lower(), []))

    created = []
    for requirement, due_context in items:
        item = OnboardingChecklistItem(brand_id=brand.id, requirement=requirement, due_context=due_context)
        db.add(item)
        created.append(item)
    db.commit()
    for item in created:
        db.refresh(item)
    return created


def compute_document_status(expiry_date: date | None, has_file: bool) -> DocumentStatus:
    if not has_file:
        return DocumentStatus.MISSING
    if expiry_date is None:
        return DocumentStatus.UPLOADED
    today = date.today()
    if expiry_date < today:
        return DocumentStatus.EXPIRED
    if expiry_date <= today + timedelta(days=_EXPIRY_WARNING_DAYS):
        return DocumentStatus.EXPIRING_SOON
    return DocumentStatus.UPLOADED


def upsert_document(
    db: Session,
    brand: Brand,
    doc_type: DocumentType,
    label: str,
    file_ref: str,
    note: str | None,
    expiry_date: date | None,
    extracted_value: str | None,
) -> Document:
    """Adds a new version to an existing document of this type, or creates
    one — the vault's add/update/replace/version model (PRD §4.2C)."""
    document = db.query(Document).filter(Document.brand_id == brand.id, Document.type == doc_type).first()
    if document is None:
        document = Document(brand_id=brand.id, type=doc_type, label=label)
        db.add(document)
        db.flush()

    next_version = len(document.versions) + 1
    db.add(DocumentVersion(document_id=document.id, version_number=next_version, file_ref=file_ref, note=note))

    document.label = label
    document.current_file_ref = file_ref
    document.expiry_date = expiry_date
    document.extracted_value = extracted_value
    document.status = compute_document_status(expiry_date, has_file=True)

    db.commit()
    db.refresh(document)
    return document
