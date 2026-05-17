from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


class RoleEnum(str, Enum):
    admin = "admin"
    user = "user"


class UserBase(BaseModel):
    email: EmailStr


class UserLogin(UserBase):
    password: str


class AuthenticatedUser(UserBase):
    id: UUID
    name: str = ""
    is_active: bool = True
    role: RoleEnum = RoleEnum.user
    provider: str = "local"
    google_id: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    """Request para iniciar autenticação Google"""

    redirect_uri: Optional[str] = None


class GoogleCallbackRequest(BaseModel):
    """Callback do Google com código de autorização"""

    code: str
    state: Optional[str] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: Optional[str] = None


__all__ = [
    "UserBase",
    "UserLogin",
    "Token",
    "TokenData",
    "RoleEnum",
    "AuthenticatedUser",
    "GoogleAuthRequest",
    "GoogleCallbackRequest",
]
