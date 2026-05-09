from typing import List, Optional
from uuid import UUID
from sqlalchemy import select
from app.database.models.base import Achievement, UserAchievement
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.core.logger import logger
from app.exceptions.exceptions import RepositoryError


class AchievementRepository(BaseRepository[Achievement]):
    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(Achievement, uow)

    async def get_unlocked_achievements(self, user_id: UUID) -> List[Achievement]:
        try:
            session = await self.uow.get_session()
            query = (
                select(Achievement)
                .join(UserAchievement, Achievement.id == UserAchievement.achievement_id)
                .filter(
                    UserAchievement.user_id == user_id, Achievement.is_active.is_(True)
                )
                .order_by(UserAchievement.unlocked_at.desc())
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching unlocked achievements: {e}")
            raise RepositoryError

    async def get_by_code(self, code: str) -> Optional[Achievement]:
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(
                self.model.code == code, self.model.is_active.is_(True)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching achievement by code: {e}")
            raise RepositoryError

    async def get_available_for_user(self, user_id: UUID) -> List[Achievement]:
        try:
            session = await self.uow.get_session()
            subquery = select(UserAchievement.achievement_id).filter(
                UserAchievement.user_id == user_id
            )
            query = select(self.model).filter(
                self.model.id.notin_(subquery),
                self.model.is_active.is_(True),
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching available achievements: {e}")
            raise RepositoryError

    async def unlock_achievement(
        self, user_id: UUID, achievement_id: UUID
    ) -> Optional[UserAchievement]:
        try:
            session = await self.uow.get_session()
            existing = await session.execute(
                select(UserAchievement).filter(
                    UserAchievement.user_id == user_id,
                    UserAchievement.achievement_id == achievement_id,
                )
            )
            if existing.scalar_one_or_none():
                return None

            ua = UserAchievement(
                user_id=user_id,
                achievement_id=achievement_id,
                created_by="system",
                updated_by="system",
            )
            session.add(ua)
            await session.commit()
            await session.refresh(ua)
            return ua
        except Exception as e:
            logger.error(f"Error unlocking achievement: {e}")
            raise RepositoryError
