"""Output schemas for events"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FighterSummary(BaseModel):
    """Resumo do lutador para exibição"""

    id: UUID
    name: str
    nickname: Optional[str] = None
    actual_weight_class: Optional[str] = None
    image_url: Optional[str] = None


class FightResponse(BaseModel):
    """Response schema para uma luta"""

    id: UUID
    event_id: UUID
    fighter1_id: UUID
    fighter2_id: UUID
    fighter1: Optional[FighterSummary] = None
    fighter2: Optional[FighterSummary] = None
    fight_order: int
    fight_type: str
    weight_class: Optional[str] = None
    rounds: int
    is_title_fight: bool
    status: str
    winner_id: Optional[UUID] = None
    winner: Optional[FighterSummary] = None
    result_type: Optional[str] = None
    finish_round: Optional[int] = None
    finish_time: Optional[str] = None
    method_details: Optional[str] = None
    fighter1_probability: Optional[float] = None
    fighter2_probability: Optional[float] = None
    simulation_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


class EventResponse(BaseModel):
    """Response schema para um evento"""

    id: UUID
    name: str
    date: datetime
    location: Optional[str] = None
    organization: str
    description: Optional[str] = None
    status: str
    poster_url: Optional[str] = None
    creator_id: UUID
    fights: List[FightResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    """Response schema para lista de eventos"""

    id: UUID
    name: str
    date: datetime
    location: Optional[str] = None
    organization: str
    status: str
    poster_url: Optional[str] = None
    fights_count: int = 0
    created_at: datetime


class SimulationResult(BaseModel):
    """Resultado da simulação de um evento"""

    event_id: UUID
    event_name: str
    simulated_fights: List[FightResponse]
    summary: Dict[str, Any] = Field(
        default_factory=dict, description="Resumo com estatísticas da simulação"
    )
