"""D027: testes de reproducibilidade e nao mutacao de entradas.

Rodar no checkout oficial (src do projeto disponivel no PYTHONPATH).
"""
from __future__ import annotations

import csv
import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/analyze_promethee_sensitivity.py"
SPEC = importlib.util.spec_from_file_location("analyze_promethee_sensitivity", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

AHW = {"f1": .6474358974358975, "f2": .0782051282051282,
       "f3": .0782051282051282, "c4": .19615384615384615}
PARAMS = MODULE._parameters_at(.01, .25)
PROTOCOL = json.loads((ROOT / "data/protocolo_sensibilidade_promethee.json").read_text())


def fake_matrix():
    """Dados sinteticos apenas para teste de contrato, nunca de resultado oficial."""
    data = []
    for i in range(1, 92):
        data.append({
            "alternative_id": f"A{i:03d}",
            "f1": 59680000 + i * 20000,
            "f2": 3 + (i * 17 % 31) / 7,
            "f3": 2 + (i * 13 % 37) / 9,
            "c4": .28 + (i * 11 % 41) / 200,
        })
    return data


def test_parameter_builder_supports_zero_q_and_rejects_invalid():
    p = MODULE._parameters_at(0, .20)
    assert set(p) == set(MODULE.CRITERIA)
    assert all(v["q_fraction_of_observed_range"] == 0 for v in p.values())
    for q, pref in ((-.01, .2), (.2, .2), (.4, .3), (0, 1.1)):
        with pytest.raises(ValueError):
            MODULE._parameters_at(q, pref)


def test_cost_weight_rescaling_preserves_other_ratios_and_normalization():
    new = MODULE._weights_with_cost_share(AHW, .75)
    assert new["f1"] == pytest.approx(.75)
    assert sum(new.values()) == pytest.approx(1)
    assert new["f2"] / new["c4"] == pytest.approx(AHW["f2"] / AHW["c4"])
    assert AHW["f1"] == pytest.approx(.6474358974358975)
    with pytest.raises(ValueError):
        MODULE._weights_with_cost_share(AHW, 1)


def test_analyze_does_not_mutate_inputs_and_covers_scenarios():
    alts, ws, base, protocol = fake_matrix(), deepcopy(AHW), deepcopy(PARAMS), deepcopy(PROTOCOL)
    old = deepcopy((alts, ws, base, protocol))
    thresholds, weights, summary = MODULE.analyze(alts, ws, base, protocol)
    assert len(thresholds) == 7
    assert len(weights) == 7
    assert summary["threshold_scenario_count"] == 7
    assert summary["weight_scenario_count"] == 7
    assert thresholds[1]["q_frac"] == pytest.approx(.01)
    assert thresholds[1]["p_frac"] == pytest.approx(.25)
    assert (alts, ws, base, protocol) == old


def test_refuses_baseline_drift():
    config = deepcopy(PARAMS)
    config["c4"]["p_fraction_of_observed_range"] = .24
    with pytest.raises(ValueError, match="baseline"):
        MODULE.analyze(fake_matrix(), AHW, config, PROTOCOL)


def test_refuses_incomplete_matrix():
    with pytest.raises(ValueError, match="91"):
        MODULE.analyze(fake_matrix()[:90], AHW, PARAMS, PROTOCOL)


def test_csv_writer_roundtrip(tmp_path):
    sample = [{"cenario": "L01", "primeiro": "A020"}]
    file = tmp_path / "sample.csv"
    MODULE._write_csv(file, sample)
    with file.open(newline="", encoding="utf-8") as h:
        assert list(csv.DictReader(h)) == sample


def test_official_data_if_available():
    matrix = ROOT / "results/mcda/matriz_decisao.csv"
    ahp_file = ROOT / "results/mcda/pesos_ahp.json"
    base_file = ROOT / "data/parametros_promethee.json"
    if not all(p.is_file() for p in (matrix, ahp_file, base_file)):
        pytest.skip("Integração exige checkout oficial de D023, D024, D026")
    with matrix.open(encoding="utf-8", newline="") as handle:
        alts = list(csv.DictReader(handle))
    ahp = json.loads(ahp_file.read_text(encoding="utf-8"))["weights"]
    base = json.loads(base_file.read_text(encoding="utf-8"))["preference_parameters"]
    thresholds, weights, summary = MODULE.analyze(alts, ahp, base, PROTOCOL)
    assert all(x["primeiro"] == "A020" for x in thresholds)
    assert all(x["segundo"] == "A016" for x in thresholds)
    assert thresholds[1]["incomparaveis_promethee_i"] == 198
    assert thresholds[1]["phi_primeiro"] == pytest.approx(.5292317868364013, abs=1e-10)
    assert {x["primeiro"] for x in weights if x["peso_f1"] <= .70} == {"A020"}
    assert {x["primeiro"] for x in weights if x["peso_f1"] >= .75} == {"A002"}
    assert summary["winner_is_stable_across_thresholds"]
