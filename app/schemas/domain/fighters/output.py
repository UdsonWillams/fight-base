"""Schemas de output para Fighters"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, computed_field


class FighterOutput(BaseModel):
    """Schema de saída para um lutador"""

    model_config = {"from_attributes": True}

    # IDs e metadados
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: str

    # Informações básicas
    name: str
    nickname: Optional[str] = None
    last_organization_fight: Optional[str] = None
    actual_weight_class: Optional[str] = None
    fighting_style: Optional[str] = None

    # Atributos de luta
    striking: int
    grappling: int
    defense: int
    stamina: int
    speed: int
    strategy: int

    # Estatísticas
    wins: Optional[int] = 0
    losses: Optional[int] = 0
    draws: Optional[int] = 0
    ko_wins: Optional[int] = 0
    submission_wins: Optional[int] = 0

    # Informações adicionais
    age: Optional[int] = None
    height_cm: Optional[float] = None
    reach_cm: Optional[float] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    is_real: bool
    creator_id: UUID

    @computed_field
    @property
    def overall_rating(self) -> float:
        """Calcula a nota geral do lutador (média dos atributos)"""
        return round(
            (
                self.striking
                + self.grappling
                + self.defense
                + self.stamina
                + self.speed
                + self.strategy
            )
            / 6,
            1,
        )

    @computed_field
    @property
    def record(self) -> str:
        """Retorna o cartel no formato W-L-D"""
        return f"{self.wins}-{self.losses}-{self.draws}"

    @computed_field
    @property
    def finish_rate(self) -> float:
        """Taxa de finalização (KO + Submission / Total Wins)"""
        if self.wins == 0:
            return 0.0
        total_finishes = (self.ko_wins or 0) + (self.submission_wins or 0)
        return round((total_finishes / self.wins) * 100, 1)


class FighterListOutput(BaseModel):
    """Schema para lista de lutadores com paginação"""

    fighters: list[FighterOutput]
    total: int
    limit: int
    offset: int


class FighterComparisonOutput(BaseModel):
    """Schema para comparação entre dois lutadores"""

    fighter1: FighterOutput
    fighter2: FighterOutput

    # Comparação de atributos
    striking_advantage: str  # Nome do lutador com vantagem
    grappling_advantage: str
    defense_advantage: str
    stamina_advantage: str
    speed_advantage: str
    strategy_advantage: str

    # Diferenças
    striking_diff: int
    grappling_diff: int
    defense_diff: int
    stamina_diff: int
    speed_diff: int
    strategy_diff: int

    overall_advantage: str
    overall_diff: float


class FighterStatsOutput(BaseModel):
    """Estatísticas agregadas de lutadores"""

    total_fighters: int
    total_real: int
    total_fictional: int
    last_organizations: dict[str, int]  # Mudou de organizations para last_organizations
    weight_classes: dict[str, int]  # Mantém o nome, mas vem de actual_weight_class
    avg_overall_rating: float
