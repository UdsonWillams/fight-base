"""Service for Event operations"""

import random
from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING
from uuid import UUID

from app.core.logger import logger

from app.database.models.base import Event, Fight
from app.database.repositories.event import EventRepository
from app.database.repositories.fight import FightRepository
from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.exceptions.exceptions import ForbiddenError, NotFoundError
from app.schemas.domain.events.input import AddFightToEvent, CreateEvent
from app.schemas.domain.events.output import FightResponse, SimulationResult
from app.services.domain.fight_simulation import FightSimulationService

if TYPE_CHECKING:
    from app.schemas.domain.predictions.input import UpdateFightResult


class EventService:
    """Service para gerenciar eventos de MMA"""

    def __init__(
        self,
        uow: UnitOfWorkConnection,
        simulation_service: FightSimulationService,
        event_repo: EventRepository,
        fight_repo: FightRepository,
        fighter_repo: FighterRepository,
        user_email: str = "system",
    ):
        self.uow = uow
        self.user_email = user_email
        self.event_repo = event_repo
        self.fight_repo = fight_repo
        self.fighter_repo = fighter_repo
        self.simulation_service = simulation_service

    async def create_event(self, payload: CreateEvent, creator_id: UUID) -> Event:
        """Cria um novo evento com lutas"""
        # Cria o evento
        event_data = payload.model_dump(exclude={"fights"})
        event = Event(
            **event_data,
            creator_id=creator_id,
            status="scheduled",
            created_by=self.user_email,
            updated_by=self.user_email,
        )

        session = await self.uow.get_session()
        session.add(event)
        await session.flush()  # Flush para obter o ID do evento

        # Cria as lutas associadas
        for fight_data in payload.fights:
            fight = Fight(
                **fight_data.model_dump(),
                event_id=event.id,
                status="scheduled",
                created_by=self.user_email,
                updated_by=self.user_email,
            )
            session.add(fight)

        await session.commit()
        await session.refresh(event)

        return event

    async def get_event(self, event_id: UUID) -> Optional[Event]:
        """Busca um evento com suas lutas"""
        event = await self.event_repo.get_with_fights(event_id)
        if not event:
            raise NotFoundError("Event not found")
        return event

    async def list_events(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        organization: Optional[str] = None,
        search: Optional[str] = None,
        order_by: Optional[str] = "created_at",
    ) -> List[Event]:
        """Lista eventos com filtros e ordenação"""
        return await self.event_repo.list_events(
            skip=skip,
            limit=limit,
            status=status,
            organization=organization,
            search=search,
            order_by=order_by,
        )

    async def add_fight_to_event(
        self, event_id: UUID, fight_data: AddFightToEvent
    ) -> Fight:
        """Adiciona uma luta a um evento existente"""
        event = await self.event_repo.get_by_id(event_id)
        if not event:
            raise NotFoundError("Event not found")

        if event.status != "scheduled":
            raise ForbiddenError("Cannot add fights to non-scheduled events")

        # Cria a luta
        fight = Fight(
            **fight_data.model_dump(),
            event_id=event_id,
            status="scheduled",
            created_by=self.user_email,
            updated_by=self.user_email,
        )

        session = await self.uow.get_session()
        session.add(fight)
        await session.commit()
        await session.refresh(fight)

        return fight

    async def simulate_event(self, event_id: UUID) -> SimulationResult:
        """Simula todas as lutas de um evento"""
        event = await self.get_event(event_id)

        if event.status == "completed":
            raise ForbiddenError("Event already simulated")

        if not event.fights:
            raise ForbiddenError("Event has no fights to simulate")

        session = await self.uow.get_session()

        fights = sorted(event.fights, key=lambda f: f.fight_order)

        simulated_fights = []

        for fight in fights:
            if fight.status == "simulated":
                simulated_fights.append(fight)
                continue

            await session.refresh(fight, ["fighter1", "fighter2"])

            prob1, prob2 = await self.simulation_service.calculate_win_probability(
                fight.fighter1, fight.fighter2
            )

            result = self.simulation_service._run_fight_simulation(
                fight.fighter1, fight.fighter2, fight.rounds
            )

            fight.winner_id = result.winner_id
            fight.result_type = result.result_type
            fight.finish_round = result.finish_round
            fight.finish_time = (
                f"{random.randint(0, 4)}:{random.randint(10, 59):02d}"  # nosec B311
                if result.finish_round
                else None
            )
            fight.fighter1_probability = prob1
            fight.fighter2_probability = prob2
            fight.simulation_details = {
                "rounds": result.round_details,
                "total_points": {
                    "fighter1": round(result.fighter1_total_points, 2),
                    "fighter2": round(result.fighter2_total_points, 2),
                },
            }
            fight.status = "simulated"
            fight.updated_at = datetime.now(timezone.utc)
            fight.updated_by = self.user_email

            simulated_fights.append(fight)

        import asyncio

        fight_responses = await asyncio.gather(
            *[self._fight_to_response(f) for f in simulated_fights]
        )

        event.status = "completed"
        event.updated_at = datetime.now(timezone.utc)
        event.updated_by = self.user_email

        await session.commit()

        ko_count = sum(1 for f in simulated_fights if f.result_type == "KO")
        sub_count = sum(1 for f in simulated_fights if f.result_type == "Submission")
        dec_count = sum(1 for f in simulated_fights if f.result_type == "Decision")

        summary = {
            "total_fights": len(simulated_fights),
            "knockouts": ko_count,
            "submissions": sub_count,
            "decisions": dec_count,
            "finish_rate": round(
                (ko_count + sub_count) / len(simulated_fights) * 100, 2
            ),
        }

        return SimulationResult(
            event_id=event.id,
            event_name=event.name,
            simulated_fights=fight_responses,
            summary=summary,
        )

    async def _fight_to_response(self, fight: Fight) -> FightResponse:
        """Converte Fight para FightResponse"""
        from app.schemas.domain.events.output import FighterSummary

        # Garante que as relações estão carregadas
        session = await self.uow.get_session()
        await session.refresh(fight, ["fighter1", "fighter2"])

        def _fighter_summary(fighter):
            return FighterSummary(
                id=fighter.id,
                name=fighter.name,
                nickname=fighter.nickname,
                actual_weight_class=fighter.actual_weight_class,
                image_url=fighter.image_url,
                overall_rating=getattr(fighter, "overall_rating", None),
                record=f"{fighter.wins}-{fighter.losses}-{fighter.draws}"
                if fighter.wins is not None
                else None,
            )

        fighter1_summary = _fighter_summary(fight.fighter1)
        fighter2_summary = _fighter_summary(fight.fighter2)

        winner_summary = None
        if fight.winner_id:
            winner = (
                fight.fighter1
                if fight.winner_id == fight.fighter1_id
                else fight.fighter2
            )
            winner_summary = _fighter_summary(winner)

        return FightResponse(
            id=fight.id,
            event_id=fight.event_id,
            fighter1_id=fight.fighter1_id,
            fighter2_id=fight.fighter2_id,
            fighter1=fighter1_summary,
            fighter2=fighter2_summary,
            fight_order=fight.fight_order,
            fight_type=fight.fight_type,
            weight_class=fight.weight_class,
            rounds=fight.rounds,
            is_title_fight=fight.is_title_fight,
            status=fight.status,
            winner_id=fight.winner_id,
            winner=winner_summary,
            result_type=fight.result_type,
            finish_round=fight.finish_round,
            finish_time=fight.finish_time,
            method_details=fight.method_details,
            fighter1_probability=fight.fighter1_probability,
            fighter2_probability=fight.fighter2_probability,
            simulation_details=fight.simulation_details,
            created_at=fight.created_at,
            updated_at=fight.updated_at,
        )

    async def update_fight_result(
        self, fight_id: UUID, payload: "UpdateFightResult"
    ) -> Fight:
        """
        Atualiza o resultado real de uma luta (usado por admins).
        Marca a luta como 'completed'.
        """
        fight = await self.fight_repo.get_by_id(fight_id)
        if not fight:
            raise NotFoundError("Fight not found")

        update_data = {
            "winner_id": payload.winner_id,
            "method_id": payload.method_id,  # Novo campo vinculado a FinishMethod
            "finish_round": payload.finish_round,
            "finish_time": payload.finish_time,
            "method_details": payload.method_details,
            "status": "completed",
            "updated_at": datetime.now(timezone.utc),
            "updated_by": self.user_email,
        }

        updated_fight = await self.fight_repo.update(
            fight_id, update_data, updated_by=self.user_email
        )

        # Verifica se todas as lutas do evento foram concluídas
        await self._check_and_complete_event(updated_fight.event_id)

        return updated_fight

    async def _check_and_complete_event(self, event_id: UUID):
        """
        Verifica se todas as lutas de um evento foram concluídas.
        Se sim, marca o evento como 'completed'.
        """
        event = await self.event_repo.get_with_fights(event_id)
        if not event or not event.fights:
            return

        # Verifica se todas as lutas têm status 'completed' ou 'simulated'
        all_fights_done = all(
            fight.status in ["completed", "simulated"] for fight in event.fights
        )

        # Se todas as lutas acabaram e o evento ainda não está marcado como completed
        if all_fights_done and event.status != "completed":
            session = await self.uow.get_session()
            event.status = "completed"
            event.updated_at = datetime.now(timezone.utc)
            event.updated_by = self.user_email
            await session.commit()
            logger.info(
                f"Event {event_id} automatically marked as completed - all fights finished"
            )

    async def delete_event(self, event_id: UUID) -> bool:
        """Deleta um evento (soft delete)"""
        return await self.event_repo.delete(event_id)
