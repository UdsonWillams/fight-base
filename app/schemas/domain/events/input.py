"""Input schemas for events"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class CreateFight(BaseModel):
    """Schema para criar uma luta"""

    fighter1_id: UUID = Field(..., description="ID do primeiro lutador")
    fighter2_id: UUID = Field(..., description="ID do segundo lutador")
    fight_order: int = Field(..., description="Ordem da luta no card (1=main event)")
    fight_type: str = Field(
        default="standard", description="Tipo da luta (main, co-main, prelim, standard)"
    )
    weight_class: Optional[str] = Field(None, description="Categoria de peso")
    rounds: int = Field(default=3, description="Número de rounds (3 ou 5)")
    is_title_fight: bool = Field(default=False, description="Se é luta de cinturão")

    @field_validator("fighter1_id", "fighter2_id")
    @classmethod
    def validate_fighter_ids(cls, v, info):
        """Valida que os IDs dos lutadores são válidos"""
        if v is None:
            raise ValueError("Fighter ID cannot be None")
        return v

    @field_validator("rounds")
    @classmethod
    def validate_rounds(cls, v):
        """Valida número de rounds"""
        if v not in [3, 5]:
            raise ValueError("Rounds must be 3 or 5")
        return v

    @field_validator("fight_type")
    @classmethod
    def validate_fight_type(cls, v):
        """Valida tipo de luta"""
        valid_types = ["main", "co-main", "prelim", "standard"]
        if v not in valid_types:
            raise ValueError(f"Fight type must be one of: {', '.join(valid_types)}")
        return v


class CreateEvent(BaseModel):
    """Schema para criar um evento"""

    name: str = Field(..., min_length=3, max_length=255, description="Nome do evento")
    date: datetime = Field(..., description="Data do evento")
    location: Optional[str] = Field(None, max_length=255, description="Local do evento")
    organization: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Organização (UFC, Bellator, etc)",
    )
    description: Optional[str] = Field(None, description="Descrição do evento")
    poster_url: Optional[str] = Field(None, max_length=500, description="URL do poster")
    fights: List[CreateFight] = Field(
        default_factory=list, description="Lista de lutas do evento"
    )

    @field_validator("fights")
    @classmethod
    def validate_fights(cls, v):
        """Valida lista de lutas"""
        if len(v) == 0:
            raise ValueError("Event must have at least one fight")

        # Verifica fight_order duplicado
        fight_orders = [fight.fight_order for fight in v]
        if len(fight_orders) != len(set(fight_orders)):
            raise ValueError("Fight orders must be unique")

        # Verifica se lutadores não lutam contra si mesmos
        for fight in v:
            if fight.fighter1_id == fight.fighter2_id:
                raise ValueError("A fighter cannot fight against themselves")

        return v


class AddFightToEvent(BaseModel):
    """Schema para adicionar uma luta a um evento existente"""

    fighter1_id: UUID
    fighter2_id: UUID
    fight_order: int
    fight_type: str = "standard"
    weight_class: Optional[str] = None
    rounds: int = 3
    is_title_fight: bool = False
