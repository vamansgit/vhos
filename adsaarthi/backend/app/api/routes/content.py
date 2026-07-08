from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand
from app.models.content import ContentDraft
from app.models.enums import ContentDraftStatus, ContentDraftType
from app.schemas.content import (
    AdCopyGenerateRequest,
    BlogGenerateRequest,
    ContentDraftOut,
    ContentDraftUpdate,
    ImageGenerateRequest,
)
from app.services.content_service import generate_ad_copy_drafts, generate_blog_draft, generate_image_draft

router = APIRouter(prefix="/api/content", tags=["content"])


@router.post("/blog", response_model=ContentDraftOut, status_code=status.HTTP_201_CREATED)
def create_blog(
    payload: BlogGenerateRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> ContentDraft:
    return generate_blog_draft(db, brand, payload.topic, payload.keywords)


@router.post("/ad-copy", response_model=list[ContentDraftOut], status_code=status.HTTP_201_CREATED)
def create_ad_copy(
    payload: AdCopyGenerateRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> list[ContentDraft]:
    return generate_ad_copy_drafts(db, brand, payload.product_or_offer, payload.platforms)


@router.post("/image", response_model=ContentDraftOut, status_code=status.HTTP_201_CREATED)
def create_image(
    payload: ImageGenerateRequest, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> ContentDraft:
    return generate_image_draft(db, brand, payload.prompt, payload.format)


@router.get("", response_model=list[ContentDraftOut])
def list_content(
    type: ContentDraftType | None = None,
    status_filter: ContentDraftStatus | None = None,
    brand: Brand = Depends(get_current_brand),
    db: Session = Depends(get_db),
) -> list[ContentDraft]:
    query = db.query(ContentDraft).filter(ContentDraft.brand_id == brand.id)
    if type is not None:
        query = query.filter(ContentDraft.type == type)
    if status_filter is not None:
        query = query.filter(ContentDraft.status == status_filter)
    return query.order_by(ContentDraft.created_at.desc()).all()


@router.get("/{draft_id}", response_model=ContentDraftOut)
def get_content(draft_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> ContentDraft:
    draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id, ContentDraft.brand_id == brand.id).first()
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content draft not found")
    return draft


@router.patch("/{draft_id}", response_model=ContentDraftOut)
def update_content(
    draft_id: str,
    payload: ContentDraftUpdate,
    brand: Brand = Depends(get_current_brand),
    db: Session = Depends(get_db),
) -> ContentDraft:
    draft = db.query(ContentDraft).filter(ContentDraft.id == draft_id, ContentDraft.brand_id == brand.id).first()
    if draft is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Content draft not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(draft, field, value)
    db.commit()
    db.refresh(draft)
    return draft
