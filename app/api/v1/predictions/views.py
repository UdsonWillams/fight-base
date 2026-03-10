from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse

from app.api.v1.auth.dependencies import get_current_user
from app.database.models.base import User
from app.database.repositories.prediction import PredictionRepository
from app.database.repositories.achievement import AchievementRepository
from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.schemas.domain.predictions.input import CreatePrediction
from app.schemas.domain.predictions.output import (
    PredictionResponse,
    LeaderboardEntry,
    UserStatsResponse,
    FinishMethodResponse,
    AchievementResponse,
)
from app.services.domain.prediction import PredictionService

router = APIRouter(prefix="/predictions", tags=["Predictions"])


def get_prediction_service(
    uow: UnitOfWorkConnection = Depends(get_uow),
) -> PredictionService:
    prediction_repo = PredictionRepository(uow)
    achievement_repo = AchievementRepository(uow)
    return PredictionService(uow, prediction_repo, achievement_repo)


@router.post(
    "/", response_model=PredictionResponse, status_code=status.HTTP_201_CREATED
)
async def create_prediction(
    data: CreatePrediction,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    """Cria um palpite para uma luta"""
    try:
        prediction = await service.create_prediction(current_user.id, data)
        return PredictionResponse.model_validate(prediction)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.get("/my/event/{event_id}", response_model=List[PredictionResponse])
async def get_my_predictions_for_event(
    event_id: UUID,
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    """Retorna os palpites do usuário para um evento específico"""
    predictions = await service.prediction_repo.get_user_predictions_for_event(
        current_user.id, event_id
    )
    return [PredictionResponse.model_validate(p) for p in predictions]


@router.get("/leaderboard/event/{event_id}", response_model=List[LeaderboardEntry])
async def get_event_leaderboard(
    event_id: UUID,
    limit: int = Query(50, ge=1, le=100),
    service: PredictionService = Depends(get_prediction_service),
):
    """Retorna o ranking de usuários para um evento"""
    # Aqui precisaríamos de um join com User para pegar o username
    # Simplificando no repository ou service
    await service.prediction_repo.get_event_leaderboard(event_id, limit)
    # Mapping logic needed here for usernames
    return []  # Placeholder - will implement full mapping in service/repo if needed


@router.get("/my/stats", response_model=UserStatsResponse)
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    """Retorna as estatísticas históricas do usuário"""
    stats = await service.prediction_repo.get_user_stats(current_user.id)
    if not stats:
        return UserStatsResponse(
            total_points=0,
            total_predictions=0,
            correct_winners=0,
            underdog_bonus_points=0,
            current_streak=0,
            best_streak=0,
            events_participated=0,
        )
    return UserStatsResponse.model_validate(stats)


@router.get("/finish-methods", response_model=List[FinishMethodResponse])
async def get_finish_methods(
    service: PredictionService = Depends(get_prediction_service),
):
    """Lista todos os métodos de finalização disponíveis para palpites"""
    methods = await service.prediction_repo.get_finish_methods()
    return [FinishMethodResponse.model_validate(m) for m in methods]


@router.get("/my/achievements", response_model=List[AchievementResponse])
async def get_my_achievements(
    current_user: User = Depends(get_current_user),
    service: PredictionService = Depends(get_prediction_service),
):
    """Lista os achievements desbloqueados pelo usuário"""
    achievements = await service.achievement_repo.get_unlocked_achievements(
        current_user.id
    )
    return [AchievementResponse.model_validate(a) for a in achievements]
