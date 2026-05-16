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
