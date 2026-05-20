from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, desc
from app.database.models.base import (
    Prediction,
    EventLeaderboard,
    UserStats,
    FinishMethod,
    Fight,
    User,
)
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.core.logger import logger
from app.exceptions.exceptions import RepositoryError


class PredictionRepository(BaseRepository[Prediction]):
    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(Prediction, uow)

    async def get_user_predictions_for_event(
        self, user_id: UUID, event_id: UUID
    ) -> List[Prediction]:
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(
                self.model.user_id == user_id,
                self.model.event_id == event_id,
                self.model.deleted_at.is_(None),
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching user predictions: {e}")
            raise RepositoryError

    async def get_event_leaderboard(
        self, event_id: UUID, limit: int = 50
    ) -> List[EventLeaderboard]:
        try:
            session = await self.uow.get_session()
            query = (
                select(EventLeaderboard)
                .filter(
                    EventLeaderboard.event_id == event_id,
                    EventLeaderboard.deleted_at.is_(None),
                )
                .order_by(desc(EventLeaderboard.total_points))
                .limit(limit)
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching event leaderboard: {e}")
            raise RepositoryError

    async def get_event_leaderboard_with_users(
        self, event_id: UUID, limit: int = 50
    ) -> list[dict]:
        try:
            session = await self.uow.get_session()
            query = (
                select(EventLeaderboard, User.username, User.name)
                .join(User, EventLeaderboard.user_id == User.id)
                .filter(
                    EventLeaderboard.event_id == event_id,
                    EventLeaderboard.deleted_at.is_(None),
                )
                .order_by(desc(EventLeaderboard.total_points))
                .limit(limit)
            )
            result = await session.execute(query)
            rows = result.all()
            return [
                {
                    "user_id": lb.user_id,
                    "username": username,
                    "display_name": name or username,
                    "total_points": lb.total_points,
                    "correct_winners": lb.correct_winners,
                    "correct_methods": lb.correct_methods,
                    "correct_rounds": lb.correct_rounds,
                    "total_predictions": lb.total_predictions,
                }
                for lb, username, name in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching event leaderboard with users: {e}")
            raise RepositoryError

    async def get_user_stats(self, user_id: UUID) -> Optional[UserStats]:
        try:
            session = await self.uow.get_session()
            query = select(UserStats).filter(
                UserStats.user_id == user_id, UserStats.deleted_at.is_(None)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching user stats: {e}")
            raise RepositoryError

    async def get_or_create_user_stats(self, user_id: UUID) -> UserStats:
        try:
            session = await self.uow.get_session()
            query = select(UserStats).filter(
                UserStats.user_id == user_id, UserStats.deleted_at.is_(None)
            )
            result = await session.execute(query)
            stats = result.scalar_one_or_none()
            if not stats:
                stats = UserStats(
                    user_id=user_id, created_by="system", updated_by="system"
                )
                session.add(stats)
                await session.commit()
                await session.refresh(stats)
            return stats
        except Exception as e:
            logger.error(f"Error in get_or_create_user_stats: {e}")
            raise RepositoryError

    async def get_or_create_event_leaderboard(
        self, user_id: UUID, event_id: UUID
    ) -> EventLeaderboard:
        try:
            session = await self.uow.get_session()
            query = select(EventLeaderboard).filter(
                EventLeaderboard.user_id == user_id,
                EventLeaderboard.event_id == event_id,
            )
            result = await session.execute(query)
            lb = result.scalar_one_or_none()
            if not lb:
                lb = EventLeaderboard(
                    user_id=user_id,
                    event_id=event_id,
                    created_by="system",
                    updated_by="system",
                )
                session.add(lb)
                await session.commit()
                await session.refresh(lb)
            return lb
        except Exception as e:
            logger.error(f"Error in get_or_create_event_leaderboard: {e}")
            raise RepositoryError

    async def get_finish_methods(self) -> List[FinishMethod]:
        try:
            session = await self.uow.get_session()
            query = select(FinishMethod).filter(FinishMethod.is_active.is_(True))
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching finish methods: {e}")
            raise RepositoryError

    async def get_prediction_by_user_and_fight(
        self, user_id: UUID, fight_id: UUID
    ) -> Optional[Prediction]:
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(
                self.model.user_id == user_id,
                self.model.fight_id == fight_id,
                self.model.deleted_at.is_(None),
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching prediction by user and fight: {e}")
            raise RepositoryError

    async def get_unprocessed_predictions_for_fight(
        self, fight_id: UUID
    ) -> List[Prediction]:
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(
                self.model.fight_id == fight_id,
                self.model.processed_at.is_(None),
                self.model.deleted_at.is_(None),
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching unprocessed predictions: {e}")
            raise RepositoryError

    async def get_all_processed_for_user(self, user_id: UUID) -> List[Prediction]:
        try:
            session = await self.uow.get_session()
            query = (
                select(self.model)
                .filter(
                    self.model.user_id == user_id,
                    self.model.processed_at.is_not(None),
                    self.model.deleted_at.is_(None),
                )
                .order_by(self.model.processed_at.desc())
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching processed predictions: {e}")
            raise RepositoryError

    async def get_fight_by_id(self, fight_id: UUID) -> Optional[Fight]:
        try:
            session = await self.uow.get_session()
            query = select(Fight).filter(Fight.id == fight_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching fight: {e}")
            raise RepositoryError

    async def get_global_leaderboard(self, limit: int = 50) -> List[UserStats]:
        try:
            session = await self.uow.get_session()
            query = (
                select(UserStats)
                .filter(UserStats.deleted_at.is_(None))
                .order_by(desc(UserStats.total_points))
                .limit(limit)
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching global leaderboard: {e}")
            raise RepositoryError

    async def get_global_leaderboard_with_users(self, limit: int = 50) -> list[dict]:
        try:
            session = await self.uow.get_session()
            query = (
                select(UserStats, User.username, User.name)
                .join(User, UserStats.user_id == User.id)
                .filter(UserStats.deleted_at.is_(None))
                .order_by(desc(UserStats.total_points))
                .limit(limit)
            )
            result = await session.execute(query)
            rows = result.all()

            from app.database.models.base import LeagueMember, League

            user_ids = [row[0].user_id for row in rows]

            leagues_query = (
                select(LeagueMember.user_id, League.name)
                .join(League, LeagueMember.league_id == League.id)
                .filter(
                    LeagueMember.user_id.in_(user_ids),
                    LeagueMember.deleted_at.is_(None),
                )
            )
            leagues_result = await session.execute(leagues_query)
            leagues_rows = leagues_result.all()

            user_leagues: dict = {}
            for user_id, league_name in leagues_rows:
                if user_id not in user_leagues:
                    user_leagues[user_id] = []
                user_leagues[user_id].append(league_name)

            return [
                {
                    "user_id": stats.user_id,
                    "username": username,
                    "display_name": name or username,
                    "total_points": stats.total_points,
                    "correct_winners": stats.correct_winners,
                    "total_predictions": stats.total_predictions,
                    "current_streak": stats.current_streak,
                    "best_streak": stats.best_streak,
                    "underdog_bonus_points": stats.underdog_bonus_points,
                    "events_participated": stats.events_participated,
                    "leagues": user_leagues.get(stats.user_id, []),
                }
                for stats, username, name in rows
            ]
        except Exception as e:
            logger.error(f"Error fetching global leaderboard with users: {e}")
            raise RepositoryError
