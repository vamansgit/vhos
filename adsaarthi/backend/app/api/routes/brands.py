from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_brand, require_roles
from app.database import get_db
from app.models.brand import Brand
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import InviteUserRequest, UserOut
from app.schemas.brand import BrandOut, BrandUpdate
from app.security import hash_password

router = APIRouter(prefix="/api/brands", tags=["brands"])


@router.get("/me", response_model=BrandOut)
def get_my_brand(brand: Brand = Depends(get_current_brand)) -> Brand:
    return brand


@router.patch("/me", response_model=BrandOut)
def update_my_brand(
    payload: BrandUpdate,
    brand: Brand = Depends(get_current_brand),
    _user: User = Depends(require_roles(UserRole.OWNER)),
    db: Session = Depends(get_db),
) -> Brand:
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(brand, field, value)
    db.commit()
    db.refresh(brand)
    return brand


@router.get("/me/users", response_model=list[UserOut])
def list_users(brand: Brand = Depends(get_current_brand), db: Session = Depends(get_db)) -> list[User]:
    return db.query(User).filter(User.brand_id == brand.id).all()


@router.post("/me/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def invite_user(
    payload: InviteUserRequest,
    brand: Brand = Depends(get_current_brand),
    _user: User = Depends(require_roles(UserRole.OWNER)),
    db: Session = Depends(get_db),
) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(
        brand_id=brand.id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
