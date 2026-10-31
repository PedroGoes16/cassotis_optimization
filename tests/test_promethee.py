"""Testes matemáticos e integrações condicionais da D026."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from cassotis_optimization.mcda.promethee import (
    _compare_flows,
    promethee_i_ii,
    v_shape_with_indifference,
)

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ("f1", "f2", "f3", "c4")
W = {"f1": 0.4, "f2": 0.3, "f3": 0.2, "c4": 0.1}
CONFIG = {c: {"function": "v_shape_with_indifference",
              "q_fraction_of_observed_range": 0.1,
              "p_fraction_of_observed_range": 0.5} for c in CRITERIA}


def _row(alt_id, **kwargs):
    return {"alternative_id": alt_id, **{c: kwargs.get(c, 1.0) for c in CRITERIA}}


def test_preference_zero_linear_full():
    assert v_shape_with_indifference(-1, 1, 3) == 0
    assert v_shape_with_indifference(1, 1, 3) == 0
    assert v_shape_with_indifference(2, 1, 3) == pytest.approx(0.5)
    assert v_shape_with_indifference(3, 1, 3) == 1
    assert v_shape_with_indifference(8, 1, 3) == 1


def test_preference_invalid_thresholds():
    with pytest.raises(ValueError):
        v_shape_with_indifference(1, 2, 2)
    with pytest.raises(ValueError):
        v_shape_with_indifference(1, -1, 2)
    with pytest.raises(ValueError):
        v_shape_with_indifference(float("inf"), 0, 1)


def test_two_opposite_alternatives_derive_weighted_flows():
    data = [_row("A", f1=0, f2=10), _row("B", f1=10, f2=0)]
    summary, ranking, pairs = promethee_i_ii(data, W, CONFIG)
    a, b = (next(x for x in ranking if x["alternative_id"] == k) for k in ("A", "B"))
    assert a["phi_positive"] == pytest.approx(0.4)
    assert a["phi_negative"] == pytest.approx(0.3)
    assert a["phi_net"] == pytest.approx(0.1)
    assert b["phi_net"] == pytest.approx(-0.1)
    # Com apenas dois perfis, o fluxo favoravel de A e o desfavoravel de B
    # se correspondem; neste exemplo I tambem prefere A.
    assert pairs[0]["relation_promethee_i"] == "a_preferida"
    assert summary["promethee_i_pair_types"]["incomparaveis"] == 0
    assert ranking[0]["alternative_id"] == "A"


def test_identical_alternatives_are_indifferent_and_tied():
    data = [_row("B"), _row("A")]
    summary, ranking, pairs = promethee_i_ii(data, W, CONFIG)
    assert [x["alternative_id"] for x in ranking] == ["A", "B"]
    assert all(x["rank_promethee_ii"] == 1 for x in ranking)
    assert all(x["phi_net"] == 0 for x in ranking)
    assert pairs[0]["relation_promethee_i"] == "indiferentes"
    assert summary["promethee_i_unbeaten"] == ["A", "B"]


def test_strict_dominance_recognized_in_both_variants():
    data = [_row("A", f1=0, f2=0, f3=0, c4=0),
            _row("B", f1=10, f2=10, f3=10, c4=10)]
    summary, ranking, pairs = promethee_i_ii(data, W, CONFIG)
    assert ranking[0]["alternative_id"] == "A"
    assert ranking[0]["phi_positive"] == pytest.approx(1)
    assert ranking[0]["phi_negative"] == pytest.approx(0)
    assert pairs[0]["relation_promethee_i"] == "a_preferida"
    assert summary["promethee_i_unbeaten"] == ["A"]


def test_sum_net_flows_zero_and_bounds():
    data = [_row("A", f1=2, f2=3, f3=4, c4=1),
            _row("B", f1=1, f2=5, f3=2, c4=5),
            _row("C", f1=4, f2=1, f3=6, c4=2)]
    summary, ranking, pairs = promethee_i_ii(data, W, CONFIG)
    assert len(pairs) == 3
    assert sum(x["phi_net"] for x in ranking) == pytest.approx(0, abs=1e-13)
    for row in ranking:
        assert 0 <= row["phi_positive"] <= 1
        assert 0 <= row["phi_negative"] <= 1
        assert -1 <= row["phi_net"] <= 1
    assert summary["unordered_pairs"] == 3


def test_scaling_one_criterion_keeps_results_with_relative_thresholds():
    data = [_row("A", f1=1, f2=9, f3=4, c4=1),
            _row("B", f1=6, f2=2, f3=7, c4=5),
            _row("C", f1=4, f2=5, f3=1, c4=3)]
    data_scaled = [{**item, "f1": item["f1"] * 2000} for item in data]
    _, a, _ = promethee_i_ii(data, W, CONFIG)
    _, b, _ = promethee_i_ii(data_scaled, W, CONFIG)
    assert [x["alternative_id"] for x in a] == [x["alternative_id"] for x in b]
    assert [x["phi_net"] for x in a] == pytest.approx([x["phi_net"] for x in b])


def test_rejects_bad_params_weights_and_duplicate_ids():
    data = [_row("A"), _row("B", f1=2)]
    config = {k: dict(v) for k, v in CONFIG.items()}
    config["f1"]["p_fraction_of_observed_range"] = 0.05
    with pytest.raises(ValueError, match="Limiares"):
        promethee_i_ii(data, W, config)
    with pytest.raises(ValueError, match="somar 1"):
        promethee_i_ii(data, {**W, "f1": .5}, CONFIG)
    with pytest.raises(ValueError, match="duplicados"):
        promethee_i_ii([data[0], data[0]], W, CONFIG)


def test_partial_comparison_cases():
    assert _compare_flows(.8, .2, .6, .4) == "a_preferida"
    assert _compare_flows(.2, .5, .5, .1) == "b_preferida"
    assert _compare_flows(.7, .5, .6, .4) == "incomparaveis"
    assert _compare_flows(.7, .1, .7, .1) == "indiferentes"


def test_outputs_do_not_depend_on_row_order():
    data = [_row("C", f1=2, f2=3), _row("A", f1=4, f2=2), _row("B", f1=1, f2=4)]
    _, first, _ = promethee_i_ii(data, W, CONFIG)
    _, second, _ = promethee_i_ii(list(reversed(data)), W, CONFIG)
    assert [x["alternative_id"] for x in first] == [x["alternative_id"] for x in second]
    assert [x["phi_net"] for x in first] == pytest.approx([x["phi_net"] for x in second])


def test_official_checkout_when_present():
    """No checkout do usuário: verifica os três primeiros e as contagens oficiais.

    No pacote distribuído isoladamente, não é gerada uma matriz 'oficial' fictícia.
    """
    matrix_file = ROOT / "results/mcda/matriz_decisao.csv"
    weights_file = ROOT / "results/mcda/pesos_ahp.json"
    params_file = ROOT / "data/parametros_promethee.json"
    if not matrix_file.is_file() or not weights_file.is_file() or not params_file.is_file():
        pytest.skip("Integração depende do checkout oficial com D023 e D024.")
    with matrix_file.open(encoding="utf-8", newline="") as handle:
        matrix = list(csv.DictReader(handle))
    ahp = json.loads(weights_file.read_text(encoding="utf-8"))
    params = json.loads(params_file.read_text(encoding="utf-8"))
    assert len(matrix) == 91
    summary, ranked, pairs = promethee_i_ii(matrix, ahp["weights"],
                                             params["preference_parameters"])
    assert [x["alternative_id"] for x in ranked[:3]] == ["A020", "A016", "A002"]
    assert ranked[0]["phi_net"] == pytest.approx(0.5292317868364012, abs=1e-10)
    assert summary["promethee_i_pair_types"]["incomparaveis"] == 198
    assert len(pairs) == 4095


def test_real_incomparability_even_though_ii_orders():
    # Quatro alternativas com preferencias cruzadas.
    data = [
        _row("A0", f1=7, f2=4, f3=3, c4=1),
        _row("A1", f1=9, f2=5, f3=4, c4=6),
        _row("A2", f1=6, f2=3, f3=6, c4=1),
        _row("A3", f1=6, f2=6, f3=0, c4=7),
    ]
    params = {k: {**v, "q_fraction_of_observed_range": 0.01,
                  "p_fraction_of_observed_range": 0.25} for k, v in CONFIG.items()}
    _, ranking, pairs = promethee_i_ii(data, W, params)
    incomparables = {(p["a"], p["b"]) for p in pairs
                     if p["relation_promethee_i"] == "incomparaveis"}
    assert ("A0", "A3") in incomparables
    # PROMETHEE II sempre pode comparar seus fluxos líquidos.
    a0 = next(x for x in ranking if x["alternative_id"] == "A0")
    a3 = next(x for x in ranking if x["alternative_id"] == "A3")
    assert abs(a0["phi_net"] - a3["phi_net"]) > 1e-12
