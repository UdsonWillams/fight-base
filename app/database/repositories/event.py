"""Repository for Event operations"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.orm import selectinload

from app.database.models.base import Event, Fight
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection


class EventRepository(BaseRepository[Event]):
    """Repository para gerenciar eventos"""

    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(Event, uow)

    async def get_with_fights(self, event_id: UUID) -> Optional[Event]:
        """Busca um evento com suas lutas carregadas"""
        session = await self.uow.get_session()
        query = (
            select(self.model)
            .options(
                selectinload(self.model.fights).selectinload(Fight.fighter1),
                selectinload(self.model.fights).selectinload(Fight.fighter2),
                selectinload(self.model.fights).selectinload(Fight.winner),
            )
            .filter(
                self.model.id == event_id,
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

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
        session = await self.uow.get_session()
        query = (
            select(self.model)
            .options(
                selectinload(self.model.fights)
            )  # Eager loading para evitar lazy load
            .filter(
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )
        )

        if search:
            query = query.filter(self.model.name.ilike(f"%{search}%"))

        if status:
            query = query.filter(self.model.status == status)

        if organization:
            query = query.filter(self.model.organization.ilike(f"%{organization}%"))

        # Aplica ordenação
        if order_by == "created_at":
            query = query.order_by(desc(self.model.created_at))
        elif order_by == "date_desc":
            query = query.order_by(desc(self.model.date))
        elif order_by == "date_asc":
            query = query.order_by(self.model.date)
        elif order_by == "name_asc":
            query = query.order_by(self.model.name)
        elif order_by == "name_desc":
            query = query.order_by(desc(self.model.name))
        else:
            query = query.order_by(desc(self.model.created_at))  # Padrão

        query = query.offset(skip).limit(limit)
        result = await session.execute(query)
        return list(result.scalars().all())
