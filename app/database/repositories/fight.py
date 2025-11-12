"""Repository for Fight operations"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database.models.base import Fight
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection


class FightRepository(BaseRepository[Fight]):
    """Repository para gerenciar lutas"""

    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(Fight, uow)

    async def get_fights_by_event(self, event_id: UUID) -> List[Fight]:
        """Busca todas as lutas de um evento"""
        session = await self.uow.get_session()
        query = (
            select(self.model)
            .options(
                selectinload(self.model.fighter1),
                selectinload(self.model.fighter2),
                selectinload(self.model.winner),
            )
            .filter(
                self.model.event_id == event_id,
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )
            .order_by(self.model.fight_order)
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def get_with_fighters(self, fight_id: UUID) -> Optional[Fight]:
        """Busca uma luta com lutadores carregados"""
        session = await self.uow.get_session()
        query = (
            select(self.model)
            .options(
                selectinload(self.model.fighter1),
                selectinload(self.model.fighter2),
                selectinload(self.model.winner),
            )
            .filter(
                self.model.id == fight_id,
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()
