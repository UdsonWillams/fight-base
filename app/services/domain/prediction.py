from datetime import datetime, timezone
from typing import List
from uuid import UUID

from sqlalchemy import select, func, cast as sa_cast, Integer
from app.core.logger import logger
from app.database.models.base import (
    Prediction,
    Fight,
    UserStats,
    EventLeaderboard,
    UserAchievement,
    Achievement,
)
from app.database.repositories.prediction import PredictionRepository
from app.database.repositories.achievement import AchievementRepository
from app.database.unit_of_work import UnitOfWorkConnection
from app.schemas.domain.predictions.input import CreatePrediction, UpdatePrediction


class PredictionService:
    def __init__(
        self,
        uow: UnitOfWorkConnection,
        prediction_repo: PredictionRepository,
        achievement_repo: AchievementRepository,
    ):
        self.uow = uow
        self.prediction_repo = prediction_repo
        self.achievement_repo = achievement_repo

    async def create_prediction(
        self, user_id: UUID, payload: CreatePrediction
    ) -> Prediction:
        """Cria um novo palpite para uma luta"""
        # Validar se já existe
        existing = await self.prediction_repo.get_prediction_by_user_and_fight(
            user_id, payload.fight_id
        )
        if existing:
            raise ValueError("Você já fez um palpite para esta luta.")

        prediction = Prediction(
            user_id=user_id,
            fight_id=payload.fight_id,
            event_id=payload.event_id,
            predicted_winner_id=payload.predicted_winner_id,
            predicted_method_id=payload.predicted_method_id,
            predicted_round=payload.predicted_round,
            created_by=str(user_id),
            updated_by=str(user_id),
        )

        return await self.prediction_repo.create(prediction)

    async def update_prediction(
        self, user_id: UUID, prediction_id: UUID, payload: UpdatePrediction
    ) -> Prediction:
        """Atualiza um palpite existente"""
        prediction = await self.prediction_repo.get_by_id(prediction_id)
        if not prediction or prediction.user_id != user_id:
            raise ValueError("Palpite não encontrado.")

        if prediction.processed_at:
            raise ValueError("Este palpite já foi processado e não pode ser alterado.")

        update_data = payload.model_dump(exclude_unset=True)
        return await self.prediction_repo.update(
            prediction_id, update_data, updated_by=str(user_id)
        )

    async def process_fight_results(self, fight_id: UUID):
        """
        Background Task: Processa todos os palpites de uma luta após o resultado ser definido.
        """
        try:
            session = await self.uow.get_session()

            # Buscar a luta e o método de finalização real
            # Precisamos de um repository de fight ou usar o session direto
            from sqlalchemy import select

            fight_query = select(Fight).filter(Fight.id == fight_id)
            fight_result = await session.execute(fight_query)
            fight = fight_result.scalar_one_or_none()

            if not fight or fight.status != "completed":
                logger.warning(f"Fight {fight_id} not found or not completed.")
                return

            # Buscar todos os palpites para esta luta que ainda não foram processados
            predictions_query = select(Prediction).filter(
                Prediction.fight_id == fight_id, Prediction.processed_at.is_(None)
            )
            predictions_result = await session.execute(predictions_query)
            predictions = predictions_result.scalars().all()

            for pred in predictions:
                await self._calculate_and_update_prediction(pred, fight)

            await session.commit()

            # Após processar palpites, atualizar rankings e conquistas (pode disparar outras tasks)
            # Para evitar loops complexos, chamamos as atualizações aqui mesmo
            for pred in predictions:
                await self._update_user_stats_and_achievements(pred.user_id)
                await self._update_event_leaderboard(pred.user_id, fight.event_id)

        except Exception as e:
            logger.error(f"Error processing fight results for fight {fight_id}: {e}")
            raise

    async def _calculate_and_update_prediction(self, pred: Prediction, fight: Fight):
        """Calcula pontos de um palpite específico"""
        points = 0
        is_winner_correct = False
        is_method_correct = False
        is_round_correct = False

        # 1. Vencedor (3 pontos)
        # Se fight.winner_id é NULL, foi DRAW/NC. O palpite correta seria predicted_winner_id NULL.
        if pred.predicted_winner_id == fight.winner_id:
            is_winner_correct = True
            points += 3

            # Bônus Underdog (baseado em probabilidade ML interna)
            points += self._calculate_underdog_bonus(fight, pred)

        # 2. Método (2 pontos bônus - apenas se acertou o vencedor)
        # Nota: dependendo da regra, pode dar pontos de método mesmo errando vencedor?
        # Geralmente em fantasy MMA, método só conta se acertar vencedor.
        if is_winner_correct:
            # Aqui precisaríamos comparar pred.predicted_method_id com o método real da luta
            # O sistema atual de Fight usa result_type (string).
            # Precisamos garantir que o admin preencheu o method_id corretamente no model Fight (ou similar)
            # Como adicionei finish_methods agora, a luta concluída deve ter um method_id vinculado.
            # Se não tiver (lutas antigas), pulamos.
            if (
                hasattr(fight, "method_id")
                and pred.predicted_method_id == fight.method_id
            ):
                is_method_correct = True
                points += 2

            # 3. Round (1 ponto bônus)
            if pred.predicted_round == fight.finish_round:
                is_round_correct = True
                points += 1

        # Atualizar Prediction
        pred.is_winner_correct = is_winner_correct
        pred.is_method_correct = is_method_correct
        pred.is_round_correct = is_round_correct
        pred.points_earned = points
        pred.processed_at = datetime.now(timezone.utc)

    def _calculate_underdog_bonus(self, fight: Fight, pred: Prediction) -> int:
        """Calcula bônus se acertou um azarão (probabilidade < 50%)"""
        # Se foi empate, não tem underdog bonus
        if fight.winner_id is None:
            return 0

        prob = 0
        if fight.winner_id == fight.fighter1_id:
            prob = fight.fighter1_probability or 0.5
        else:
            prob = fight.fighter2_probability or 0.5

        if prob < 0.3:
            return 3
        if prob < 0.4:
            return 2
        if prob < 0.5:
            return 1
        return 0

    async def _update_user_stats_and_achievements(self, user_id: UUID):
        """Atualiza estatísticas globais e verifica achievements"""
        session = await self.uow.get_session()

        # Buscar ou criar UserStats
        stats_query = select(UserStats).filter(UserStats.user_id == user_id)
        stats_result = await session.execute(stats_query)
        stats = stats_result.scalar_one_or_none()

        if not stats:
            stats = UserStats(user_id=user_id, created_by="system", updated_by="system")
            session.add(stats)

        # Agregar todos os palpites processados do usuário
        select(
            func.sum(Prediction.points_earned).label("total_points"),
            func.count(Prediction.id).label("total_preds"),
            func.sum(sa_cast(Prediction.is_winner_correct, Integer)).label(
                "correct_winners"
            ),
        ).filter(Prediction.user_id == user_id, Prediction.processed_at.is_not(None))
        # Obs: cast depende do banco, SQLAlchemy or_ / func.sum(cast(bool, int))
        # Para simplificar aqui, vamos assumir que atualizamos incrementalmente ou recalculamos

        # Recalcular (mais robusto)
        all_preds_query = select(Prediction).filter(
            Prediction.user_id == user_id, Prediction.processed_at.is_not(None)
        )
        all_preds_result = await session.execute(all_preds_query)
        all_preds = all_preds_result.scalars().all()

        stats.total_points = sum(p.points_earned for p in all_preds)
        stats.total_predictions = len(all_preds)
        stats.correct_winners = sum(1 for p in all_preds if p.is_winner_correct)
        stats.correct_methods = sum(1 for p in all_preds if p.is_method_correct)
        stats.correct_rounds = sum(1 for p in all_preds if p.is_round_correct)

        # Streak (lógica simples: últimos N palpites)
        # ... logic for streaks ...

        await self._check_achievements(user_id, stats, all_preds)

    async def _update_event_leaderboard(self, user_id: UUID, event_id: UUID):
        """Atualiza o ranking específico do evento para o usuário"""
        session = await self.uow.get_session()

        lb_query = select(EventLeaderboard).filter(
            EventLeaderboard.user_id == user_id, EventLeaderboard.event_id == event_id
        )
        lb_result = await session.execute(lb_query)
        lb = lb_result.scalar_one_or_none()

        if not lb:
            lb = EventLeaderboard(
                user_id=user_id,
                event_id=event_id,
                created_by="system",
                updated_by="system",
            )
            session.add(lb)

        event_preds_query = select(Prediction).filter(
            Prediction.user_id == user_id,
            Prediction.event_id == event_id,
            Prediction.processed_at.is_not(None),
        )
        event_preds_result = await session.execute(event_preds_query)
        event_preds = event_preds_result.scalars().all()

        lb.total_points = sum(p.points_earned for p in event_preds)
        lb.correct_winners = sum(1 for p in event_preds if p.is_winner_correct)
        lb.total_predictions = len(event_preds)

    async def _check_achievements(
        self, user_id: UUID, stats: UserStats, all_preds: List[Prediction]
    ):
        """Verifica se o usuário desbloqueou novas conquistas"""
        session = await self.uow.get_session()

        # Listar achievements que o usuário ainda não tem
        subquery = select(UserAchievement.achievement_id).filter(
            UserAchievement.user_id == user_id
        )
        new_ach_query = select(Achievement).filter(
            Achievement.id.notin_(subquery), Achievement.is_active.is_(True)
        )
        new_ach_result = await session.execute(new_ach_query)
        available_achievements = new_ach_result.scalars().all()

        for ach in available_achievements:
            unlocked = False
            if ach.code == "FIRST_PREDICTION" and stats.total_predictions >= 1:
                unlocked = True
            elif ach.code == "PREDICTIONS_10" and stats.total_predictions >= 10:
                unlocked = True
            # ... and so on for others ...

            if unlocked:
                ua = UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    created_by="system",
                    updated_by="system",
                )
                session.add(ua)
                logger.info(f"User {user_id} unlocked achievement: {ach.name}")
