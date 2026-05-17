from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.v1.auth.dependencies import get_current_user
from app.database.models.base import User
from app.database.repositories.league import LeagueRepository
from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.schemas.domain.predictions.input import (
    LeagueCreate,
    LeagueSelectEvent,
    LeaguePredictionsBulk,
    LeagueCreateFighter,
    LeagueUpgradeFighter,
)
from app.schemas.domain.predictions.output import (
    LeagueResponse,
    LeagueDetailResponse,
    LeagueLeaderboardEntry,
    LeaguePredictionResponse,
)
from app.services.domain.league import LeagueService

router = APIRouter(prefix="/leagues", tags=["Leagues"])


def get_league_service(uow: UnitOfWorkConnection = Depends(get_uow)) -> LeagueService:
    league_repo = LeagueRepository(uow)
    return LeagueService(uow, league_repo)


@router.post("/", response_model=LeagueResponse, status_code=status.HTTP_201_CREATED)
async def create_league(
    data: LeagueCreate,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Cria uma nova liga privada"""
    league = await service.create_league(
        current_user.id, data.name, data.description, data.is_public, data.max_members
    )
    return LeagueResponse.model_validate(league)


@router.post("/join/{invite_code}", response_model=LeagueResponse)
async def join_league(
    invite_code: str,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Entra em uma liga usando o código de convite"""
    try:
        league = await service.join_league(current_user.id, invite_code)
        return LeagueResponse.model_validate(league)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.get("/my", response_model=List[LeagueResponse])
async def get_my_leagues(
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Lista as ligas das quais o usuário participa"""
    leagues = await service.get_user_leagues(current_user.id)
    return [LeagueResponse.model_validate(league) for league in leagues]


@router.get("/{league_id}", response_model=LeagueDetailResponse)
async def get_league_detail(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Retorna detalhes completos da liga com evento ativo e leaderboard"""
    try:
        detail = await service.get_league_detail(league_id, current_user.id)
        return detail
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND, content={"message": str(e)}
        )


@router.delete("/{league_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Deleta a liga (apenas o dono)"""
    try:
        await service.delete_league(league_id, current_user.id)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.post("/{league_id}/select-event", response_model=LeagueResponse)
async def select_event(
    league_id: UUID,
    data: LeagueSelectEvent,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Seleciona o evento ativo da liga (apenas o dono)"""
    try:
        league = await service.select_event(league_id, data.event_id, current_user.id)
        members_count = len(league.members) if league.members else 0
        return {
            "id": str(league.id),
            "name": league.name,
            "description": league.description,
            "invite_code": league.invite_code,
            "owner_id": str(league.owner_id),
            "members_count": members_count,
            "active_event_id": str(league.active_event_id)
            if league.active_event_id
            else None,
            "active_event_name": league.active_event.name
            if league.active_event
            else None,
        }
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.get("/{league_id}/leaderboard", response_model=List[LeagueLeaderboardEntry])
async def get_leaderboard(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Ranking de membros da liga ordenado por pontos"""
    members = await service.get_league_leaderboard(league_id)
    entries = []
    for rank, m in enumerate(members, 1):
        entries.append(
            LeagueLeaderboardEntry(
                user_id=m.user_id,
                username=m.user.name if m.user else "",
                total_points=m.total_points,
                rank=rank,
            )
        )
    return entries


@router.post("/{league_id}/predictions", response_model=List[LeaguePredictionResponse])
async def create_predictions(
    league_id: UUID,
    data: LeaguePredictionsBulk,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Envia palpites para as lutas do evento ativo da liga"""
    try:
        predictions = await service.create_league_predictions(
            league_id, current_user.id, data.predictions
        )
        result = []
        for p in predictions:
            result.append(
                LeaguePredictionResponse(
                    id=p.id,
                    fight_id=p.fight_id,
                    predicted_winner_id=p.predicted_winner_id,
                    points_earned=p.points_earned or 0,
                )
            )
        return result
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.get(
    "/{league_id}/predictions/my", response_model=List[LeaguePredictionResponse]
)
async def get_my_predictions(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Retorna os palpites do usuário no evento ativo da liga"""
    try:
        predictions = await service.get_league_predictions(league_id, current_user.id)
        return predictions
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.post("/{league_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_league(
    league_id: UUID,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Sai da liga"""
    try:
        await service.leave_league(league_id, current_user.id)
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.post("/{league_id}/fighters")
async def create_league_fighter(
    league_id: UUID,
    data: LeagueCreateFighter,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Cria um lutador gastando pontos da liga"""
    try:
        result = await service.create_fighter_with_points(
            league_id, current_user.id, data
        )
        return result
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )


@router.post("/{league_id}/fighters/{fighter_id}/upgrade")
async def upgrade_league_fighter(
    league_id: UUID,
    fighter_id: UUID,
    data: LeagueUpgradeFighter,
    current_user: User = Depends(get_current_user),
    service: LeagueService = Depends(get_league_service),
):
    """Melhora atributos de um lutador gastando pontos da liga"""
    try:
        result = await service.upgrade_fighter_attributes(
            league_id, fighter_id, current_user.id, data.attribute, data.points_cost
        )
        return result
    except ValueError as e:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(e)}
        )
