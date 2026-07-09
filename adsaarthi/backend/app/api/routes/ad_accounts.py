import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand, require_roles
from app.database import get_db
from app.models.ad_account import AdAccount
from app.models.brand import Brand
from app.models.enums import AdAccountStatus, UserRole
from app.schemas.ad_account import AdAccountConnectRequest, AdAccountOut
from app.services.analytics_service import sync_ad_account

router = APIRouter(prefix="/api/ad-accounts", tags=["ad-accounts"])


@router.get("", response_model=list[AdAccountOut])
def list_ad_accounts(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[AdAccount]:
    return db.query(AdAccount).filter(AdAccount.brand_id == brand.id).all()


@router.post("", response_model=AdAccountOut, status_code=status.HTTP_201_CREATED)
def connect_ad_account(
    payload: AdAccountConnectRequest,
    brand: Brand = Depends(get_current_brand),
    _user=Depends(require_roles(UserRole.OWNER, UserRole.MARKETER)),
    db: Session = Depends(get_db),
) -> AdAccount:
    """Connects a read-only ad account (PRD 7.1 onboarding). In production
    this would complete an OAuth2 authorization-code exchange; MVP accepts a
    display name directly and mock-connects it so the dashboard populates
    immediately without live platform credentials."""
    account = AdAccount(
        brand_id=brand.id,
        platform=payload.platform,
        display_name=payload.display_name,
        external_account_id=payload.external_account_id or f"mock-{uuid.uuid4().hex[:10]}",
        status=AdAccountStatus.CONNECTED,
        token_reference=None,
    )
    db.add(account)
    db.commit()
    db.refresh(account)

    sync_ad_account(db, account)
    db.refresh(account)
    return account


@router.post("/{account_id}/sync", response_model=AdAccountOut)
def resync_ad_account(
    account_id: str, brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)
) -> AdAccount:
    account = db.query(AdAccount).filter(AdAccount.id == account_id, AdAccount.brand_id == brand.id).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad account not found")
    sync_ad_account(db, account)
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_ad_account(
    account_id: str,
    brand: Brand = Depends(get_current_brand),
    _user=Depends(require_roles(UserRole.OWNER)),
    db: Session = Depends(get_db),
) -> None:
    account = db.query(AdAccount).filter(AdAccount.id == account_id, AdAccount.brand_id == brand.id).first()
    if account is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ad account not found")
    account.status = AdAccountStatus.DISCONNECTED
    db.commit()
