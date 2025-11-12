"""Schemas para simulação de lutas"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FightSimulationInput(BaseModel):
    """Schema para solicitar uma simulação de luta"""

    fighter1_id: UUID = Field(..., description="ID do primeiro lutador")
    fighter2_id: UUID = Field(..., description="ID do segundo lutador")
    rounds: int = Field(3, ge=1, le=5, description="Número de rounds (1-5)")
    notes: Optional[str] = Field(
        None, max_length=1000, description="Observações sobre a simulação"
    )


class SimulationRoundDetail(BaseModel):
    """Detalhes de um round da simulação"""

    round_number: int
    fighter1_points: int
    fighter2_points: int
    dominant_fighter: str
    events: list[str]  # Eventos importantes do round


class FightSimulationOutput(BaseModel):
    """Schema de saída para simulação de luta"""

    model_config = {"from_attributes": True}

    # IDs
    id: UUID
    fighter1_id: UUID
    fighter2_id: UUID

    # Nomes dos lutadores (para facilitar visualização)
    fighter1_name: str
    fighter2_name: str

    # Resultado
    winner_id: UUID
    winner_name: str
    result_type: str  # KO, Submission, Decision, Draw
    rounds: int
    finish_round: Optional[int] = None

    # Probabilidades
    fighter1_probability: float
    fighter2_probability: float

    # Detalhes
    simulation_details: Optional[dict] = None
    notes: Optional[str] = None


class FightPredictionOutput(BaseModel):
    """Schema para previsão de luta (sem executar simulação)"""

    fighter1_id: UUID
    fighter2_id: UUID
    fighter1_name: str
    fighter2_name: str

    # Probabilidades de vitória
    fighter1_win_probability: float
    fighter2_win_probability: float
    draw_probability: float

    # Probabilidades por tipo de resultado
    ko_probability: float
    submission_probability: float
    decision_probability: float

    # Análise de vantagens
    striking_advantage: str
    grappling_advantage: str
    overall_advantage: str

    # Análise textual
    analysis: str
    key_factors: list[str]


class FightHistoryOutput(BaseModel):
    """Histórico de lutas de um lutador"""

    fighter_id: UUID
    fighter_name: str
    total_simulations: int
    wins: int
    losses: int
    win_rate: float
    recent_fights: list[FightSimulationOutput]
