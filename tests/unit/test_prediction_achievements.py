from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.database.models.base import Achievement, Prediction, UserStats
from app.services.domain.prediction import PredictionService


def make_prediction(**kwargs):
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "fight_id": uuid4(),
        "event_id": uuid4(),
        "is_winner_correct": True,
        "is_method_correct": False,
        "is_round_correct": False,
        "points_earned": 3,
        "processed_at": None,
    }
    defaults.update(kwargs)
    return Prediction(**defaults)


def make_achievement(code, name="Test"):
    return Achievement(id=uuid4(), code=code, name=name, description="desc", category="test")


class TestCheckAchievements:
    @pytest.mark.asyncio
    async def test_unlocks_first_prediction(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("FIRST_PREDICTION")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        stats = UserStats(total_predictions=1, total_points=0, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, [])

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlocks_streak_3(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("STREAK_3")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        predictions = [make_prediction(is_winner_correct=True) for _ in range(3)]
        stats = UserStats(total_predictions=3, total_points=9, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, predictions)

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_streak_broken_by_loss(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("STREAK_3")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        predictions = [
            make_prediction(is_winner_correct=False),
            make_prediction(is_winner_correct=True),
            make_prediction(is_winner_correct=True),
        ]
        stats = UserStats(total_predictions=3, total_points=6, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, predictions)

        mock_achievement_repo.unlock_achievement.assert_not_called()

    @pytest.mark.asyncio
    async def test_unlocks_streak_5(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("STREAK_5")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        predictions = [make_prediction(is_winner_correct=True) for _ in range(5)]
        stats = UserStats(total_predictions=5, total_points=15, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, predictions)

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlocks_streak_10(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("STREAK_10")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        predictions = [make_prediction(is_winner_correct=True) for _ in range(10)]
        stats = UserStats(total_predictions=10, total_points=30, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, predictions)

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlocks_predictions_10(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("PREDICTIONS_10")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        stats = UserStats(total_predictions=10, total_points=0, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, [])

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_not_enough_predictions_for_50(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("PREDICTIONS_50")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        stats = UserStats(total_predictions=30, total_points=0, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, [])

        mock_achievement_repo.unlock_achievement.assert_not_called()

    @pytest.mark.asyncio
    async def test_unlocks_underdog_king(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("UNDERDOG_KING")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        stats = UserStats(total_predictions=10, total_points=0, underdog_bonus_points=15)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, [])

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlocks_points_100(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("POINTS_100")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        stats = UserStats(total_predictions=50, total_points=150, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, [])

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlocks_points_500(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("POINTS_500")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        stats = UserStats(total_predictions=100, total_points=600, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, [])

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_unlocks_perfect_event(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("PERFECT_EVENT")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        event_id = uuid4()
        predictions = [
            make_prediction(event_id=event_id, is_winner_correct=True),
            make_prediction(event_id=event_id, is_winner_correct=True),
            make_prediction(event_id=event_id, is_winner_correct=True),
        ]
        stats = UserStats(total_predictions=3, total_points=9, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, predictions)

        mock_achievement_repo.unlock_achievement.assert_called_once()

    @pytest.mark.asyncio
    async def test_perfect_event_requires_min_3_fights(self):
        mock_achievement_repo = AsyncMock()
        achievements = [make_achievement("PERFECT_EVENT")]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        event_id = uuid4()
        predictions = [
            make_prediction(event_id=event_id, is_winner_correct=True),
            make_prediction(event_id=event_id, is_winner_correct=True),
        ]
        stats = UserStats(total_predictions=2, total_points=6, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, predictions)

        mock_achievement_repo.unlock_achievement.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_achievements_unlocked_at_once(self):
        mock_achievement_repo = AsyncMock()
        achievements = [
            make_achievement("FIRST_PREDICTION"),
            make_achievement("STREAK_3"),
        ]
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=achievements)
        mock_achievement_repo.unlock_achievement = AsyncMock()

        predictions = [make_prediction(is_winner_correct=True) for _ in range(3)]
        stats = UserStats(total_predictions=3, total_points=9, underdog_bonus_points=0)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, predictions)

        assert mock_achievement_repo.unlock_achievement.call_count == 2

    @pytest.mark.asyncio
    async def test_no_achievements_if_none_available(self):
        mock_achievement_repo = AsyncMock()
        mock_achievement_repo.get_available_for_user = AsyncMock(return_value=[])
        mock_achievement_repo.unlock_achievement = AsyncMock()

        stats = UserStats(total_predictions=10, total_points=100, underdog_bonus_points=50)

        service = PredictionService(MagicMock(), AsyncMock(), mock_achievement_repo)
        await service._check_achievements(mock_achievement_repo, uuid4(), stats, [])

        mock_achievement_repo.unlock_achievement.assert_not_called()
