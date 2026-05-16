from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.database.models.base import Fight, Prediction
from app.services.domain.prediction import PredictionService


class TestCalculateUnderdogBonus:
    def setup_method(self):
        self.service = PredictionService(MagicMock(), AsyncMock(), AsyncMock())

    def test_no_winner_returns_zero(self):
        fight = Fight(winner_id=None)
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 0

    def test_fighter1_heavy_underdog(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.20,
            fighter2_probability=0.80,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 3

    def test_fighter1_moderate_underdog(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.35,
            fighter2_probability=0.65,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 2

    def test_fighter1_light_underdog(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.45,
            fighter2_probability=0.55,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 1

    def test_fighter1_favorite_no_bonus(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.60,
            fighter2_probability=0.40,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 0

    def test_fighter2_heavy_underdog(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.75,
            fighter2_probability=0.25,
        )
        fight.winner_id = fight.fighter2_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 3

    def test_fighter2_favorite_no_bonus(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.40,
            fighter2_probability=0.60,
        )
        fight.winner_id = fight.fighter2_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 0

    def test_probability_none_defaults_to_fifty(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=None,
            fighter2_probability=None,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 0

    def test_boundary_30_percent(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.30,
            fighter2_probability=0.70,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 2

    def test_boundary_40_percent(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.40,
            fighter2_probability=0.60,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 1

    def test_boundary_50_percent(self):
        fight = Fight(
            fighter1_id=uuid4(),
            fighter2_id=uuid4(),
            winner_id=None,
            fighter1_probability=0.50,
            fighter2_probability=0.50,
        )
        fight.winner_id = fight.fighter1_id
        pred = Prediction()
        assert self.service._calculate_underdog_bonus(fight, pred) == 0


class TestCalculateAndUpdatePrediction:
    def setup_method(self):
        self.service = PredictionService(MagicMock(), AsyncMock(), AsyncMock())

    def test_correct_winner_only(self):
        f1_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=f1_id,
                       fighter1_probability=0.6, fighter2_probability=0.4,
                       finish_round=2)
        pred = Prediction(predicted_winner_id=f1_id, predicted_method_id=None, predicted_round=1)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.is_method_correct is False
        assert pred.is_round_correct is False
        assert pred.points_earned == 3
        assert pred.processed_at is not None

    def test_correct_winner_with_underdog_bonus(self):
        f1_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=f1_id,
                       fighter1_probability=0.25, fighter2_probability=0.75,
                       finish_round=1)
        pred = Prediction(predicted_winner_id=f1_id, predicted_round=2)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.points_earned == 6

    def test_wrong_winner_zero_points(self):
        f1_id = uuid4()
        f2_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=f2_id, winner_id=f1_id)
        pred = Prediction(predicted_winner_id=f2_id)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is False
        assert pred.is_method_correct is False
        assert pred.is_round_correct is False
        assert pred.points_earned == 0

    def test_correct_winner_and_method(self):
        f1_id = uuid4()
        method_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=f1_id,
                       fighter1_probability=0.55, fighter2_probability=0.45,
                       finish_round=3)
        fight.method_id = method_id
        pred = Prediction(predicted_winner_id=f1_id, predicted_method_id=method_id, predicted_round=1)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.is_method_correct is True
        assert pred.is_round_correct is False
        assert pred.points_earned == 5

    def test_correct_winner_and_round(self):
        f1_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=f1_id,
                       fighter1_probability=0.7, fighter2_probability=0.3, finish_round=2)
        pred = Prediction(predicted_winner_id=f1_id, predicted_method_id=None, predicted_round=2)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.is_round_correct is True
        assert pred.points_earned == 4

    def test_correct_all_perfect_score(self):
        f1_id = uuid4()
        method_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=f1_id,
                       fighter1_probability=0.15, fighter2_probability=0.85, finish_round=1)
        fight.method_id = method_id
        pred = Prediction(predicted_winner_id=f1_id, predicted_method_id=method_id, predicted_round=1)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.is_method_correct is True
        assert pred.is_round_correct is True
        assert pred.points_earned == 9

    def test_wrong_method_correct_winner_no_method_points(self):
        f1_id = uuid4()
        method_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=f1_id,
                       fighter1_probability=0.6, fighter2_probability=0.4,
                       finish_round=1)
        fight.method_id = method_id
        pred = Prediction(predicted_winner_id=f1_id, predicted_method_id=uuid4(), predicted_round=2)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.is_method_correct is False
        assert pred.is_round_correct is False
        assert pred.points_earned == 3

    def test_wrong_round_correct_winner_no_round_points(self):
        f1_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=f1_id,
                       fighter1_probability=0.6, fighter2_probability=0.4, finish_round=3)
        pred = Prediction(predicted_winner_id=f1_id, predicted_method_id=None, predicted_round=1)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.is_round_correct is False
        assert pred.points_earned == 3

    def test_draw_scenario_both_none_counts_as_correct(self):
        f1_id = uuid4()
        fight = Fight(fighter1_id=f1_id, fighter2_id=uuid4(), winner_id=None,
                       fighter1_probability=0.6, fighter2_probability=0.4,
                       finish_round=1)
        pred = Prediction(predicted_winner_id=None, predicted_round=None)

        self.service._calculate_and_update_prediction(pred, fight)

        assert pred.is_winner_correct is True
        assert pred.points_earned == 3
