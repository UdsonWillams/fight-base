import uuid
from unittest.mock import AsyncMock

import pytest

from app.database.models.base import Fighter
from app.services.domain.fight_simulation import FightSimulationService, FightSimulationResult


def make_fighter(
    name="Test Fighter",
    striking=50,
    grappling=50,
    defense=50,
    stamina=50,
    speed=50,
    strategy=50,
    wins=0,
    losses=0,
    draws=0,
    slpm=4.0,
    sapm=3.0,
    td_avg=1.5,
    td_def=60.0,
    sub_avg=0.5,
    str_def=55.0,
    str_acc=45.0,
) -> Fighter:
    return Fighter(
        id=uuid.uuid4(),
        name=name,
        striking=striking,
        grappling=grappling,
        defense=defense,
        stamina=stamina,
        speed=speed,
        strategy=strategy,
        wins=wins,
        losses=losses,
        draws=draws,
        slpm=slpm,
        sapm=sapm,
        td_avg=td_avg,
        td_def=td_def,
        sub_avg=sub_avg,
        str_def=str_def,
        str_acc=str_acc,
        is_real=False,
        creator_id=uuid.uuid4(),
    )


class TestFightSimulationAlgorithm:
    """Testes unitários do algoritmo core de simulação (sem DB)"""

    def setup_method(self):
        self.service = FightSimulationService(
            fighter_repo=AsyncMock(),
            simulation_repo=AsyncMock(),
        )

    def test_run_simulation_decision_winner_by_total_points(self):
        """Decision: vencedor = maior pontuação total acumulada"""
        f1 = make_fighter(name="Fighter A", striking=80, grappling=50, defense=60)
        f2 = make_fighter(name="Fighter B", striking=40, grappling=40, defense=40)

        for _ in range(20):
            result = self.service._run_fight_simulation(f1, f2, rounds=3)
            assert result.winner_id is not None
            assert result.result_type in ("KO", "Submission", "Decision")
            if result.result_type == "Decision":
                if result.fighter1_total_points > result.fighter2_total_points:
                    assert result.winner_id == f1.id
                elif result.fighter2_total_points > result.fighter1_total_points:
                    assert result.winner_id == f2.id

    def test_run_simulation_ko_winner_is_last_round_dominant(self):
        """KO/Submission: vencedor = dominante do último round simulado"""
        f1 = make_fighter(name="Dominant KO", striking=90, grappling=80, slpm=8.0, sapm=1.0)
        f2 = make_fighter(name="Weak Fighter", striking=10, grappling=10, slpm=1.0, sapm=8.0)

        ko_count = 0
        for _ in range(30):
            result = self.service._run_fight_simulation(f1, f2, rounds=3)
            if result.result_type in ("KO", "Submission"):
                ko_count += 1
                last_round = result.round_details[-1]
                dominant_name = last_round["dominant_fighter"]
                winner_name = f1.name if result.winner_id == f1.id else f2.name
                assert winner_name == dominant_name, (
                    f"KO/Sub: winner ({winner_name}) must be "
                    f"last round dominant ({dominant_name})"
                )

        assert ko_count > 0, "Should have at least one KO/Submission in 30 sims"

    def test_finish_round_less_than_total_rounds(self):
        """finish_round < rounds para KO/Submission (quando rounds > 1)"""
        f1 = make_fighter(name="F1", striking=80, grappling=80)
        f2 = make_fighter(name="F2", striking=20, grappling=20)

        for _ in range(30):
            result = self.service._run_fight_simulation(f1, f2, rounds=3)
            if result.result_type in ("KO", "Submission"):
                assert result.finish_round is not None
                assert result.finish_round <= 3

    def test_equal_fighters_handled(self):
        """Lutadores idênticos não causam erro"""
        f1 = make_fighter(name="Clone A")
        f2 = make_fighter(name="Clone B")

        for _ in range(10):
            result = self.service._run_fight_simulation(f1, f2, rounds=3)
            assert result.winner_id in (f1.id, f2.id)
            assert result.result_type in ("KO", "Submission", "Decision")

    def test_fighter_power_calculation(self):
        f = make_fighter(striking=80, grappling=60, defense=70, stamina=50, speed=90, strategy=40)

        striking_power = self.service._calculate_fighter_power(f, "striking")
        assert striking_power == 80 * 0.5 + 90 * 0.3 + 70 * 0.2

        grappling_power = self.service._calculate_fighter_power(f, "grappling")
        assert grappling_power == 60 * 0.5 + 50 * 0.3 + 40 * 0.2

        overall = self.service._calculate_fighter_power(f, "overall")
        assert overall == (80 + 60 + 70 + 50 + 90 + 40) / 6

    @pytest.mark.asyncio
    async def test_legacy_probability_includes_draws(self):
        f1 = make_fighter(name="F1", wins=10, losses=5, draws=3)
        f2 = make_fighter(name="F2", wins=5, losses=10, draws=1)

        with pytest.MonkeyPatch.context() as mp:
            import app.services.domain.fight_simulation as sim_mod
            mp.setattr(sim_mod.ml_prediction_service, "predict_winner_from_model", AsyncMock(return_value=None))

            prob1, prob2 = await self.service.calculate_win_probability(f1, f2)

        assert prob1 > prob2

    def test_predict_result_type_sums_to_100(self):
        f1 = make_fighter(name="Striker", striking=90, grappling=20)
        f2 = make_fighter(name="Grappler", striking=20, grappling=90)

        result_types = self.service.predict_result_type(f1, f2)
        total = result_types["ko"] + result_types["submission"] + result_types["decision"]
        assert abs(total - 100) < 0.5

    def test_simulation_result_dataclass(self):
        result = FightSimulationResult(
            winner_id=uuid.uuid4(),
            result_type="KO",
            finish_round=2,
            rounds=3,
            fighter1_total_points=10.0,
            fighter2_total_points=8.0,
            round_details=[{"round_number": 1, "events": []}],
        )
        assert result.winner_id is not None
        assert result.result_type == "KO"
        assert result.finish_round == 2
        assert result.fighter1_total_points == 10.0


class TestSimulateRound:
    """Testes do método _simulate_round"""

    def setup_method(self):
        self.service = FightSimulationService(
            fighter_repo=AsyncMock(),
            simulation_repo=AsyncMock(),
        )

    def test_round_returns_expected_structure(self):
        f1 = make_fighter(name="F1", slpm=5.0, td_avg=2.0, sub_avg=1.0, str_def=60, td_def=60)
        f2 = make_fighter(name="F2", slpm=3.0, td_avg=1.0, sub_avg=0.5, str_def=50, td_def=50)

        result = self.service._simulate_round(f1, f2, 1)

        assert "round_number" in result
        assert "fighter1_points" in result
        assert "fighter2_points" in result
        assert "dominant_fighter" in result
        assert "events" in result
        assert result["round_number"] == 1
        assert isinstance(result["fighter1_points"], (int, float))
        assert isinstance(result["fighter2_points"], (int, float))

    def test_round_points_vary_with_randomness(self):
        f1 = make_fighter(name="F1")
        f2 = make_fighter(name="F2")

        results = set()
        for _ in range(20):
            r = self.service._simulate_round(f1, f2, 1)
            results.add(round(r["fighter1_points"], 2))

        assert len(results) > 1, "Randomness should produce varying points"


class TestPredictionScoring:
    """Testes do algoritmo de scoring de palpites"""

    def test_underdog_bonus(self):
        from app.services.domain.prediction import PredictionService
        from app.database.models.base import Fight, Prediction

        service = PredictionService(
            uow=AsyncMock(),
            prediction_repo=AsyncMock(),
            achievement_repo=AsyncMock(),
        )

        fight = Fight(fighter1_id=uuid.uuid4(), fighter2_id=uuid.uuid4(),
                       winner_id=None, fighter1_probability=None, fighter2_probability=None)
        pred = Prediction()

        assert service._calculate_underdog_bonus(fight, pred) == 0

        fight.winner_id = fight.fighter1_id
        fight.fighter1_probability = 0.25
        assert service._calculate_underdog_bonus(fight, pred) == 3

        fight.fighter1_probability = 0.35
        assert service._calculate_underdog_bonus(fight, pred) == 2

        fight.fighter1_probability = 0.45
        assert service._calculate_underdog_bonus(fight, pred) == 1

        fight.fighter1_probability = 0.55
        assert service._calculate_underdog_bonus(fight, pred) == 0
