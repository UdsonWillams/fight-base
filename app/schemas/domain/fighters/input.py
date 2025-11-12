"""Schemas de input para Fighters"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class FighterCreateInput(BaseModel):
    """Schema para criação de um lutador"""

    # Informações básicas
    name: str = Field(..., min_length=2, max_length=150, description="Nome do lutador")
    nickname: Optional[str] = Field(
        None, max_length=100, description="Apelido do lutador"
    )
    last_organization_fight: str = Field(
        ..., description="Última organização (UFC, Bellator, ONE, etc)"
    )
    actual_weight_class: str = Field(..., description="Categoria de peso atual")
    fighting_style: str = Field(..., description="Estilo de luta")

    # Atributos de luta (0-100)
    striking: int = Field(..., ge=0, le=100, description="Habilidade de striking")
    grappling: int = Field(..., ge=0, le=100, description="Habilidade de grappling")
    defense: int = Field(..., ge=0, le=100, description="Capacidade defensiva")
    stamina: int = Field(..., ge=0, le=100, description="Resistência/Cardio")
    speed: int = Field(..., ge=0, le=100, description="Velocidade")
    strategy: int = Field(..., ge=0, le=100, description="QI de luta")

    # Estatísticas (opcional)
    wins: Optional[int] = Field(0, ge=0, description="Vitórias")
    losses: Optional[int] = Field(0, ge=0, description="Derrotas")
    draws: Optional[int] = Field(0, ge=0, description="Empates")
    ko_wins: Optional[int] = Field(0, ge=0, description="Vitórias por nocaute")
    submission_wins: Optional[int] = Field(
        0, ge=0, description="Vitórias por finalização"
    )

    # Informações adicionais
    age: Optional[int] = Field(None, ge=18, le=60, description="Idade")
    height_cm: Optional[float] = Field(None, ge=150, le=230, description="Altura em cm")
    reach_cm: Optional[float] = Field(
        None, ge=150, le=250, description="Envergadura em cm"
    )
    bio: Optional[str] = Field(None, max_length=2000, description="Biografia")
    image_url: Optional[str] = Field(None, max_length=500, description="URL da imagem")
    is_real: bool = Field(True, description="Lutador real ou fictício")

    @field_validator("last_organization_fight")
    @classmethod
    def validate_organization(cls, v: str) -> str:
        valid_orgs = [
            "UFC",
            "Bellator",
            "ONE",
            "PFL",
            "Rizin",
            "Glory",
            "K-1",
            "Custom",
            "Other",
        ]
        if v not in valid_orgs:
            return "Other"
        return v


class FighterUpdateInput(BaseModel):
    """Schema para atualização de um lutador"""

    name: Optional[str] = Field(None, min_length=2, max_length=150)
    nickname: Optional[str] = Field(None, max_length=100)
    last_organization_fight: Optional[str] = None
    actual_weight_class: Optional[str] = None
    fighting_style: Optional[str] = None

    striking: Optional[int] = Field(None, ge=0, le=100)
    grappling: Optional[int] = Field(None, ge=0, le=100)
    defense: Optional[int] = Field(None, ge=0, le=100)
    stamina: Optional[int] = Field(None, ge=0, le=100)
    speed: Optional[int] = Field(None, ge=0, le=100)
    strategy: Optional[int] = Field(None, ge=0, le=100)

    wins: Optional[int] = Field(None, ge=0)
    losses: Optional[int] = Field(None, ge=0)
    draws: Optional[int] = Field(None, ge=0)
    ko_wins: Optional[int] = Field(None, ge=0)
    submission_wins: Optional[int] = Field(None, ge=0)

    age: Optional[int] = Field(None, ge=18, le=60)
    height_cm: Optional[float] = Field(None, ge=150, le=230)
    reach_cm: Optional[float] = Field(None, ge=150, le=250)
    bio: Optional[str] = Field(None, max_length=2000)
    image_url: Optional[str] = Field(None, max_length=500)
    is_real: Optional[bool] = None


class FighterSearchInput(BaseModel):
    """Schema para busca de lutadores"""

    name: Optional[str] = Field(None, description="Buscar por nome")
    last_organization_fight: Optional[str] = Field(
        None, description="Filtrar por última organização"
    )
    actual_weight_class: Optional[str] = Field(
        None, description="Filtrar por categoria atual"
    )
    fighting_style: Optional[str] = Field(None, description="Filtrar por estilo")
    is_real: Optional[bool] = Field(None, description="Filtrar por real/fictício")
    min_overall: Optional[int] = Field(
        None, ge=0, le=100, description="Nota mínima geral"
    )
    limit: int = Field(10, ge=1, le=100, description="Limite de resultados")
    offset: int = Field(0, ge=0, description="Offset para paginação")
