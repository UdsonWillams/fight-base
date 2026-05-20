from datetime import datetime, timezone
from typing import List
from uuid import UUID

from app.core.logger import logger
from app.database.models.base import (
    Prediction,
    Fight,
    UserStats,
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
        Cria sua própria sessão de banco, independente da request HTTP.

        Pipeline:
        1. Calcula pontos dos palpites
        2. Atualiza estatísticas (UserStats) de cada usuário
        3. Atualiza leaderboard do evento
        4. Verifica conquistas dos usuários (processo separado, após consolidação)
        """
        async with UnitOfWorkConnection() as bg_uow:
            bg_prediction_repo = PredictionRepository(bg_uow)
            bg_achievement_repo = AchievementRepository(bg_uow)

            fight = await bg_prediction_repo.get_fight_by_id(fight_id)
            if not fight or fight.status != "completed":
                logger.warning(f"Fight {fight_id} not found or not completed.")
                return

            predictions = (
                await bg_prediction_repo.get_unprocessed_predictions_for_fight(fight_id)
            )

            for pred in predictions:
                self._calculate_and_update_prediction(pred, fight)

            await bg_uow.commit()

            affected_users = set()

            for pred in predictions:
                await self._update_user_stats(bg_uow, bg_prediction_repo, pred.user_id)
                await self._update_event_leaderboard(
                    bg_uow, bg_prediction_repo, pred.user_id, fight.event_id
                )
                affected_users.add(pred.user_id)

            unique_users = list(affected_users)
            for user_id in unique_users:
                await self._check_user_achievements(
                    bg_uow, bg_prediction_repo, bg_achievement_repo, user_id
                )

        logger.info(f"Processed {len(predictions)} predictions for fight {fight_id}")

    def _calculate_and_update_prediction(self, pred: Prediction, fight: Fight):
        points = 0
        is_winner_correct = False
        is_method_correct = False
        is_round_correct = False

        if pred.predicted_winner_id == fight.winner_id:
            is_winner_correct = True
            points += 3

            points += self._calculate_underdog_bonus(fight, pred)

        if is_winner_correct:
            if (
                hasattr(fight, "method_id")
                and pred.predicted_method_id == fight.method_id
            ):
                is_method_correct = True
                points += 2

            if pred.predicted_round == fight.finish_round:
                is_round_correct = True
                points += 1

        pred.is_winner_correct = is_winner_correct
        pred.is_method_correct = is_method_correct
        pred.is_round_correct = is_round_correct
        pred.points_earned = points
        pred.processed_at = datetime.now(timezone.utc)

    def _calculate_underdog_bonus(self, fight: Fight, pred: Prediction) -> int:
        if fight.winner_id is None:
            return 0

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

    async def _update_user_stats(
        self,
        uow: UnitOfWorkConnection,
        prediction_repo: PredictionRepository,
        user_id: UUID,
    ):
        stats = await prediction_repo.get_or_create_user_stats(user_id)

        all_preds = await prediction_repo.get_all_processed_for_user(user_id)

        stats.total_points = sum(p.points_earned or 0 for p in all_preds)
        stats.total_predictions = len(all_preds)
        stats.correct_winners = sum(1 for p in all_preds if p.is_winner_correct)
        stats.correct_methods = sum(1 for p in all_preds if p.is_method_correct)
        stats.correct_rounds = sum(1 for p in all_preds if p.is_round_correct)

        underdog_total = 0
        for p in all_preds:
            if p.points_earned and p.is_winner_correct and p.points_earned > 3:
                underdog_total += p.points_earned - 3
        stats.underdog_bonus_points = underdog_total

        current_streak = 0
        best_streak = 0
        for p in all_preds:
            if p.is_winner_correct:
                current_streak += 1
                if current_streak > best_streak:
                    best_streak = current_streak
            else:
                current_streak = 0
        stats.current_streak = current_streak
        stats.best_streak = max(stats.best_streak or 0, best_streak)

        event_ids = set(p.event_id for p in all_preds if p.event_id)
        stats.events_participated = len(event_ids)

        now = datetime.now(timezone.utc)
        stats.points_this_month = sum(
            (p.points_earned or 0)
            for p in all_preds
            if p.processed_at
            and p.processed_at.month == now.month
            and p.processed_at.year == now.year
        )
        stats.points_this_year = sum(
            (p.points_earned or 0)
            for p in all_preds
            if p.processed_at and p.processed_at.year == now.year
        )

        await uow.commit()

    async def _check_user_achievements(
        self,
        uow: UnitOfWorkConnection,
        prediction_repo: PredictionRepository,
        achievement_repo: AchievementRepository,
        user_id: UUID,
    ):
        """
        Verifica e desbloqueia conquistas para um usuário.
        Processo independente da pontuação - executado após consolidação dos stats.
        """
        stats = await prediction_repo.get_user_stats(user_id)
        if not stats:
            return

        all_preds = await prediction_repo.get_all_processed_for_user(user_id)

        await self._check_achievements(achievement_repo, user_id, stats, all_preds)

    async def _update_event_leaderboard(
        self,
        uow: UnitOfWorkConnection,
        prediction_repo: PredictionRepository,
        user_id: UUID,
        event_id: UUID,
    ):
        lb = await prediction_repo.get_or_create_event_leaderboard(user_id, event_id)

        event_preds = await prediction_repo.get_user_predictions_for_event(
            user_id, event_id
        )
        processed = [p for p in event_preds if p.processed_at is not None]

        lb.total_points = sum(p.points_earned or 0 for p in processed)
        lb.correct_winners = sum(1 for p in processed if p.is_winner_correct)
        lb.correct_methods = sum(1 for p in processed if p.is_method_correct)
        lb.correct_rounds = sum(1 for p in processed if p.is_round_correct)
        lb.total_predictions = len(processed)

        await uow.commit()

    async def _check_achievements(
        self,
        achievement_repo: AchievementRepository,
        user_id: UUID,
        stats: UserStats,
        all_preds: List[Prediction],
    ):
        available = await achievement_repo.get_available_for_user(user_id)

        streak_wins = 0
        for p in all_preds:
            if p.is_winner_correct:
                streak_wins += 1
            else:
                break

        perfect_events = {}
        for p in all_preds:
            if p.event_id:
                if p.event_id not in perfect_events:
                    perfect_events[p.event_id] = {"correct": 0, "total": 0}
                perfect_events[p.event_id]["total"] += 1
                if p.is_winner_correct:
                    perfect_events[p.event_id]["correct"] += 1

        has_perfect_event = any(
            ev["total"] >= 3 and ev["correct"] == ev["total"]
            for ev in perfect_events.values()
        )

        for ach in available:
            unlocked = False

            if ach.code == "FIRST_PREDICTION" and stats.total_predictions >= 1:
                unlocked = True
            elif ach.code == "PREDICTIONS_10" and stats.total_predictions >= 10:
                unlocked = True
            elif ach.code == "PREDICTIONS_50" and stats.total_predictions >= 50:
                unlocked = True
            elif ach.code == "PREDICTIONS_100" and stats.total_predictions >= 100:
                unlocked = True
            elif ach.code == "STREAK_3" and streak_wins >= 3:
                unlocked = True
            elif ach.code == "STREAK_5" and streak_wins >= 5:
                unlocked = True
            elif ach.code == "STREAK_10" and streak_wins >= 10:
                unlocked = True
            elif ach.code == "PERFECT_EVENT" and has_perfect_event:
                unlocked = True
            elif ach.code == "UNDERDOG_KING" and stats.underdog_bonus_points >= 10:
                unlocked = True
            elif ach.code == "POINTS_100" and stats.total_points >= 100:
                unlocked = True
            elif ach.code == "POINTS_500" and stats.total_points >= 500:
                unlocked = True

            if unlocked:
                await achievement_repo.unlock_achievement(user_id, ach.id)
                logger.info(f"User {user_id} unlocked achievement: {ach.name}")
