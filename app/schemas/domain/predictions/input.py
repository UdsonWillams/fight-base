from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, conint


class PredictionInput(BaseModel):
    fight_id: UUID
    event_id: UUID
    predicted_winner_id: Optional[UUID] = None  # None for Draw
    predicted_method_id: Optional[UUID] = None
    predicted_round: Optional[conint(ge=1, le=5)] = None


class CreatePrediction(PredictionInput):
    pass


class UpdatePrediction(BaseModel):
    predicted_winner_id: Optional[UUID] = None
    predicted_method_id: Optional[UUID] = None
    predicted_round: Optional[conint(ge=1, le=5)] = None


class LeagueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: bool = False
    max_members: int = Field(default=50, ge=2)


class UpdateFightResult(BaseModel):
    winner_id: Optional[UUID] = None  # None if DRAW or NC
    method_id: UUID
    finish_round: Optional[int] = None
    finish_time: Optional[str] = None
    method_details: Optional[str] = None


class LeagueSelectEvent(BaseModel):
    """Schema para o owner da liga selecionar o evento ativo."""

    event_id: UUID


class LeaguePrediction(BaseModel):
    """Schema para palpitar em uma luta dentro da liga."""

    fight_id: UUID
    predicted_winner_id: Optional[UUID] = None


class LeaguePredictionsBulk(BaseModel):
    """Schema para enviar múltiplos palpites de uma vez."""

    predictions: list[LeaguePrediction]


class LeagueCreateFighter(BaseModel):
    """Schema para criar lutador gastando pontos da liga."""

    name: str = Field(..., min_length=1, max_length=150)
    nickname: Optional[str] = None
    actual_weight_class: Optional[str] = None
    fighting_style: Optional[str] = None
    stance: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    reach: Optional[float] = None
    organization: str = "League"
    gender: Optional[str] = None
    points_cost: int = Field(default=0, ge=0)


class LeagueUpgradeFighter(BaseModel):
    """Schema para melhorar atributos de um lutador gastando pontos da liga."""

    attribute: str = Field(
        ...,
        description="Atributo a aumentar: striking, grappling, defense, stamina, speed, strategy",
    )
    points_cost: int = Field(
        default=0, ge=0, description="Pontos a gastar (cada ponto = +1 no atributo)"
    )

    @field_validator("attribute")
    @classmethod
    def validate_attribute(cls, v: str) -> str:
        valid = {"striking", "grappling", "defense", "stamina", "speed", "strategy"}
        if v not in valid:
            raise ValueError(f"attribute must be one of: {', '.join(valid)}")
        return v
