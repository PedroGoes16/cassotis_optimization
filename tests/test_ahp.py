"""D024: verificações independentes dos seis julgamentos AHP."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import numpy as np
import pytest

from cassotis_optimization.mcda.ahp import calculate_ahp, pairwise_matrix

CONFIG = Path(__file__).resolve().parents[1] / "data" / "preferencias_ahp.json"


@pytest.fixture
def prefs() -> dict:
    return json.loads(CONFIG.read_text(encoding="utf-8"))


def test_matrix_exactly_matches_user_judgments(prefs: dict) -> None:
    ids, a = pairwise_matrix(prefs)
    assert ids == ("f1", "f2", "f3", "c4")
    expected = np.array([
        [1, 7, 7, 5],
        [1 / 7, 1, 1, 1 / 3],
        [1 / 7, 1, 1, 1 / 3],
        [1 / 5, 3, 3, 1],
    ])
    np.testing.assert_allclose(a, expected, rtol=0, atol=1e-15)
    np.testing.assert_allclose(a * a.T, np.ones((4, 4)), rtol=0, atol=1e-15)


def test_spicelogic_weight_method(prefs: dict) -> None:
    result = calculate_ahp(prefs)
    assert result["weight_method"] == "normalized_column_row_mean"
    assert result["weights"] == pytest.approx({
        "f1": 0.6474358974358975,
        "f2": 0.0782051282051282,
        "f3": 0.0782051282051282,
        "c4": 0.19615384615384618,
    }, abs=1e-12)
    assert sum(result["weights"].values()) == pytest.approx(1.0)
    assert result["weights"]["f2"] == result["weights"]["f3"]
    np.testing.assert_allclose(np.sum(result["normalized_matrix"], axis=0), np.ones(4))


def test_consistency_ratio_uses_principal_eigenvalue(prefs: dict) -> None:
    result = calculate_ahp(prefs)
    assert result["lambda_max"] == pytest.approx(4.07346699345865, abs=1e-10)
    assert result["consistency_index"] == pytest.approx(0.02448899781955, abs=1e-10)
    assert result["consistency_ratio"] == pytest.approx(0.02720999757728, abs=1e-10)
    assert result["consistent"] is True


def test_rejects_missing_or_duplicate_pair(prefs: dict) -> None:
    missing = copy.deepcopy(prefs)
    missing["comparisons"].pop()
    with pytest.raises(ValueError, match="incompletas"):
        pairwise_matrix(missing)
    duplicated = copy.deepcopy(prefs)
    duplicated["comparisons"].append(duplicated["comparisons"][0])
    with pytest.raises(ValueError, match="duplicada"):
        pairwise_matrix(duplicated)


def test_rejects_nonreciprocal_input_or_missing_justification(prefs: dict) -> None:
    wrong = copy.deepcopy(prefs)
    wrong["comparisons"][0]["preferred"] = "other"
    with pytest.raises(ValueError, match="preferência"):
        pairwise_matrix(wrong)
    wrong = copy.deepcopy(prefs)
    wrong["comparisons"][0]["justification"] = ""
    with pytest.raises(ValueError, match="Justificativa"):
        pairwise_matrix(wrong)
    wrong = copy.deepcopy(prefs)
    wrong["comparisons"][3]["preferred"] = "f3"
    with pytest.raises(ValueError, match="Empate"):
        pairwise_matrix(wrong)


def test_consistency_flags_bad_judgments(prefs: dict) -> None:
    wrong = copy.deepcopy(prefs)
    # Ciclo f1 > f2 > f3 > f1 induz CR alto.
    wrong["comparisons"][3].update({"preferred": "f2", "intensity": 9})
    wrong["comparisons"][1].update({"preferred": "f3", "intensity": 9})
    assert calculate_ahp(wrong)["consistent"] is False
