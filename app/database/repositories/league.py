from typing import List, Optional
from uuid import UUID
from sqlalchemy import select, desc
from app.database.models.base import League, LeagueMember
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.core.logger import logger
from app.exceptions.exceptions import RepositoryError


class LeagueRepository(BaseRepository[League]):
    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(League, uow)

    async def get_by_invite_code(self, invite_code: str) -> Optional[League]:
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(
                self.model.invite_code == invite_code, self.model.deleted_at.is_(None)
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching league by code: {e}")
            raise RepositoryError

    async def get_member(
        self, league_id: UUID, user_id: UUID
    ) -> Optional[LeagueMember]:
        try:
            session = await self.uow.get_session()
            query = select(LeagueMember).filter(
                LeagueMember.league_id == league_id,
                LeagueMember.user_id == user_id,
                LeagueMember.deleted_at.is_(None),
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching league member: {e}")
            raise RepositoryError

    async def get_league_members(
        self, league_id: UUID, limit: int = 100
    ) -> List[LeagueMember]:
        try:
            session = await self.uow.get_session()
            query = (
                select(LeagueMember)
                .filter(
                    LeagueMember.league_id == league_id,
                    LeagueMember.deleted_at.is_(None),
                )
                .order_by(desc(LeagueMember.total_points))
                .limit(limit)
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching league members: {e}")
            raise RepositoryError

    async def get_user_leagues(self, user_id: UUID) -> List[League]:
        try:
            session = await self.uow.get_session()
            query = (
                select(self.model)
                .join(LeagueMember, self.model.id == LeagueMember.league_id)
                .filter(
                    LeagueMember.user_id == user_id, self.model.deleted_at.is_(None)
                )
            )
            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching user leagues: {e}")
            raise RepositoryError
