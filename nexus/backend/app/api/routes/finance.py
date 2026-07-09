from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand
from app.database import get_db
from app.models.brand import Brand
from app.schemas.finance import FinanceDashboard, TaxProfileOut
from app.services.finance_service import get_dashboard_summary, sync_ledger, sync_tax_profile

router = APIRouter(prefix="/api/finance", tags=["finance"])


@router.get("/dashboard", response_model=FinanceDashboard)
def dashboard(days: int = 90, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> dict:
    """PRD §7.2A — real-time P&L, materialized from Source/Sell records on
    every request rather than a monthly close cycle."""
    sync_ledger(db, brand.id)
    return get_dashboard_summary(db, brand.id, days=days)


@router.get("/tax-profile", response_model=TaxProfileOut)
def tax_profile(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)):
    return sync_tax_profile(db, brand)
