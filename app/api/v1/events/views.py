"""API endpoints for Events"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks

from app.api.v1.auth.dependencies import get_current_user
from app.api.v1.predictions.views import get_prediction_service
from app.core.logger import logger
from app.database.repositories.fight_simulation import FightSimulationRepository
from app.database.repositories.fighter import FighterRepository
from app.database.repositories.event import EventRepository
from app.database.repositories.fight import FightRepository
from app.database.unit_of_work import UnitOfWorkConnection, get_uow
from app.schemas.auth import AuthenticatedUser
from app.schemas.domain.events.input import AddFightToEvent, CreateEvent
from app.schemas.domain.events.output import (
    EventListResponse,
    EventResponse,
    SimulationResult,
    FightResponse,
)
from app.schemas.domain.predictions.input import UpdateFightResult
from app.services.domain.event import EventService
from app.services.domain.fight_simulation import FightSimulationService
from app.services.domain.prediction import PredictionService


router = APIRouter(prefix="/events", tags=["events"])


def get_event_service(
    uow: UnitOfWorkConnection = Depends(get_uow),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EventService:
    """
    Dependency para obter o EventService com injeção de dependências.

    Cria FightSimulationService e injeta no EventService.
    """
    fighter_repo = FighterRepository(uow)
    simulation_repo = FightSimulationRepository(uow)

    simulation_service = FightSimulationService(
        fighter_repo=fighter_repo,
        simulation_repo=simulation_repo,
    )

    event_repo = EventRepository(uow)
    fight_repo = FightRepository(uow)

    return EventService(
        uow=uow,
        simulation_service=simulation_service,
        event_repo=event_repo,
        fight_repo=fight_repo,
        fighter_repo=fighter_repo,
        user_email=current_user.email,
    )


@router.put(
    "/{event_id}/fights/{fight_id}/result",
    response_model=FightResponse,
    summary="Update real fight result (Admin)",
)
async def update_fight_result(
    event_id: UUID,
    fight_id: UUID,
    payload: UpdateFightResult,
    background_tasks: BackgroundTasks,
    # current_user: AuthenticatedUser = Depends(require_admin), # Placeholder for admin check
    service: EventService = Depends(get_event_service),
    prediction_service: PredictionService = Depends(get_prediction_service),
):
    """
    Admin define o resultado real de uma luta.
    Dispara background task para processar os palpites dos usuários.
    """
    try:
        updated_fight = await service.update_fight_result(fight_id, payload)

        # Disparar background task para processar palpites
        background_tasks.add_task(prediction_service.process_fight_results, fight_id)

        # Converter para response mantendo a consistência da API
        return await service._fight_to_response(updated_fight)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post(
    "/",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new event",
)
async def create_event(
    payload: CreateEvent,
    current_user: AuthenticatedUser = Depends(get_current_user),
    service: EventService = Depends(get_event_service),
):
    """
    Cria um novo evento de MMA com suas lutas.

    - **name**: Nome do evento (ex: "UFC 233")
    - **date**: Data do evento
    - **organization**: Organização (UFC, Bellator, etc)
    - **fights**: Lista de lutas do evento
    """
    try:
        event = await service.create_event(payload, creator_id=current_user.id)
        # Recarrega com lutas
        event_with_fights = await service.get_event(event.id)
        return event_with_fights
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.get(
    "/",
    response_model=List[EventListResponse],
    summary="List all events",
)
async def list_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    status: Optional[str] = Query(None, description="Filter by status"),
    organization: Optional[str] = Query(None, description="Filter by organization"),
    search: Optional[str] = Query(None, description="Search by event name"),
    order_by: Optional[str] = Query(
        "created_at",
        description="Order by: created_at, date_desc, date_asc, name_asc, name_desc",
    ),
    service: EventService = Depends(get_event_service),
):
    """
    Lista todos os eventos com paginação e filtros opcionais.

    - **skip**: Número de registros para pular
    - **limit**: Limite de registros retornados
    - **status**: Filtro por status (scheduled, completed, cancelled)
    - **organization**: Filtro por organização
    - **search**: Busca por nome do evento (case-insensitive, parcial)
    - **order_by**: Ordenação (created_at, date_desc, date_asc, name_asc, name_desc)
    """
    events = await service.list_events(
        skip=skip,
        limit=limit,
        status=status,
        organization=organization,
        search=search,
        order_by=order_by,
    )

    # Converte para EventListResponse
    response = []
    for event in events:
        response.append(
            EventListResponse(
                id=event.id,
                name=event.name,
                date=event.date,
                location=event.location,
                organization=event.organization,
                status=event.status,
                poster_url=event.poster_url,
                fights_count=len(event.fights) if hasattr(event, "fights") else 0,
                created_at=event.created_at,
            )
        )

    return response


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event by ID",
)
async def get_event(
    event_id: UUID,
    service: EventService = Depends(get_event_service),
):
    """
    Busca um evento específico pelo ID com todas suas lutas.
    """
    try:
        event = await service.get_event(event_id)
        return event
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        ) from e


@router.post(
    "/{event_id}/fights",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Add fight to event",
)
async def add_fight_to_event(
    event_id: UUID,
    payload: AddFightToEvent,
    service: EventService = Depends(get_event_service),
):
    """
    Adiciona uma nova luta a um evento existente.
    """
    try:
        fight = await service.add_fight_to_event(event_id, payload)
        return {"id": str(fight.id), "message": "Fight added successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.post(
    "/{event_id}/simulate",
    response_model=SimulationResult,
    summary="Simulate all fights in event",
)
async def simulate_event(
    event_id: UUID,
    service: EventService = Depends(get_event_service),
):
    """
    Simula todas as lutas de um evento.

    Este endpoint irá:
    1. Simular cada luta do evento em ordem
    2. Determinar vencedores e métodos de vitória
    3. Gerar estatísticas detalhadas de cada luta
    4. Marcar o evento como concluído

    Retorna os resultados de todas as simulações.
    """
    try:
        logger.info(f"Usuário solicitou simulação do evento {event_id}")
        result = await service.simulate_event(event_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        ) from e


@router.delete(
    "/{event_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete event",
)
async def delete_event(
    event_id: UUID,
    service: EventService = Depends(get_event_service),
):
    """
    Deleta um evento (soft delete).
    """
    try:
        await service.delete_event(event_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found"
        ) from e
