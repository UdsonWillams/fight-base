from typing import List

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse

from app.api.v1.auth.dependencies import get_current_user
from app.database.models.base import User
from app.database.repositories.league import LeagueRepository
from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.schemas.domain.predictions.input import LeagueCreate
from app.schemas.domain.predictions.output import LeagueResponse
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
    # Precisamos de um schema que suporte count de membros
    return LeagueResponse(
        id=league.id,
        name=league.name,
        description=league.description,
        invite_code=league.invite_code,
        owner_id=league.owner_id,
        members_count=1,
    )


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
