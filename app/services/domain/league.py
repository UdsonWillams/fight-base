import secrets
import string
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.database.models.base import (
    Event,
    Fight,
    Fighter,
    League,
    LeagueMember,
    Prediction,
)
from app.database.repositories.league import LeagueRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.core.logger import logger


class LeagueService:
    def __init__(self, uow: UnitOfWorkConnection, league_repo: LeagueRepository):
        self.uow = uow
        self.league_repo = league_repo

    async def create_league(
        self,
        user_id: UUID,
        name: str,
        description: Optional[str],
        is_public: bool,
        max_members: int,
    ) -> League:
        """Cria uma nova liga e adiciona o criador como membro"""
        invite_code = self._generate_invite_code()
        for _ in range(10):
            existing = await self.league_repo.get_by_invite_code(invite_code)
            if not existing:
                break
            invite_code = self._generate_invite_code()

        league = League(
            name=name,
            description=description,
            invite_code=invite_code,
            is_public=is_public,
            max_members=max_members,
            owner_id=user_id,
            created_by=str(user_id),
            updated_by=str(user_id),
        )

        created_league = await self.league_repo.create(league)

        member = LeagueMember(
            league_id=created_league.id,
            user_id=user_id,
            created_by=str(user_id),
            updated_by=str(user_id),
        )
        session = await self.uow.get_session()
        session.add(member)
        await session.commit()

        await session.refresh(created_league, ["members"])

        return created_league

    async def join_league(self, user_id: UUID, invite_code: str) -> League:
        """Entra em uma liga usando o código de convite"""
        league = await self.league_repo.get_by_invite_code(invite_code)
        if not league:
            raise ValueError("Liga não encontrada com este código.")

        existing_member = await self.league_repo.get_member(league.id, user_id)
        if existing_member:
            raise ValueError("Você já faz parte desta liga.")

        session = await self.uow.get_session()

        count_query = select(func.count(LeagueMember.id)).filter(
            LeagueMember.league_id == league.id
        )
        count_result = await session.execute(count_query)
        count = count_result.scalar()

        if count >= league.max_members:
            raise ValueError("Esta liga atingiu o limite máximo de membros.")

        member = LeagueMember(
            league_id=league.id,
            user_id=user_id,
            created_by=str(user_id),
            updated_by=str(user_id),
        )
        session.add(member)
        await session.commit()

        await session.refresh(league, ["members"])

        return league

    def _generate_invite_code(self, length: int = 8) -> str:
        chars = string.ascii_uppercase + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    async def get_user_leagues(self, user_id: UUID) -> List[League]:
        return await self.league_repo.get_user_leagues(user_id)

    async def get_league_leaderboard(
        self, league_id: UUID, limit: int = 50
    ) -> List[LeagueMember]:
        return await self.league_repo.get_league_members(league_id, limit)

    # ── League Detail ──
    async def get_league_detail(self, league_id: UUID, current_user_id: UUID) -> dict:
        session = await self.uow.get_session()
        query = (
            select(League)
            .options(
                selectinload(League.members),
                selectinload(League.owner),
                selectinload(League.active_event),
            )
            .filter(
                League.id == league_id,
                League.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        league = result.unique().scalar_one_or_none()

        if not league:
            raise ValueError("Liga não encontrada.")

        is_owner = str(league.owner_id) == str(current_user_id)
        is_member = any(str(m.user_id) == str(current_user_id) for m in league.members)

        active_event_fights_count = 0
        active_event_name = None
        active_event_date = None
        if league.active_event_id:
            event_query = select(Fight).filter(
                Fight.event_id == league.active_event_id,
                Fight.deleted_at.is_(None),
            )
            fights_result = await session.execute(event_query)
            active_event_fights_count = len(fights_result.scalars().all())
            if league.active_event:
                active_event_name = league.active_event.name
                active_event_date = (
                    league.active_event.date.isoformat()
                    if league.active_event.date
                    else None
                )

        return {
            "id": str(league.id),
            "name": league.name,
            "description": league.description,
            "invite_code": league.invite_code,
            "owner_id": str(league.owner_id),
            "owner_name": league.owner.name if league.owner else "",
            "members_count": league.members_count,
            "is_owner": is_owner,
            "is_member": is_member,
            "active_event_id": (
                str(league.active_event_id) if league.active_event_id else None
            ),
            "active_event_name": active_event_name,
            "active_event_date": active_event_date,
            "active_event_fights_count": active_event_fights_count,
        }

    # ── Select Event ──
    async def select_event(
        self, league_id: UUID, event_id: UUID, user_id: UUID
    ) -> League:
        session = await self.uow.get_session()
        query = select(League).filter(
            League.id == league_id, League.deleted_at.is_(None)
        )
        result = await session.execute(query)
        league = result.scalar_one_or_none()

        if not league:
            raise ValueError("Liga não encontrada.")
        if str(league.owner_id) != str(user_id):
            raise ValueError("Apenas o dono da liga pode selecionar um evento.")

        event_query = select(Event).filter(
            Event.id == event_id, Event.deleted_at.is_(None)
        )
        event_result = await session.execute(event_query)
        event = event_result.scalar_one_or_none()
        if not event:
            raise ValueError("Evento não encontrado.")

        league.active_event_id = event_id
        league.updated_by = str(user_id)
        await session.commit()
        await session.refresh(league, ["active_event"])
        return league

    # ── League Predictions ──
    async def create_league_predictions(
        self, league_id: UUID, user_id: UUID, predictions: list
    ) -> list[Prediction]:
        session = await self.uow.get_session()

        league = await self._get_league(league_id)
        if not league.active_event_id:
            raise ValueError("Liga não possui evento ativo.")

        member = await self.league_repo.get_member(league_id, user_id)
        if not member:
            raise ValueError("Você não é membro desta liga.")

        created = []
        for pred in predictions:
            existing_query = select(Prediction).filter(
                Prediction.user_id == user_id,
                Prediction.fight_id == pred.fight_id,
                Prediction.league_id == league_id,
                Prediction.deleted_at.is_(None),
            )
            existing_result = await session.execute(existing_query)
            existing = existing_result.scalar_one_or_none()

            if existing:
                existing.predicted_winner_id = pred.predicted_winner_id
                existing.updated_by = str(user_id)
                created.append(existing)
                continue

            new_pred = Prediction(
                user_id=user_id,
                fight_id=pred.fight_id,
                event_id=league.active_event_id,
                league_id=league_id,
                predicted_winner_id=pred.predicted_winner_id,
                created_by=str(user_id),
                updated_by=str(user_id),
            )
            session.add(new_pred)
            created.append(new_pred)

        await session.commit()
        for p in created:
            await session.refresh(p)
        return created

    async def get_league_predictions(
        self, league_id: UUID, user_id: UUID
    ) -> list[dict]:
        session = await self.uow.get_session()

        query = (
            select(Prediction, Fight, Fighter)
            .join(Fight, Prediction.fight_id == Fight.id)
            .outerjoin(
                Fighter,
                Prediction.predicted_winner_id == Fighter.id,
            )
            .filter(
                Prediction.user_id == user_id,
                Prediction.league_id == league_id,
                Prediction.deleted_at.is_(None),
            )
        )
        result = await session.execute(query)
        rows = result.all()

        output = []
        for pred, fight, fighter in rows:
            output.append(
                {
                    "id": str(pred.id),
                    "fight_id": str(pred.fight_id),
                    "fighter1_name": fight.fighter1.name
                    if hasattr(fight, "fighter1") and fight.fighter1
                    else None,
                    "fighter2_name": fight.fighter2.name
                    if hasattr(fight, "fighter2") and fight.fighter2
                    else None,
                    "predicted_winner_id": (
                        str(pred.predicted_winner_id)
                        if pred.predicted_winner_id
                        else None
                    ),
                    "predicted_winner_name": fighter.name if fighter else None,
                    "is_correct": pred.is_winner_correct,
                    "points_earned": pred.points_earned or 0,
                }
            )
        return output

    async def _get_league(self, league_id: UUID) -> League:
        session = await self.uow.get_session()
        query = select(League).filter(
            League.id == league_id, League.deleted_at.is_(None)
        )
        result = await session.execute(query)
        league = result.scalar_one_or_none()
        if not league:
            raise ValueError("Liga não encontrada.")
        return league

    # ── Leave League ──
    async def leave_league(self, league_id: UUID, user_id: UUID) -> None:
        session = await self.uow.get_session()
        query = select(LeagueMember).filter(
            LeagueMember.league_id == league_id,
            LeagueMember.user_id == user_id,
            LeagueMember.deleted_at.is_(None),
        )
        result = await session.execute(query)
        member = result.scalar_one_or_none()

        if not member:
            raise ValueError("Você não é membro desta liga.")

        league = await self._get_league(league_id)
        if str(league.owner_id) == str(user_id):
            raise ValueError(
                "O dono da liga não pode sair. Delete a liga ou transfira a posse."
            )

        member.deleted_at = func.now()
        member.deleted_by = str(user_id)
        await session.commit()

    # ── Delete League ──
    async def delete_league(self, league_id: UUID, user_id: UUID) -> None:
        league = await self._get_league(league_id)
        if str(league.owner_id) != str(user_id):
            raise ValueError("Apenas o dono pode deletar a liga.")
        await self.league_repo.delete(league_id, deleted_by=str(user_id))

    # ── Create Fighter with Points ──
    async def create_fighter_with_points(
        self, league_id: UUID, user_id: UUID, fighter_data
    ) -> dict:
        session = await self.uow.get_session()

        member = await self.league_repo.get_member(league_id, user_id)
        if not member:
            raise ValueError("Você não é membro desta liga.")

        points_cost = getattr(fighter_data, "points_cost", 0) or 0
        if member.total_points < points_cost:
            raise ValueError(
                f"Pontos insuficientes. Você tem {member.total_points}, "
                f"custa {points_cost}."
            )

        import uuid as uuid_lib

        fighter = Fighter(
            id=uuid_lib.uuid4(),
            name=fighter_data.name,
            nickname=getattr(fighter_data, "nickname", None),
            actual_weight_class=getattr(fighter_data, "actual_weight_class", None),
            fighting_style=getattr(fighter_data, "fighting_style", None),
            stance=getattr(fighter_data, "stance", None),
            height=getattr(fighter_data, "height", None),
            weight=getattr(fighter_data, "weight", None),
            reach=getattr(fighter_data, "reach", None),
            organization=getattr(fighter_data, "organization", "League"),
            gender=getattr(fighter_data, "gender", None),
            is_real=False,
            creator_id=user_id,
            created_by=str(user_id),
            updated_by=str(user_id),
        )
        session.add(fighter)

        member.total_points -= points_cost
        member.updated_by = str(user_id)

        await session.commit()
        await session.refresh(fighter)

        logger.info(
            f"Fighter '{fighter.name}' criado na liga {league_id} "
            f"por {user_id} (custo: {points_cost} pts)"
        )

        return {
            "id": str(fighter.id),
            "name": fighter.name,
            "nickname": fighter.nickname,
            "points_spent": points_cost,
            "remaining_points": member.total_points,
        }

    # ── Score League Event ──
    async def score_league_event(self, league_id: UUID, event_id: UUID) -> None:
        """
        Calcula pontos para todos os palpites de uma liga em um evento finalizado.
        Chamado quando um evento é completado (simulado ou resultados reais definidos).
        """
        session = await self.uow.get_session()

        league = await self._get_league(league_id)
        if str(league.active_event_id) != str(event_id):
            return

        predictions_query = select(Prediction).filter(
            Prediction.league_id == league_id,
            Prediction.event_id == event_id,
            Prediction.deleted_at.is_(None),
        )
        preds_result = await session.execute(predictions_query)
        predictions = preds_result.scalars().all()

        if not predictions:
            logger.info(f"Liga {league_id}: sem palpites para pontuar.")
            return

        for pred in predictions:
            fight_query = select(Fight).filter(
                Fight.id == pred.fight_id, Fight.deleted_at.is_(None)
            )
            fight_result = await session.execute(fight_query)
            fight = fight_result.scalar_one_or_none()

            if not fight or fight.status not in ("completed", "simulated"):
                continue

            points = 0
            pred.is_winner_correct = (
                fight.winner_id is not None
                and pred.predicted_winner_id is not None
                and fight.winner_id == pred.predicted_winner_id
            )

            if pred.is_winner_correct:
                points += 3
                underdog_bonus = self._calculate_underdog_bonus(fight, pred)
                points += underdog_bonus

            pred.points_earned = points
            pred.processed_at = func.now()

            member_query = select(LeagueMember).filter(
                LeagueMember.league_id == league_id,
                LeagueMember.user_id == pred.user_id,
                LeagueMember.deleted_at.is_(None),
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            if member:
                member.total_points = (member.total_points or 0) + points
                member.updated_by = "system"

        await session.commit()
        logger.info(
            f"Liga {league_id}: {len(predictions)} palpites pontuados "
            f"para o evento {event_id}"
        )

    def _calculate_underdog_bonus(self, fight: Fight, pred: Prediction) -> int:
        prob = None
        if fight.winner_id == fight.fighter1_id:
            prob = fight.fighter1_probability
        elif fight.winner_id == fight.fighter2_id:
            prob = fight.fighter2_probability

        if prob is None:
            return 0
        if prob < 0.3:
            return 3
        if prob < 0.4:
            return 2
        if prob < 0.5:
            return 1
        return 0
