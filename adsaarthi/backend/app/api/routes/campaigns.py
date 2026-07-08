from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand, require_roles
from app.database import get_db
from app.models.brand import Brand
from app.models.campaign import CampaignBrief, MatchResult
from app.models.enums import MatchStatus, UserRole
from app.models.user import User
from app.schemas.campaign import CampaignBriefCreate, CampaignBriefOut, MatchResultOut, MatchReviewRequest
from app.services.campaign_service import run_auto_match

router = APIRouter(prefix="/api/campaigns", tags=["campaigns"])


def _get_brief(db: Session, brand: Brand, brief_id: str) -> CampaignBrief:
    brief = db.query(CampaignBrief).filter(CampaignBrief.id == brief_id, CampaignBrief.brand_id == brand.id).first()
    if brief is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign brief not found")
    return brief


@router.post("", response_model=CampaignBriefOut, status_code=status.HTTP_201_CREATED)
def create_brief(
    payload: CampaignBriefCreate, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> CampaignBrief:
    """Step 1 — Campaign Intent Input (PRD 6.2)."""
    brief = CampaignBrief(brand_id=brand.id, **payload.model_dump())
    db.add(brief)
    db.commit()
    db.refresh(brief)
    return brief


@router.get("", response_model=list[CampaignBriefOut])
def list_briefs(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[CampaignBrief]:
    return (
        db.query(CampaignBrief)
        .filter(CampaignBrief.brand_id == brand.id)
        .order_by(CampaignBrief.created_at.desc())
        .all()
    )


@router.get("/{brief_id}", response_model=CampaignBriefOut)
def get_brief(brief_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> CampaignBrief:
    return _get_brief(db, brand, brief_id)


@router.post("/{brief_id}/match", response_model=list[MatchResultOut])
def match_creators(
    brief_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> list[MatchResult]:
    """Steps 2-4 — auto-match, bid recommendation, and per-creator content
    drafting, in one call. Results land in pending_review status."""
    brief = _get_brief(db, brand, brief_id)
    return run_auto_match(db, brand, brief)


@router.get("/{brief_id}/matches", response_model=list[MatchResultOut])
def list_matches(
    brief_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> list[MatchResult]:
    _get_brief(db, brand, brief_id)
    return (
        db.query(MatchResult)
        .filter(MatchResult.campaign_brief_id == brief_id)
        .order_by(MatchResult.rank)
        .all()
    )


@router.patch("/{brief_id}/matches/{match_id}", response_model=MatchResultOut)
def review_match(
    brief_id: str,
    match_id: str,
    payload: MatchReviewRequest,
    brand: Brand = Depends(get_current_brand),
    _user: User = Depends(require_roles(UserRole.OWNER, UserRole.MARKETER)),
    db: Session = Depends(get_db),
) -> MatchResult:
    """Human review checkpoint (PRD 6.2, default in MVP) — owner/marketer
    approves, adjusts the bid, or rejects a matched creator before any
    outreach or spend commitment."""
    _get_brief(db, brand, brief_id)
    match = db.query(MatchResult).filter(MatchResult.id == match_id, MatchResult.campaign_brief_id == brief_id).first()
    if match is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match result not found")

    match.status = payload.status
    if payload.status in (MatchStatus.APPROVED, MatchStatus.ADJUSTED):
        match.approved_bid = payload.approved_bid if payload.approved_bid is not None else match.recommended_bid
    db.commit()
    db.refresh(match)
    return match


@router.get("/{brief_id}/export", response_class=PlainTextResponse)
def export_brief(brief_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> str:
    """Brief-ready export for owners who build a shortlist manually or want
    to take an approved shortlist outside the platform (PRD 6.2, 7.2)."""
    brief = _get_brief(db, brand, brief_id)
    matches = (
        db.query(MatchResult)
        .filter(MatchResult.campaign_brief_id == brief_id)
        .order_by(MatchResult.rank)
        .all()
    )
    lines = [
        f"AdSaarthi Campaign Brief — {brand.name}",
        f"Objective: {brief.objective.value} | Format: {brief.content_format.value} | Budget: ₹{brief.total_budget:,.0f}",
        "",
        "Shortlisted Creators:",
    ]
    for m in matches:
        lines.append(
            f"- @{m.influencer.handle} ({m.tier}) — Fit {m.fit_score}/100, bid ₹{m.approved_bid or m.recommended_bid:,.0f}, "
            f"status={m.status.value}\n  {m.reason}"
        )
    return "\n".join(lines)
