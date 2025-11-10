from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel

from app.schemas.domain.fighters.output import FighterOutput


class UserResponse(BaseModel):
    """Schema de resposta para usuário."""

    id: UUID
    name: str
    email: str
    fighters: List[FighterOutput] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CreateUserResponse(BaseModel):
    """Schema de resposta para criação de usuário."""

    id: UUID
    name: str
    email: str

    class Config:
        from_attributes = True


class UserList(BaseModel):
    """Schema de lista de usuários."""

    items: List[UserResponse]
    count: int
