from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand, FounderProfile
from app.models.checklist import OnboardingChecklistItem
from app.models.document import Document
from app.schemas.brand import BrandOut, BrandUpdate, FounderProfileOut, FounderProfileUpdate
from app.schemas.checklist import ChecklistItemOut, ChecklistItemUpdate
from app.schemas.document import DocumentOut, DocumentUploadRequest
from app.services.onboard_service import seed_checklist_for_brand, upsert_document

router = APIRouter(prefix="/api/onboard", tags=["onboard"])


@router.get("/brand", response_model=BrandOut)
def get_brand(brand: Brand = Depends(get_current_brand)) -> Brand:
    return brand


@router.patch("/brand", response_model=BrandOut)
def update_brand(payload: BrandUpdate, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> Brand:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand, field, value)
    db.commit()
    db.refresh(brand)
    return brand


@router.get("/founder", response_model=FounderProfileOut)
def get_founder_profile(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> FounderProfile:
    profile = db.query(FounderProfile).filter(FounderProfile.brand_id == brand.id).first()
    if profile is None:
        profile = FounderProfile(brand_id=brand.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.patch("/founder", response_model=FounderProfileOut)
def update_founder_profile(
    payload: FounderProfileUpdate, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> FounderProfile:
    profile = db.query(FounderProfile).filter(FounderProfile.brand_id == brand.id).first()
    if profile is None:
        profile = FounderProfile(brand_id=brand.id)
        db.add(profile)
        db.flush()
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/documents", response_model=list[DocumentOut])
def list_documents(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[Document]:
    return db.query(Document).filter(Document.brand_id == brand.id).all()


@router.post("/documents", response_model=DocumentOut, status_code=status.HTTP_201_CREATED)
def upload_document(
    payload: DocumentUploadRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> Document:
    """Add/update/replace/version a vault document in one call (PRD §4.2C) —
    re-uploading an existing document type creates a new version rather
    than a duplicate record."""
    return upsert_document(
        db,
        brand,
        doc_type=payload.type,
        label=payload.label,
        file_ref=payload.file_ref,
        note=payload.note,
        expiry_date=payload.expiry_date,
        extracted_value=payload.extracted_value,
    )


@router.get("/checklist", response_model=list[ChecklistItemOut])
def get_checklist(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[OnboardingChecklistItem]:
    return seed_checklist_for_brand(db, brand)


@router.patch("/checklist/{item_id}", response_model=ChecklistItemOut)
def update_checklist_item(
    item_id: str, payload: ChecklistItemUpdate, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> OnboardingChecklistItem:
    item = (
        db.query(OnboardingChecklistItem)
        .filter(OnboardingChecklistItem.id == item_id, OnboardingChecklistItem.brand_id == brand.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Checklist item not found")
    item.status = payload.status
    db.commit()
    db.refresh(item)
    return item
