"""Service for Event operations"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from app.database.models.base import Event, Fight
from app.database.repositories.event import EventRepository
from app.database.repositories.fight import FightRepository
from app.database.repositories.fighter import FighterRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.exceptions.exceptions import ForbiddenError, NotFoundError
from app.schemas.domain.events.input import AddFightToEvent, CreateEvent
from app.schemas.domain.events.output import FightResponse, SimulationResult
from app.services.domain.fight_simulation import FightSimulationService


class EventService:
    """Service para gerenciar eventos de MMA"""

    def __init__(
        self,
        uow: UnitOfWorkConnection,
        simulation_service: FightSimulationService,
        user_email: str = "system",
    ):
        """
        Inicializa o EventService com injeção de dependência.

        Args:
            uow: Unit of Work para gerenciamento de transações
            simulation_service: Serviço de simulação de lutas (injetado)
            user_email: Email do usuário que executa as operações
        """
        self.uow = uow
        self.user_email = user_email
        self.event_repo = EventRepository(uow)
        self.fight_repo = FightRepository(uow)
        self.fighter_repo = FighterRepository(uow)
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
        # Busca o evento com lutas
        event = await self.get_event(event_id)

        if event.status == "completed":
            raise ForbiddenError("Event already simulated")

        if not event.fights:
            raise ForbiddenError("Event has no fights to simulate")

        # Mantém a sessão ativa durante toda a simulação
        session = await self.uow.get_session()

        # Ordena lutas por fight_order
        fights = sorted(event.fights, key=lambda f: f.fight_order)

        simulated_fights = []

        # Simula cada luta
        for fight in fights:
            if fight.status == "simulated":
                # Luta já simulada, apenas carrega os dados
                simulated_fights.append(fight)
                continue

            # Garante que os fighters estão carregados na sessão
            await session.refresh(fight, ["fighter1", "fighter2"])

            # Calcula probabilidades
            prob1, prob2 = self.simulation_service.calculate_win_probability(
                fight.fighter1, fight.fighter2
            )

            # Simula a luta (reusa a lógica do FightSimulationService)
            import random

            # Simula rounds
            round_details = []
            fighter1_total_points = 0
            fighter2_total_points = 0

            for round_num in range(1, fight.rounds + 1):
                round_result = self.simulation_service._simulate_round(
                    fight.fighter1, fight.fighter2, round_num
                )
                round_details.append(round_result)
                fighter1_total_points += round_result["fighter1_points"]
                fighter2_total_points += round_result["fighter2_points"]

            # Determina o vencedor
            winner_id = (
                fight.fighter1_id
                if fighter1_total_points > fighter2_total_points
                else fight.fighter2_id
            )

            # Determina o tipo de resultado
            result_types = self.simulation_service.predict_result_type(
                fight.fighter1, fight.fighter2
            )

            rand = random.random() * 100  # nosec B311
            if rand < result_types["ko"]:
                result_type = "KO"
                finish_round = random.randint(1, fight.rounds)  # nosec B311
                finish_time = f"{random.randint(0, 4)}:{random.randint(10, 59):02d}"  # nosec B311
            elif rand < result_types["ko"] + result_types["submission"]:
                result_type = "Submission"
                finish_round = random.randint(1, fight.rounds)  # nosec B311
                finish_time = f"{random.randint(0, 4)}:{random.randint(10, 59):02d}"  # nosec B311
            else:
                result_type = "Decision"
                finish_round = None
                finish_time = None

            # Atualiza a luta com o resultado
            fight.winner_id = winner_id
            fight.result_type = result_type
            fight.finish_round = finish_round
            fight.finish_time = finish_time
            fight.fighter1_probability = prob1
            fight.fighter2_probability = prob2
            fight.simulation_details = {
                "rounds": round_details,
                "total_points": {
                    "fighter1": round(fighter1_total_points, 2),
                    "fighter2": round(fighter2_total_points, 2),
                },
            }
            fight.status = "simulated"
            fight.updated_at = datetime.now(timezone.utc)
            fight.updated_by = self.user_email

            simulated_fights.append(fight)

        # Converte fights para response ANTES do commit (enquanto ainda estão na sessão)
        import asyncio

        fight_responses = await asyncio.gather(
            *[self._fight_to_response(f) for f in simulated_fights]
        )

        # Atualiza o status do evento
        event.status = "completed"
        event.updated_at = datetime.now(timezone.utc)
        event.updated_by = self.user_email

        # Commit das alterações (sessão já obtida no início do método)
        await session.commit()

        # Gera estatísticas do evento
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

        fighter1_summary = FighterSummary(
            id=fight.fighter1.id,
            name=fight.fighter1.name,
            nickname=fight.fighter1.nickname,
            actual_weight_class=fight.fighter1.actual_weight_class,
            image_url=fight.fighter1.image_url,
        )

        fighter2_summary = FighterSummary(
            id=fight.fighter2.id,
            name=fight.fighter2.name,
            nickname=fight.fighter2.nickname,
            actual_weight_class=fight.fighter2.actual_weight_class,
            image_url=fight.fighter2.image_url,
        )

        winner_summary = None
        if fight.winner_id:
            winner = (
                fight.fighter1
                if fight.winner_id == fight.fighter1_id
                else fight.fighter2
            )
            winner_summary = FighterSummary(
                id=winner.id,
                name=winner.name,
                nickname=winner.nickname,
                actual_weight_class=winner.actual_weight_class,
                image_url=winner.image_url,
            )

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

    async def delete_event(self, event_id: UUID) -> bool:
        """Deleta um evento (soft delete)"""
        return await self.event_repo.delete(event_id)
