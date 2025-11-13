"""Repository para gerenciar simulações de lutas"""

from uuid import UUID

from sqlalchemy import func, or_, select

from app.core.logger import logger
from app.database.models.base import FightSimulation
from app.database.repositories.base import BaseRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.exceptions.exceptions import RepositoryError


class FightSimulationRepository(BaseRepository[FightSimulation]):
    """Repositório específico para simulações de lutas"""

    def __init__(self, uow: UnitOfWorkConnection):
        super().__init__(FightSimulation, uow)

    async def get_fighter_history(
        self, fighter_id: UUID, limit: int = 20, offset: int = 0
    ) -> list[FightSimulation]:
        """Retorna o histórico de simulações de um lutador"""
        try:
            session = await self.uow.get_session()
            query = (
                select(self.model)
                .filter(
                    or_(
                        self.model.fighter1_id == fighter_id,
                        self.model.fighter2_id == fighter_id,
                    )
                )
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
            logger.error(f"Error fetching fighter history: {e}")
            raise RepositoryError

    async def get_fighter_stats(self, fighter_id: UUID) -> dict:
        """Retorna estatísticas de um lutador em simulações"""
        try:
            session = await self.uow.get_session()

            # Total de lutas
            total_query = (
                select(func.count())
                .select_from(self.model)
                .filter(
                    or_(
                        self.model.fighter1_id == fighter_id,
                        self.model.fighter2_id == fighter_id,
                    ),
                    self.model.deleted_at.is_(None),
                )
            )
            total_result = await session.execute(total_query)
            total_fights = total_result.scalar()

            # Vitórias
            wins_query = (
                select(func.count())
                .select_from(self.model)
                .filter(
                    self.model.winner_id == fighter_id, self.model.deleted_at.is_(None)
                )
            )
            wins_result = await session.execute(wins_query)
            wins = wins_result.scalar()

            # Vitórias por KO
            ko_query = (
                select(func.count())
                .select_from(self.model)
                .filter(
                    self.model.winner_id == fighter_id,
                    self.model.result_type == "KO",
                    self.model.deleted_at.is_(None),
                )
            )
            ko_result = await session.execute(ko_query)
            ko_wins = ko_result.scalar()

            # Vitórias por Finalização
            sub_query = (
                select(func.count())
                .select_from(self.model)
                .filter(
                    self.model.winner_id == fighter_id,
                    self.model.result_type == "Submission",
                    self.model.deleted_at.is_(None),
                )
            )
            sub_result = await session.execute(sub_query)
            submission_wins = sub_result.scalar()

            # Vitórias por Decisão
            dec_query = (
                select(func.count())
                .select_from(self.model)
                .filter(
                    self.model.winner_id == fighter_id,
                    self.model.result_type == "Decision",
                    self.model.deleted_at.is_(None),
                )
            )
            dec_result = await session.execute(dec_query)
            decision_wins = dec_result.scalar()

            losses = total_fights - wins
            win_rate = (wins / total_fights * 100) if total_fights > 0 else 0

            return {
                "total_fights": total_fights,
                "wins": wins,
                "losses": losses,
                "win_rate": round(win_rate, 1),
                "ko_wins": ko_wins,
                "submission_wins": submission_wins,
                "decision_wins": decision_wins,
            }
        except Exception as e:
            logger.error(f"Error fetching fighter simulation stats: {e}")
            raise RepositoryError

    async def get_matchup_history(
        self, fighter1_id: UUID, fighter2_id: UUID
    ) -> list[FightSimulation]:
        """Retorna histórico de confrontos entre dois lutadores"""
        try:
            session = await self.uow.get_session()
            query = (
                select(self.model)
                .filter(
                    or_(
                        (self.model.fighter1_id == fighter1_id)
                        & (self.model.fighter2_id == fighter2_id),
                        (self.model.fighter1_id == fighter2_id)
                        & (self.model.fighter2_id == fighter1_id),
                    )
                )
                .filter(
                    self.model.deleted_at.is_(None),
                    self.model.deleted_by.is_(None),
                )
                .order_by(self.model.created_at.desc())
            )

            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching matchup history: {e}")
            raise RepositoryError

    async def get_recent_simulations(self, limit: int = 50) -> list[FightSimulation]:
        """Retorna as simulações mais recentes"""
        try:
            session = await self.uow.get_session()
            query = (
                select(self.model)
                .filter(
                    self.model.deleted_at.is_(None),
                    self.model.deleted_by.is_(None),
                )
                .order_by(self.model.created_at.desc())
                .limit(limit)
            )

            result = await session.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error fetching recent simulations: {e}")
            raise RepositoryError

    async def get_total_count(self) -> int:
        """Retorna o total de simulações no sistema"""
        try:
            session = await self.uow.get_session()
            query = (
                select(func.count())
                .select_from(self.model)
                .filter(
                    self.model.deleted_at.is_(None),
                    self.model.deleted_by.is_(None),
                )
            )
            result = await session.execute(query)
            return result.scalar() or 0
        except Exception as e:
            logger.error(f"Error counting simulations: {e}")
            raise RepositoryError
