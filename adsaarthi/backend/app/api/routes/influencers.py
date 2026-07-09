from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.enums import AdPlatform, InfluencerCategory
from app.models.influencer import Influencer
from app.schemas.influencer import InfluencerOut

router = APIRouter(prefix="/api/influencers", tags=["influencers"])


@router.get("", response_model=list[InfluencerOut])
def list_influencers(
    category: InfluencerCategory | None = None,
    platform: AdPlatform | None = None,
    min_followers: int | None = None,
    max_followers: int | None = None,
    min_engagement_pct: float | None = None,
    max_price: float | None = None,
    db: Session = Depends(get_db),
    _brand=Depends(get_current_brand),
) -> list[Influencer]:
    """Manual search/filter over the full directory (PRD 6.2 — always
    available alongside the auto-match flow)."""
    query = db.query(Influencer)
    if category is not None:
        query = query.filter(Influencer.category == category)
    if platform is not None:
        query = query.filter(Influencer.platform == platform)
    if min_followers is not None:
        query = query.filter(Influencer.follower_count >= min_followers)
    if max_followers is not None:
        query = query.filter(Influencer.follower_count <= max_followers)
    if min_engagement_pct is not None:
        query = query.filter(Influencer.engagement_rate_pct >= min_engagement_pct)
    if max_price is not None:
        query = query.filter(Influencer.indicative_price_max <= max_price)
    return query.order_by(Influencer.engagement_rate_pct.desc()).limit(200).all()


@router.get("/compare", response_model=list[InfluencerOut])
def compare_influencers(
    ids: list[str] = Query(..., min_length=1, max_length=6),
    db: Session = Depends(get_db),
    _brand=Depends(get_current_brand),
) -> list[Influencer]:
    return db.query(Influencer).filter(Influencer.id.in_(ids)).all()


@router.get("/{influencer_id}", response_model=InfluencerOut)
def get_influencer(
    influencer_id: str, db: Session = Depends(get_db), _brand=Depends(get_current_brand)
) -> Influencer:
    influencer = db.get(Influencer, influencer_id)
    if influencer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Influencer not found")
    return influencer
