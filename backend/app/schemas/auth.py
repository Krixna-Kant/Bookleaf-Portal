from datetime import date

from pydantic import BaseModel, EmailStr, Field

from app.enums import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class UserOut(BaseModel):
    id: int
    email: str
    name: str
    role: UserRole
    external_author_id: str | None
    phone: str | None
    city: str | None
    joined_date: date | None

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
