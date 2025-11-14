"""Endpoints da API para simulação de lutas"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.database.repositories.fight_simulation import FightSimulationRepository
from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.schemas.domain.simulations import FightSimulationInput
from app.services.domain.fight_simulation import FightSimulationService

router = APIRouter(prefix="/simulations", tags=["Fight Simulations"])


def get_simulation_service(
    uow: UnitOfWorkConnection = Depends(get_uow),
) -> FightSimulationService:
    """Dependency injection para FightSimulationService"""
    fighter_repo = FighterRepository(uow)
    simulation_repo = FightSimulationRepository(uow)
    return FightSimulationService(fighter_repo, simulation_repo)


@router.post(
    "/",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Simular uma luta",
)
async def simulate_fight(
    data: FightSimulationInput,
    # current_user: User = Depends(get_current_user),
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Executa uma simulação completa de luta entre dois lutadores.

    - **fighter1_id**: ID do primeiro lutador
    - **fighter2_id**: ID do segundo lutador
    - **rounds**: Número de rounds (1-5, padrão 3)
    - **notes**: Observações sobre a simulação (opcional)

    Retorna o resultado completo com vencedor, tipo de vitória, probabilidades e detalhes round a round.
    """
    simulation = await service.simulate_fight(
        fighter1_id=data.fighter1_id,
        fighter2_id=data.fighter2_id,
        rounds=data.rounds,
        notes=data.notes,
        created_by="testeer",  # current_user.email,
    )

    return await service.get_simulation_with_details(simulation)


@router.get("/predict", response_model=dict, summary="Prever resultado de luta")
async def predict_fight(
    fighter1_id: UUID = Query(..., description="ID do primeiro lutador"),
    fighter2_id: UUID = Query(..., description="ID do segundo lutador"),
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Faz uma previsão de luta sem executar a simulação.

    Retorna probabilidades de vitória, análise de vantagens e fatores-chave.
    Útil para ver quem seria o favorito antes de simular.
    """
    prediction = await service.predict_fight(fighter1_id, fighter2_id)
    return prediction


@router.get("/compare", response_model=dict, summary="Comparar dois lutadores")
async def compare_fighters(
    fighter1_id: UUID = Query(..., description="ID do primeiro lutador"),
    fighter2_id: UUID = Query(..., description="ID do segundo lutador"),
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Compara detalhadamente dois lutadores.

    Retorna comparação de cada atributo (striking, grappling, defense, etc)
    mostrando vantagens e diferenças.
    """
    comparison = await service.compare_fighters(fighter1_id, fighter2_id)
    return comparison


@router.get(
    "/history/{fighter_id}",
    response_model=dict,
    summary="Histórico de simulações de um lutador",
)
async def get_fighter_simulation_history(
    fighter_id: UUID,
    limit: int = Query(20, ge=1, le=100, description="Quantidade de lutas"),
    offset: int = Query(0, ge=0, description="Offset para paginação"),
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Retorna o histórico de simulações de um lutador específico.

    Mostra todas as lutas simuladas, vitórias, derrotas e estatísticas.
    """
    return await service.get_fighter_history(fighter_id, limit, offset)


@router.get(
    "/matchup",
    response_model=list[dict],
    summary="Histórico de confrontos entre dois lutadores",
)
async def get_matchup_history(
    fighter1_id: UUID = Query(..., description="ID do primeiro lutador"),
    fighter2_id: UUID = Query(..., description="ID do segundo lutador"),
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Retorna o histórico de confrontos diretos entre dois lutadores específicos.

    Útil para ver quantas vezes eles já se enfrentaram em simulações
    e qual lutador tem vantagem no head-to-head.
    """
    return await service.get_matchup_history_formatted(fighter1_id, fighter2_id)


@router.get("/recent", response_model=list[dict], summary="Simulações recentes")
async def get_recent_simulations(
    limit: int = Query(50, ge=1, le=100, description="Quantidade de simulações"),
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Retorna as simulações mais recentes do sistema.

    Útil para ver a atividade recente e descobrir lutas interessantes.
    """
    return await service.get_recent_simulations_formatted(limit)


@router.get(
    "/statistics/overview",
    response_model=dict,
    summary="Estatísticas gerais de simulações",
)
async def get_simulation_statistics(
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Retorna estatísticas agregadas sobre simulações.

    - Total de simulações realizadas
    """
    return await service.get_simulation_stats()
