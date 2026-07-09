from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand
from app.models.budget import BudgetRecommendation, CollaborationLog
from app.schemas.budget import BudgetRecommendationOut, CollaborationLogCreate, CollaborationLogOut
from app.services.budget_optimizer import generate_recommendation

router = APIRouter(prefix="/api/budget", tags=["budget"])


@router.get("/recommendation", response_model=BudgetRecommendationOut)
def get_recommendation(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> BudgetRecommendation:
    return generate_recommendation(db, brand)


@router.post("/collaborations", response_model=CollaborationLogOut, status_code=201)
def log_collaboration(
    payload: CollaborationLogCreate, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> CollaborationLog:
    """Manual off-platform collaboration logging so its cost flows into CAC
    tracking (PRD 7.2)."""
    log = CollaborationLog(brand_id=brand.id, **payload.model_dump())
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


@router.get("/collaborations", response_model=list[CollaborationLogOut])
def list_collaborations(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[CollaborationLog]:
    return db.query(CollaborationLog).filter(CollaborationLog.brand_id == brand.id).order_by(
        CollaborationLog.created_at.desc()
    ).all()
