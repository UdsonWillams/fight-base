from app.services.domain.fighter import _estimate_ml_stats_from_attributes, _extract_last_fight_date


class TestEstimateMLStats:
    def test_all_stats_calculated(self):
        stats = _estimate_ml_stats_from_attributes(
            striking=50, grappling=50, defense=50, stamina=50, speed=50
        )
        assert "slpm" in stats
        assert "str_acc" in stats
        assert "sapm" in stats
        assert "str_def" in stats
        assert "td_avg" in stats
        assert "td_acc" in stats
        assert "td_def" in stats
        assert "sub_avg" in stats

    def test_high_striking_high_slpm(self):
        low = _estimate_ml_stats_from_attributes(striking=10, grappling=50, defense=50, stamina=50, speed=50)
        high = _estimate_ml_stats_from_attributes(striking=90, grappling=50, defense=50, stamina=50, speed=50)
        assert high["slpm"] > low["slpm"]

    def test_high_defense_low_sapm(self):
        low = _estimate_ml_stats_from_attributes(striking=50, grappling=50, defense=90, stamina=50, speed=50)
        high = _estimate_ml_stats_from_attributes(striking=50, grappling=50, defense=10, stamina=50, speed=50)
        assert low["sapm"] < high["sapm"]

    def test_high_defense_high_str_def(self):
        low = _estimate_ml_stats_from_attributes(striking=50, grappling=50, defense=10, stamina=50, speed=50)
        high = _estimate_ml_stats_from_attributes(striking=50, grappling=50, defense=90, stamina=50, speed=50)
        assert high["str_def"] > low["str_def"]

    def test_high_grappling_high_td_avg(self):
        low = _estimate_ml_stats_from_attributes(striking=50, grappling=10, defense=50, stamina=50, speed=50)
        high = _estimate_ml_stats_from_attributes(striking=50, grappling=90, defense=50, stamina=50, speed=50)
        assert high["td_avg"] > low["td_avg"]

    def test_submission_wins_increase_sub_avg(self):
        no_subs = _estimate_ml_stats_from_attributes(
            striking=50, grappling=50, defense=50, stamina=50, speed=50,
            submission_wins=0, total_fights=10
        )
        many_subs = _estimate_ml_stats_from_attributes(
            striking=50, grappling=50, defense=50, stamina=50, speed=50,
            submission_wins=8, total_fights=10
        )
        assert many_subs["sub_avg"] > no_subs["sub_avg"]

    def test_values_not_capped_above_zero(self):
        stats = _estimate_ml_stats_from_attributes(
            striking=100, grappling=100, defense=100, stamina=100, speed=100,
            submission_wins=10, total_fights=10
        )
        for key, value in stats.items():
            assert isinstance(value, (int, float))
            assert value >= 0

    def test_zero_attributes_produces_non_negative(self):
        stats = _estimate_ml_stats_from_attributes(
            striking=0, grappling=0, defense=0, stamina=0, speed=0
        )
        for key, value in stats.items():
            assert value >= 0


class TestExtractLastFightDate:
    def test_returns_most_recent_date(self):
        cartel = [
            {"opponent": "A", "date": "2024-01-15", "result": "W"},
            {"opponent": "B", "date": "2024-06-20", "result": "L"},
            {"opponent": "C", "date": "2024-03-10", "result": "W"},
        ]
        result = _extract_last_fight_date(cartel)
        assert result == "2024-06-20"

    def test_empty_cartel_returns_none(self):
        assert _extract_last_fight_date([]) is None

    def test_none_cartel_returns_none(self):
        assert _extract_last_fight_date(None) is None

    def test_entries_without_date_skipped(self):
        cartel = [
            {"opponent": "A", "result": "W"},
            {"opponent": "B", "date": "2024-01-15", "result": "L"},
        ]
        result = _extract_last_fight_date(cartel)
        assert result == "2024-01-15"

    def test_single_entry(self):
        cartel = [{"date": "2023-12-01"}]
        assert _extract_last_fight_date(cartel) == "2023-12-01"
