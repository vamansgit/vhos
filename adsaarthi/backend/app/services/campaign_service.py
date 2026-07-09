from sqlalchemy.orm import Session

from app.models.brand import Brand
from app.models.campaign import CampaignBrief, MatchResult
from app.models.enums import CampaignBriefStatus
from app.services.content_service import generate_creator_content_draft
from app.services.matching_engine import generate_shortlist, recommend_bids


def run_auto_match(db: Session, brand: Brand, brief: CampaignBrief) -> list[MatchResult]:
    """Executes PRD 6.2 Steps 2-4: rank shortlist, recommend bids, and
    auto-draft per-creator content — all landing in PENDING_REVIEW status
    for the mandatory human checkpoint before outreach or spend (PRD 6.2,
    11. Risks & Assumptions)."""
    brief.status = CampaignBriefStatus.MATCHING
    db.commit()

    db.query(MatchResult).filter(MatchResult.campaign_brief_id == brief.id).delete()
    db.commit()

    shortlist = generate_shortlist(db, brief)
    allocations = recommend_bids(shortlist, brief.total_budget)

    results: list[MatchResult] = []
    for rank, allocation in enumerate(allocations, start=1):
        match = allocation["match"]
        match_result = MatchResult(
            campaign_brief_id=brief.id,
            influencer_id=match.influencer.id,
            fit_score=match.fit_score,
            engagement_quality_score=match.engagement_quality_score,
            audience_overlap_score=match.audience_overlap_score,
            consistency_score=match.consistency_score,
            reason=match.reason,
            recommended_bid=allocation["recommended_bid"],
            projected_reach=allocation["projected_reach"],
            tier=match.tier,
            rank=rank,
        )
        db.add(match_result)
        db.flush()
        results.append(match_result)

    brief.status = CampaignBriefStatus.MATCHED if results else CampaignBriefStatus.DRAFT
    db.commit()
    for r in results:
        db.refresh(r)

    for match_result in results:
        generate_creator_content_draft(db, brand, match_result)

    return results
