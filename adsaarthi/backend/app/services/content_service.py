from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.campaign import MatchResult
from app.models.content import ContentDraft
from app.models.enums import ContentDraftType
from app.services.content_generation import get_content_provider


def generate_blog_draft(db: Session, brand: Brand, topic: str, keywords: list[str]) -> ContentDraft:
    provider = get_content_provider()
    result = provider.generate_blog(topic, keywords, brand.brand_voice)
    draft = ContentDraft(
        brand_id=brand.id,
        type=ContentDraftType.BLOG,
        title=result["title"],
        body=result["body"],
        topic=topic,
        generated_by=provider.name,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def generate_ad_copy_drafts(db: Session, brand: Brand, product_or_offer: str, platforms: list[str]) -> list[ContentDraft]:
    provider = get_content_provider()
    drafts = []
    for platform in platforms:
        result = provider.generate_ad_copy(product_or_offer, platform, brand.brand_voice)
        draft = ContentDraft(
            brand_id=brand.id,
            type=ContentDraftType.AD_COPY,
            title=result["title"],
            body=result["body"],
            topic=product_or_offer,
            platform_variant=platform,
            generated_by=provider.name,
        )
        db.add(draft)
        drafts.append(draft)
    db.commit()
    for d in drafts:
        db.refresh(d)
    return drafts


def generate_image_draft(db: Session, brand: Brand, prompt: str, image_format: str) -> ContentDraft:
    provider = get_content_provider()
    result = provider.generate_image_concept(prompt, image_format, brand.name)
    draft = ContentDraft(
        brand_id=brand.id,
        type=ContentDraftType.IMAGE,
        title=result["title"],
        body=result["body"],
        topic=prompt,
        platform_variant=image_format,
        generated_by=provider.name,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft


def generate_creator_content_draft(db: Session, brand: Brand, match_result: MatchResult) -> ContentDraft:
    """PRD 6.2 Step 4 — automatic, creator-specific content drafting, routed
    into the same Content Studio review flow as blogs/ad copy."""
    provider = get_content_provider()
    influencer = match_result.influencer
    result = provider.generate_creator_brief(
        brand_name=brand.name,
        brand_voice=brand.brand_voice,
        campaign_objective=match_result.campaign_brief.objective.value,
        influencer_handle=influencer.handle,
        influencer_style=influencer.top_content_style,
        content_format=match_result.campaign_brief.content_format.value,
    )
    draft = ContentDraft(
        brand_id=brand.id,
        match_result_id=match_result.id,
        type=ContentDraftType.CREATOR_BRIEF,
        title=result["title"],
        body=result["body"],
        topic=f"@{influencer.handle}",
        generated_by=provider.name,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return draft
