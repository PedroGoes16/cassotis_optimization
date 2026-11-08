import pytest

from cassotis_optimization.decision.normalization import normalize_rows


def test_normalization_maps_minimum_to_zero_and_maximum_to_one() -> None:
    rows, scale = normalize_rows([{"a": 10, "b": 4}, {"a": 20, "b": 4}], ("a", "b"))
    assert rows == [{"a": 0.0, "b": 0.0}, {"a": 1.0, "b": 0.0}]
    assert scale.minimum == {"a": 10.0, "b": 4.0}
    assert scale.maximum == {"a": 20.0, "b": 4.0}


def test_normalization_requires_alternatives() -> None:
    with pytest.raises(ValueError):
        normalize_rows([], ("a",))
