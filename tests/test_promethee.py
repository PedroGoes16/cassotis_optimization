import pytest

from cassotis_optimization.decision.promethee import promethee_ii


def test_promethee_ranks_dominating_alternative_first() -> None:
    rows = [
        {"c1": 0.0, "c2": 0.0},
        {"c1": 0.5, "c2": 0.5},
        {"c1": 1.0, "c2": 1.0},
    ]
    result = promethee_ii(
        rows,
        {"c1": 0.5, "c2": 0.5},
        {"c1": 0.0, "c2": 0.0},
        {"c1": 0.2, "c2": 0.2},
    )
    assert result.ranking == (0, 1, 2)
    assert result.net_flow[0] > result.net_flow[1] > result.net_flow[2]


def test_promethee_indifference_threshold_ignores_small_difference() -> None:
    result = promethee_ii(
        [{"c": 0.0}, {"c": 0.04}],
        {"c": 1.0},
        {"c": 0.05},
        {"c": 0.2},
    )
    assert result.net_flow == pytest.approx((0.0, 0.0))
