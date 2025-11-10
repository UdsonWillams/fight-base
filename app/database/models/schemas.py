"""
Schemas baseados nas tabelas do banco de dados utilizando o Pydantic

A ideia é poder utilizar do valores que a ORM do sqlalchemy nos trás com
as funções auxiliadoras do Pydantic.
Ex.: model_dump, model_dump_json
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel as PydanticBase
from pydantic import ConfigDict


class BaseModel(PydanticBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_by: str | None = None
    created_at: datetime
    updated_by: str | None = None
    updated_at: datetime | None = None
    deleted_by: str | None = None
    deleted_at: datetime | None = None


class User(BaseModel):
    """Schema Pydantic para usuários do sistema"""

    name: str
    email: str
    password: str
    role: str
    is_active: bool


class Product(BaseModel):
    id: UUID
    external_id: str
    title: str
    price: float
    description: Optional[str] = None
    category: Optional[str] = None
    image: Optional[str] = None
    review: Optional[float] = None


# FightBase Models
class Fighter(BaseModel):
    """Schema Pydantic para lutadores"""

    name: str
    nickname: Optional[str] = None
    organization: str
    weight_class: str
    fighting_style: str
    striking: int
    grappling: int
    defense: int
    stamina: int
    speed: int
    strategy: int
    wins: Optional[int] = 0
    losses: Optional[int] = 0
    draws: Optional[int] = 0
    ko_wins: Optional[int] = 0
    submission_wins: Optional[int] = 0
    age: Optional[int] = None
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    is_real: bool
    creator_id: UUID


class FightSimulation(BaseModel):
    """Schema Pydantic para simulações de lutas"""

    fighter1_id: UUID
    fighter2_id: UUID
    winner_id: UUID
    result_type: str
    rounds: int
    finish_round: Optional[int] = None
    fighter1_probability: float
    fighter2_probability: float
    simulation_details: Optional[dict] = None
    notes: Optional[str] = None
