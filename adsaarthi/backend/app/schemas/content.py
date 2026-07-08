from datetime import date, datetime

from app.models.enums import ContentDraftStatus, ContentDraftType
from pydantic import ConfigDict, BaseModel


class BlogGenerateRequest(BaseModel):
    topic: str
    keywords: list[str] = []


class AdCopyGenerateRequest(BaseModel):
    product_or_offer: str
    platforms: list[str] = ["instagram", "youtube", "google_search"]


class ImageGenerateRequest(BaseModel):
    prompt: str
    format: str = "instagram_post"  # instagram_post | banner | story


class ContentDraftOut(BaseModel):
    id: str
    brand_id: str
    match_result_id: str | None
    type: ContentDraftType
    title: str
    body: str
    topic: str | None
    platform_variant: str | None
    status: ContentDraftStatus
    scheduled_date: date | None
    generated_by: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ContentDraftUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    status: ContentDraftStatus | None = None
    scheduled_date: date | None = None
