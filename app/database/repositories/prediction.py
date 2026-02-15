from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, desc
from app.database.models.base import (
    Prediction,
    EventLeaderboard,
    UserStats,
    FinishMethod,
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
