"""Endpoints da API para gerenciamento de lutadores"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.api.v1.auth.dependencies import get_current_user
from app.database.models.schemas import User
from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.schemas.domain.fighters.input import (
    FighterCreateInput,
    FighterSearchInput,
    FighterUpdateInput,
)
from app.schemas.domain.fighters.output import (
    FighterListOutput,
    FighterOutput,
    FighterStatsOutput,
)
from app.services.domain.fighter import FighterService

router = APIRouter(prefix="/fighters", tags=["Fighters"])


def get_fighter_service(uow: UnitOfWorkConnection = Depends()) -> FighterService:
    """Dependency injection para FighterService"""
    fighter_repo = FighterRepository(uow)
    return FighterService(fighter_repo)


@router.post(
    "/",
    response_model=FighterOutput,
    status_code=status.HTTP_201_CREATED,
    summary="Criar novo lutador",
)
async def create_fighter(
    data: FighterCreateInput,
    current_user: User = Depends(get_current_user),
    service: FighterService = Depends(get_fighter_service),
):
    """
    Cria um novo lutador no sistema.

    - **name**: Nome do lutador (obrigatório)
    - **organization**: UFC, Bellator, ONE, etc
    - **weight_class**: Categoria de peso
    - **fighting_style**: Estilo de luta
    - **striking, grappling, defense, stamina, speed, strategy**: Atributos 0-100
    """
    fighter = await service.create_fighter(
        data=data, creator_id=current_user.id, created_by=current_user.email
    )
    return FighterOutput.model_validate(fighter)


@router.get(
    "/{fighter_id}", response_model=FighterOutput, summary="Buscar lutador por ID"
)
async def get_fighter(
    fighter_id: UUID, service: FighterService = Depends(get_fighter_service)
):
    """Retorna os detalhes de um lutador específico"""
    fighter = await service.get_fighter(fighter_id)
    return FighterOutput.model_validate(fighter)


@router.put("/{fighter_id}", response_model=FighterOutput, summary="Atualizar lutador")
async def update_fighter(
    fighter_id: UUID,
    data: FighterUpdateInput,
    current_user: User = Depends(get_current_user),
    service: FighterService = Depends(get_fighter_service),
):
    """Atualiza os dados de um lutador existente"""
    fighter = await service.update_fighter(
        fighter_id=fighter_id, data=data, updated_by=current_user.email
    )
    return FighterOutput.model_validate(fighter)


@router.delete(
    "/{fighter_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Remover lutador"
)
async def delete_fighter(
    fighter_id: UUID,
    current_user: User = Depends(get_current_user),
    service: FighterService = Depends(get_fighter_service),
):
    """Remove um lutador do sistema (soft delete)"""
    await service.delete_fighter(fighter_id, deleted_by=current_user.email)
    return JSONResponse(
        status_code=status.HTTP_204_NO_CONTENT,
        content={"message": "Fighter deleted successfully"},
    )


@router.get("/", response_model=FighterListOutput, summary="Buscar lutadores")
async def search_fighters(
    name: str = Query(None, description="Buscar por nome"),
    organization: str = Query(None, description="Filtrar por organização"),
    weight_class: str = Query(None, description="Filtrar por categoria"),
    fighting_style: str = Query(None, description="Filtrar por estilo"),
    is_real: bool = Query(None, description="Filtrar por real/fictício"),
    min_overall: int = Query(None, ge=0, le=100, description="Rating mínimo"),
    limit: int = Query(10, ge=1, le=100, description="Limite de resultados"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    service: FighterService = Depends(get_fighter_service),
):
    """
    Busca lutadores com diversos filtros.

    Retorna uma lista paginada de lutadores que correspondem aos critérios.
    """
    search_params = FighterSearchInput(
        name=name,
        organization=organization,
        weight_class=weight_class,
        fighting_style=fighting_style,
        is_real=is_real,
        min_overall=min_overall,
        limit=limit,
        offset=offset,
    )

    fighters = await service.search_fighters(search_params)

    # Para simplificar, vamos contar apenas os resultados retornados
    # Em produção, você faria uma query separada para o total
    total = len(fighters)

    return FighterListOutput(
        fighters=[FighterOutput.model_validate(f) for f in fighters],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/rankings/top", response_model=list[FighterOutput], summary="Top lutadores"
)
async def get_top_fighters(
    organization: str = Query(None, description="Filtrar por organização"),
    weight_class: str = Query(None, description="Filtrar por categoria"),
    limit: int = Query(10, ge=1, le=50, description="Quantidade de lutadores"),
    service: FighterService = Depends(get_fighter_service),
):
    """
    Retorna os melhores lutadores ranqueados por overall rating.

    Pode filtrar por organização e/ou categoria de peso.
    """
    fighters = await service.get_top_fighters(
        organization=organization, weight_class=weight_class, limit=limit
    )

    return [FighterOutput.model_validate(f) for f in fighters]


@router.get(
    "/statistics/overview",
    response_model=FighterStatsOutput,
    summary="Estatísticas gerais",
)
async def get_fighter_statistics(
    service: FighterService = Depends(get_fighter_service),
):
    """
    Retorna estatísticas agregadas sobre todos os lutadores do sistema.

    - Total de lutadores
    - Lutadores reais vs fictícios
    - Distribuição por organização
    - Distribuição por categoria de peso
    - Média geral de rating
    """
    stats = await service.get_fighter_stats()
    return FighterStatsOutput(**stats)


@router.get(
    "/my/fighters", response_model=list[FighterOutput], summary="Meus lutadores"
)
async def get_my_fighters(
    current_user: User = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    service: FighterService = Depends(get_fighter_service),
):
    """Retorna os lutadores criados pelo usuário atual"""
    fighters = await service.get_fighters_by_creator(
        creator_id=current_user.id, limit=limit, offset=offset
    )

    return [FighterOutput.model_validate(f) for f in fighters]
