from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.database.models.base import Prediction
from app.schemas.domain.predictions.input import CreatePrediction, UpdatePrediction
from app.services.domain.prediction import PredictionService


class TestCreatePrediction:
    @pytest.mark.asyncio
    async def test_creates_new_prediction(self):
        mock_repo = AsyncMock()
        mock_repo.get_prediction_by_user_and_fight = AsyncMock(return_value=None)

        payload = CreatePrediction(
            fight_id=uuid4(),
            event_id=uuid4(),
            predicted_winner_id=uuid4(),
        )
        created = Prediction(id=uuid4(), user_id=uuid4(), **payload.model_dump())
        mock_repo.create = AsyncMock(return_value=created)

        service = PredictionService(MagicMock(), mock_repo, AsyncMock())
        user_id = uuid4()
        result = await service.create_prediction(user_id, payload)

        assert result == created
        mock_repo.get_prediction_by_user_and_fight.assert_called_once_with(
            user_id, payload.fight_id
        )
        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_already_predicted(self):
        mock_repo = AsyncMock()
        mock_repo.get_prediction_by_user_and_fight = AsyncMock(
            return_value=MagicMock(spec=Prediction)
        )

        payload = CreatePrediction(
            fight_id=uuid4(),
            event_id=uuid4(),
            predicted_winner_id=uuid4(),
        )

        service = PredictionService(MagicMock(), mock_repo, AsyncMock())
        with pytest.raises(ValueError, match="já fez um palpite"):
            await service.create_prediction(uuid4(), payload)

    @pytest.mark.asyncio
    async def test_creates_prediction_with_draw(self):
        mock_repo = AsyncMock()
        mock_repo.get_prediction_by_user_and_fight = AsyncMock(return_value=None)

        payload = CreatePrediction(
            fight_id=uuid4(),
            event_id=uuid4(),
            predicted_winner_id=None,
            predicted_method_id=None,
            predicted_round=None,
        )
        created = Prediction(id=uuid4(), user_id=uuid4(), **payload.model_dump())
        mock_repo.create = AsyncMock(return_value=created)

        service = PredictionService(MagicMock(), mock_repo, AsyncMock())
        result = await service.create_prediction(uuid4(), payload)

        assert result.predicted_winner_id is None


class TestUpdatePrediction:
    @pytest.mark.asyncio
    async def test_updates_prediction(self):
        user_id = uuid4()
        pred_id = uuid4()
        existing = Prediction(id=pred_id, user_id=user_id, processed_at=None)

        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=existing)

        updated_data = {"predicted_round": 3}
        updated = Prediction(id=pred_id, user_id=user_id, predicted_round=3)
        mock_repo.update = AsyncMock(return_value=updated)

        service = PredictionService(MagicMock(), mock_repo, AsyncMock())
        result = await service.update_prediction(
            user_id, pred_id, UpdatePrediction(predicted_round=3)
        )

        assert result.predicted_round == 3
        mock_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_not_found(self):
        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)

        service = PredictionService(MagicMock(), mock_repo, AsyncMock())
        with pytest.raises(ValueError, match="não encontrado"):
            await service.update_prediction(
                uuid4(), uuid4(), UpdatePrediction()
            )

    @pytest.mark.asyncio
    async def test_raises_when_not_owner(self):
        user_id = uuid4()
        existing = Prediction(id=uuid4(), user_id=uuid4())

        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=existing)

        service = PredictionService(MagicMock(), mock_repo, AsyncMock())
        with pytest.raises(ValueError, match="não encontrado"):
            await service.update_prediction(
                user_id, existing.id, UpdatePrediction()
            )

    @pytest.mark.asyncio
    async def test_raises_when_already_processed(self):
        import datetime
        user_id = uuid4()
        existing = Prediction(
            id=uuid4(),
            user_id=user_id,
            processed_at=datetime.datetime.now(datetime.timezone.utc),
        )

        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=existing)

        service = PredictionService(MagicMock(), mock_repo, AsyncMock())
        with pytest.raises(ValueError, match="já foi processado"):
            await service.update_prediction(
                user_id, existing.id, UpdatePrediction()
            )
