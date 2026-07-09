from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand
from app.schemas.analytics import DashboardSummary
from app.services.analytics_service import get_dashboard_summary
from app.services.notifications import compose_weekly_digest

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardSummary)
def dashboard(days: int = 90, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> dict:
    return get_dashboard_summary(db, brand, days=days)


@router.get("/digest")
def weekly_digest(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> dict:
    summary = get_dashboard_summary(db, brand, days=7)
    return {"text": compose_weekly_digest(brand, summary)}
