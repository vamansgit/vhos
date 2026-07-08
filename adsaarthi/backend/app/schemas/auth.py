from pydantic import ConfigDict, BaseModel, EmailStr, Field

from app.models.enums import UserRole


class SignupRequest(BaseModel):
    brand_name: str = Field(min_length=2, max_length=200)
    category: str | None = None
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class InviteUserRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str = Field(min_length=8, max_length=100)
    role: UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(BaseModel):
    id: str
    brand_id: str
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
