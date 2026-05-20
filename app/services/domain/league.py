import secrets
import string
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select, desc, Integer
from sqlalchemy.orm import selectinload

from app.database.models.base import (
    Event,
    Fight,
    Fighter,
    FinishMethod,
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

    async def get_league_event_leaderboard(
        self, league_id: UUID, event_id: UUID, limit: int = 50
    ) -> list[dict]:
        session = await self.uow.get_session()

        query = (
            select(
                Prediction.user_id,
                func.sum(Prediction.points_earned).label("total_points"),
                func.count(Prediction.id).label("total_predictions"),
                func.sum(func.cast(Prediction.is_winner_correct, Integer)).label(
                    "correct_winners"
                ),
            )
            .filter(
                Prediction.league_id == league_id,
                Prediction.event_id == event_id,
                Prediction.deleted_at.is_(None),
                Prediction.processed_at.is_not(None),
            )
            .group_by(Prediction.user_id)
            .order_by(desc(func.sum(Prediction.points_earned)))
            .limit(limit)
        )
        result = await session.execute(query)
        rows = result.all()

        from app.database.models.base import User as UserModel

        entries = []
        for rank, row in enumerate(rows, 1):
            user_query = select(UserModel).filter(UserModel.id == row[0])
            user_result = await session.execute(user_query)
            user = user_result.scalar_one_or_none()
            entries.append(
                {
                    "user_id": str(row[0]),
                    "username": user.name if user else "",
                    "total_points": int(row[1] or 0),
                    "total_predictions": int(row[2] or 0),
                    "correct_winners": int(row[3] or 0),
                    "rank": rank,
                }
            )
        return entries

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
        active_event_status = None
        active_event_winner_name = None
        active_event_winner_points = 0

        if league.active_event_id:
            event_query = select(Fight).filter(
                Fight.event_id == league.active_event_id,
                Fight.deleted_at.is_(None),
            )
            fights_result = await session.execute(event_query)
            fights_list = fights_result.scalars().all()
            active_event_fights_count = len(fights_list)

            if league.active_event:
                active_event_name = league.active_event.name
                active_event_date = (
                    league.active_event.date.isoformat()
                    if league.active_event.date
                    else None
                )
                active_event_status = league.active_event.status

            if active_event_status == "completed":
                predictions_query = (
                    select(
                        Prediction.user_id,
                        func.sum(Prediction.points_earned).label("total_points"),
                    )
                    .filter(
                        Prediction.league_id == league_id,
                        Prediction.event_id == league.active_event_id,
                        Prediction.deleted_at.is_(None),
                        Prediction.processed_at.is_not(None),
                    )
                    .group_by(Prediction.user_id)
                    .order_by(desc(func.sum(Prediction.points_earned)))
                    .limit(1)
                )
                preds_result = await session.execute(predictions_query)
                top = preds_result.first()
                if top:
                    from app.database.models.base import User as UserModel

                    user_query = select(UserModel).filter(UserModel.id == top[0])
                    user_result = await session.execute(user_query)
                    winner_user = user_result.scalar_one_or_none()
                    active_event_winner_name = winner_user.name if winner_user else ""
                    active_event_winner_points = int(top[1])

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
            "active_event_status": active_event_status,
            "active_event_winner_name": active_event_winner_name,
            "active_event_winner_points": active_event_winner_points,
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
        await session.refresh(league, ["active_event", "members"])
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
                existing.predicted_method_id = getattr(
                    pred, "predicted_method_id", None
                )
                existing.predicted_round = getattr(pred, "predicted_round", None)
                existing.updated_by = str(user_id)
                created.append(existing)
                continue

            new_pred = Prediction(
                user_id=user_id,
                fight_id=pred.fight_id,
                event_id=league.active_event_id,
                league_id=league_id,
                predicted_winner_id=pred.predicted_winner_id,
                predicted_method_id=getattr(pred, "predicted_method_id", None),
                predicted_round=getattr(pred, "predicted_round", None),
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
            .options(
                selectinload(Fight.fighter1),
                selectinload(Fight.fighter2),
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
                    "predicted_method_id": (
                        str(pred.predicted_method_id)
                        if pred.predicted_method_id
                        else None
                    ),
                    "predicted_round": pred.predicted_round,
                    "is_winner_correct": pred.is_winner_correct,
                    "is_method_correct": pred.is_method_correct,
                    "is_round_correct": pred.is_round_correct,
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

    # ── Upgrade Fighter Attributes ──
    async def upgrade_fighter_attributes(
        self,
        league_id: UUID,
        fighter_id: UUID,
        user_id: UUID,
        attribute: str,
        points_cost: int,
    ) -> dict:
        session = await self.uow.get_session()

        member = await self.league_repo.get_member(league_id, user_id)
        if not member:
            raise ValueError("Você não é membro desta liga.")

        if member.total_points < points_cost:
            raise ValueError(
                f"Pontos insuficientes. Você tem {member.total_points}, "
                f"custa {points_cost}."
            )

        fighter_query = select(Fighter).filter(
            Fighter.id == fighter_id, Fighter.deleted_at.is_(None)
        )
        fighter_result = await session.execute(fighter_query)
        fighter = fighter_result.scalar_one_or_none()
        if not fighter:
            raise ValueError("Lutador não encontrado.")
        if str(fighter.creator_id) != str(user_id):
            raise ValueError("Você não criou este lutador.")

        current = getattr(fighter, attribute, 0) or 0
        setattr(fighter, attribute, current + points_cost)
        fighter.updated_by = str(user_id)

        member.total_points -= points_cost
        member.updated_by = str(user_id)

        await session.commit()
        await session.refresh(fighter)

        logger.info(
            f"Fighter '{fighter.name}' upgraded: {attribute} {current} → {getattr(fighter, attribute)} "
            f"(custo: {points_cost} pts na liga {league_id})"
        )

        return {
            "fighter_id": str(fighter.id),
            "fighter_name": fighter.name,
            "attribute": attribute,
            "old_value": current,
            "new_value": getattr(fighter, attribute),
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
            pred.is_winner_correct = False

            fight_is_draw_nc = (
                fight.result_type is not None
                and fight.result_type.lower() in ("draw", "no_contest")
            )

            if pred.predicted_method_id:
                method_query = select(FinishMethod).filter(
                    FinishMethod.id == pred.predicted_method_id
                )
                method_result = await session.execute(method_query)
                pred_method = method_result.scalar_one_or_none()

                if pred_method and pred_method.code in ("DRAW", "NC"):
                    pred.is_winner_correct = fight_is_draw_nc
                    if pred.is_winner_correct:
                        points += 1
                elif (
                    fight.winner_id is not None
                    and pred.predicted_winner_id is not None
                    and fight.winner_id == pred.predicted_winner_id
                ):
                    pred.is_winner_correct = True
                    points += 1
            elif (
                fight.winner_id is not None
                and pred.predicted_winner_id is not None
                and fight.winner_id == pred.predicted_winner_id
            ):
                pred.is_winner_correct = True
                points += 1

            if (
                pred.is_winner_correct
                and pred.predicted_method_id
                and fight.result_type
            ):
                method_query = select(FinishMethod).filter(
                    FinishMethod.id == pred.predicted_method_id
                )
                method_result = await session.execute(method_query)
                method = method_result.scalar_one_or_none()
                pred.is_method_correct = method is not None and (
                    method.code == fight.result_type or method.name == fight.result_type
                )
                if pred.is_method_correct:
                    points += 1
            else:
                pred.is_method_correct = False

            pred.is_round_correct = (
                pred.is_winner_correct
                and pred.predicted_round is not None
                and fight.finish_round is not None
                and pred.predicted_round == fight.finish_round
            )
            if pred.is_round_correct:
                points += 1

            if (
                pred.is_winner_correct
                and pred.is_method_correct
                and pred.is_round_correct
            ):
                points += 1

            old_points = pred.points_earned or 0
            pred.points_earned = points
            pred.processed_at = func.now()

            delta = points - old_points

            member_query = select(LeagueMember).filter(
                LeagueMember.league_id == league_id,
                LeagueMember.user_id == pred.user_id,
                LeagueMember.deleted_at.is_(None),
            )
            member_result = await session.execute(member_query)
            member = member_result.scalar_one_or_none()
            if member:
                if delta != 0:
                    member.total_points = (member.total_points or 0) + delta
                    member.updated_by = "system"

        await session.commit()
        logger.info(
            f"Liga {league_id}: {len(predictions)} palpites pontuados "
            f"para o evento {event_id}"
        )
