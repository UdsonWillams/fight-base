"""Repository para gerenciar lutadores"""

from typing import Optional
from uuid import UUID

from sqlalchemy import func, select

from app.core.logger import logger
from app.database.models.base import Fighter
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.exceptions.exceptions import RepositoryError


class FighterRepository(BaseRepository[Fighter]):
    """Repositório específico para lutadores"""

    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(Fighter, uow)

    async def get_by_name(self, name: str) -> Optional[Fighter]:
        """Busca lutador por nome exato"""
        try:
            session = await self.uow.get_session()
            query = (
                select(self.model)
                .filter(self.model.name == name)
                .filter(
                    self.model.deleted_at.is_(None),
                    self.model.deleted_by.is_(None),
                )
            )
            result = await session.execute(query)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error fetching Fighter by name: {e}")
            raise RepositoryError

    async def search_fighters(
        self,
        name: Optional[str] = None,
        last_organization_fight: Optional[str] = None,
        actual_weight_class: Optional[str] = None,
        fighting_style: Optional[str] = None,
        is_real: Optional[bool] = None,
        min_overall: Optional[int] = None,
        limit: int = 10,
        offset: int = 0,
    ) -> list[Fighter]:
        """Busca avançada de lutadores"""
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )

            # Aplicar filtros
            if name:
                query = query.filter(self.model.name.ilike(f"%{name}%"))

            if last_organization_fight:
                query = query.filter(
                    self.model.last_organization_fight == last_organization_fight
                )

            if actual_weight_class:
                query = query.filter(
                    self.model.actual_weight_class == actual_weight_class
                )

            if fighting_style:
                query = query.filter(self.model.fighting_style == fighting_style)

            if is_real is not None:
                query = query.filter(self.model.is_real == is_real)

            # Filtro por overall rating mínimo (calculado como média dos atributos)
            if min_overall:
                query = query.filter(
                    (
                        self.model.striking
                        + self.model.grappling
                        + self.model.defense
                        + self.model.stamina
                        + self.model.speed
                        + self.model.strategy
                    )
                    / 6
                    >= min_overall
                )

            # Ordenar por overall rating (decrescente)
            query = query.order_by(
                (
                    (
                        self.model.striking
                        + self.model.grappling
                        + self.model.defense
                        + self.model.stamina
                        + self.model.speed
                        + self.model.strategy
                    )
                    / 6
                ).desc()
            )

            # Paginação
            query = query.offset(offset).limit(limit)

            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error searching fighters: {e}")
            raise RepositoryError

    async def count_fighters(
        self,
        name: Optional[str] = None,
        last_organization_fight: Optional[str] = None,
        actual_weight_class: Optional[str] = None,
        fighting_style: Optional[str] = None,
        is_real: Optional[bool] = None,
        min_overall: Optional[int] = None,
    ) -> int:
        """Conta lutadores que correspondem aos filtros"""
        try:
            session = await self.uow.get_session()
            query = select(func.count(self.model.id)).filter(
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )

            # Aplicar os mesmos filtros da busca
            if name:
                query = query.filter(self.model.name.ilike(f"%{name}%"))

            if last_organization_fight:
                query = query.filter(
                    self.model.last_organization_fight == last_organization_fight
                )

            if actual_weight_class:
                query = query.filter(
                    self.model.actual_weight_class == actual_weight_class
                )

            if fighting_style:
                query = query.filter(self.model.fighting_style == fighting_style)

            if is_real is not None:
                query = query.filter(self.model.is_real == is_real)

            if min_overall:
                query = query.filter(
                    (
                        self.model.striking
                        + self.model.grappling
                        + self.model.defense
                        + self.model.stamina
                        + self.model.speed
                        + self.model.strategy
                    )
                    / 6
                    >= min_overall
                )

            result = await session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting fighters: {e}")
            raise RepositoryError

    async def get_fighters_by_creator(
        self, creator_id: UUID, limit: int = 50, offset: int = 0
    ) -> list[Fighter]:
        """Busca lutadores criados por um usuário específico"""
        try:
            session = await self.uow.get_session()
            query = (
                select(self.model)
                .filter(self.model.creator_id == creator_id)
                .filter(
                    self.model.deleted_at.is_(None),
                    self.model.deleted_by.is_(None),
                )
                .order_by(self.model.created_at.desc())
                .offset(offset)
                .limit(limit)
            )

            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching fighters by creator: {e}")
            raise RepositoryError

    async def get_top_fighters(
        self,
        last_organization_fight: Optional[str] = None,
        actual_weight_class: Optional[str] = None,
        limit: int = 10,
    ) -> list[Fighter]:
        """Retorna os melhores lutadores (por overall rating)"""
        try:
            session = await self.uow.get_session()
            query = select(self.model).filter(
                self.model.deleted_at.is_(None),
                self.model.deleted_by.is_(None),
            )

            if last_organization_fight:
                query = query.filter(
                    self.model.last_organization_fight == last_organization_fight
                )

            if actual_weight_class:
                query = query.filter(
                    self.model.actual_weight_class == actual_weight_class
                )

            # Ordenar por overall rating
            query = query.order_by(
                (
                    (
                        self.model.striking
                        + self.model.grappling
                        + self.model.defense
                        + self.model.stamina
                        + self.model.speed
                        + self.model.strategy
                    )
                    / 6
                ).desc()
            ).limit(limit)

            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching top fighters: {e}")
            raise RepositoryError

    async def get_stats(self) -> dict:
        """Retorna estatísticas agregadas sobre lutadores"""
        try:
            session = await self.uow.get_session()

            # Total de lutadores
            total_query = (
                select(func.count())
                .select_from(self.model)
                .filter(self.model.deleted_at.is_(None))
            )
            total_result = await session.execute(total_query)
            total = total_result.scalar()

            # Total de lutadores reais
            real_query = (
                select(func.count())
                .select_from(self.model)
                .filter(self.model.deleted_at.is_(None), self.model.is_real.is_(True))
            )
            real_result = await session.execute(real_query)
            total_real = real_result.scalar()

            # Lutadores por última organização
            org_query = (
                select(self.model.last_organization_fight, func.count(self.model.id))
                .filter(self.model.deleted_at.is_(None))
                .group_by(self.model.last_organization_fight)
            )
            org_result = await session.execute(org_query)
            last_organizations = {org: count for org, count in org_result.all()}

            # Lutadores por categoria de peso atual
            weight_query = (
                select(self.model.actual_weight_class, func.count(self.model.id))
                .filter(self.model.deleted_at.is_(None))
                .group_by(self.model.actual_weight_class)
            )
            weight_result = await session.execute(weight_query)
            weight_classes = {wc: count for wc, count in weight_result.all()}

            # Média geral de overall rating
            avg_query = select(
                func.avg(
                    (
                        self.model.striking
                        + self.model.grappling
                        + self.model.defense
                        + self.model.stamina
                        + self.model.speed
                        + self.model.strategy
                    )
                    / 6
                )
            ).filter(self.model.deleted_at.is_(None))
            avg_result = await session.execute(avg_query)
            avg_overall = float(avg_result.scalar() or 0)

            return {
                "total_fighters": total,
                "total_real": total_real,
                "total_fictional": total - total_real,
                "last_organizations": last_organizations,
                "weight_classes": weight_classes,
                "avg_overall_rating": round(avg_overall, 2),
            }
        except Exception as e:
            logger.error(f"Error fetching fighter stats: {e}")
            raise RepositoryError
