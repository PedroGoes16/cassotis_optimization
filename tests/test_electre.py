from cassotis_optimization.decision.electre import electre_iii


def test_electre_finds_undominated_maximal_alternative() -> None:
    rows = [
        {"c1": 0.0, "c2": 0.0},
        {"c1": 0.5, "c2": 0.5},
        {"c1": 1.0, "c2": 1.0},
    ]
    result = electre_iii(
        rows,
        {"c1": 0.5, "c2": 0.5},
        {"c1": 0.05, "c2": 0.05},
        {"c1": 0.2, "c2": 0.2},
        {"c1": 0.6, "c2": 0.6},
    )
    assert result.maximal == (0,)
    assert result.ranking[0] == 0


def test_electre_preserves_incomparability_under_opposed_vetoes() -> None:
    rows = [{"c1": 0.0, "c2": 1.0}, {"c1": 1.0, "c2": 0.0}]
    result = electre_iii(
        rows,
        {"c1": 0.5, "c2": 0.5},
        {"c1": 0.05, "c2": 0.05},
        {"c1": 0.2, "c2": 0.2},
        {"c1": 0.6, "c2": 0.6},
    )
    assert result.maximal == (0, 1)
    assert result.incomparable_pairs == ((0, 1),)
