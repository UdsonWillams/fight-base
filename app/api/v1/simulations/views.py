"""Endpoints da API para simulação de lutas"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.api.v1.auth.dependencies import get_current_user
from app.database.models.schemas import User
from app.database.repositories.fight_simulation import FightSimulationRepository
from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.schemas.domain.simulations import (
    FightSimulationInput,
)
from app.services.domain.fight_simulation import FightSimulationService

router = APIRouter(prefix="/simulations", tags=["Fight Simulations"])


def get_simulation_service(
    uow: UnitOfWorkConnection = Depends(),
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
    current_user: User = Depends(get_current_user),
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
        created_by=current_user.email,
    )

    # Busca os nomes dos lutadores para retorno
    fighter1 = await service.fighter_repo.get_by_id(data.fighter1_id)
    fighter2 = await service.fighter_repo.get_by_id(data.fighter2_id)
    winner = fighter1 if simulation.winner_id == fighter1.id else fighter2

    return {
        "id": str(simulation.id),
        "fighter1_id": str(simulation.fighter1_id),
        "fighter2_id": str(simulation.fighter2_id),
        "fighter1_name": fighter1.name,
        "fighter2_name": fighter2.name,
        "winner_id": str(simulation.winner_id),
        "winner_name": winner.name,
        "result_type": simulation.result_type,
        "rounds": simulation.rounds,
        "finish_round": simulation.finish_round,
        "fighter1_probability": simulation.fighter1_probability,
        "fighter2_probability": simulation.fighter2_probability,
        "simulation_details": simulation.simulation_details,
        "notes": simulation.notes,
        "created_at": simulation.created_at.isoformat(),
    }


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
    # Busca histórico
    history = await service.simulation_repo.get_fighter_history(
        fighter_id=fighter_id, limit=limit, offset=offset
    )

    # Busca estatísticas
    stats = await service.simulation_repo.get_fighter_stats(fighter_id)

    # Busca info do lutador
    fighter = await service.fighter_repo.get_by_id(fighter_id)

    # Formata resposta
    fights = []
    for sim in history:
        f1 = await service.fighter_repo.get_by_id(sim.fighter1_id)
        f2 = await service.fighter_repo.get_by_id(sim.fighter2_id)
        winner = f1 if sim.winner_id == f1.id else f2

        fights.append(
            {
                "id": str(sim.id),
                "fighter1_name": f1.name,
                "fighter2_name": f2.name,
                "winner_name": winner.name,
                "result_type": sim.result_type,
                "rounds": sim.rounds,
                "finish_round": sim.finish_round,
                "created_at": sim.created_at.isoformat(),
            }
        )

    return {
        "fighter_id": str(fighter_id),
        "fighter_name": fighter.name,
        "statistics": stats,
        "recent_fights": fights,
        "pagination": {"limit": limit, "offset": offset, "total": len(fights)},
    }


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
    history = await service.simulation_repo.get_matchup_history(
        fighter1_id, fighter2_id
    )

    # Formata resposta
    results = []
    for sim in history:
        f1 = await service.fighter_repo.get_by_id(sim.fighter1_id)
        f2 = await service.fighter_repo.get_by_id(sim.fighter2_id)
        winner = f1 if sim.winner_id == f1.id else f2

        results.append(
            {
                "id": str(sim.id),
                "fighter1_name": f1.name,
                "fighter2_name": f2.name,
                "winner_name": winner.name,
                "result_type": sim.result_type,
                "rounds": sim.rounds,
                "finish_round": sim.finish_round,
                "fighter1_probability": sim.fighter1_probability,
                "fighter2_probability": sim.fighter2_probability,
                "created_at": sim.created_at.isoformat(),
            }
        )

    return results


@router.get("/recent", response_model=list[dict], summary="Simulações recentes")
async def get_recent_simulations(
    limit: int = Query(50, ge=1, le=100, description="Quantidade de simulações"),
    service: FightSimulationService = Depends(get_simulation_service),
):
    """
    Retorna as simulações mais recentes do sistema.

    Útil para ver a atividade recente e descobrir lutas interessantes.
    """
    simulations = await service.simulation_repo.get_recent_simulations(limit)

    results = []
    for sim in simulations:
        f1 = await service.fighter_repo.get_by_id(sim.fighter1_id)
        f2 = await service.fighter_repo.get_by_id(sim.fighter2_id)
        winner = f1 if sim.winner_id == f1.id else f2

        results.append(
            {
                "id": str(sim.id),
                "fighter1_name": f1.name,
                "fighter2_name": f2.name,
                "winner_name": winner.name,
                "result_type": sim.result_type,
                "rounds": sim.rounds,
                "finish_round": sim.finish_round,
                "created_at": sim.created_at.isoformat(),
            }
        )

    return results
