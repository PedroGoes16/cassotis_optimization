"""Testes da D025: relações, vetos, incomparabilidade e núcleo em DAG."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from cassotis_optimization.mcda.electre import (
    _acyclic_choice_kernel,
    electre_i,
)

WEIGHTS = {"f1": .6474358974358975, "f2": .0782051282051282,
           "f3": .0782051282051282, "c4": .19615384615384615}
VETO = {k: .4 for k in WEIGHTS}


def r(name, f1, f2, f3, c4):
    return {"alternative_id": name, "f1": f1, "f2": f2, "f3": f3, "c4": c4}


def test_clear_dominance_outranks_worse_solution():
    rows = [r("A", 0, 0, 0, 0), r("B", 10, 10, 10, 10)]
    summary, pairs = electre_i(rows, WEIGHTS, .8, VETO)
    assert summary["choice_kernel"] == ["A"]
    assert summary["not_outranked_by_any"] == ["A"]
    assert pairs[0]["concordancia_ab"] == pytest.approx(1.0)
    assert pairs[0]["situacao"] == "a_sobreclassifica_b"


def test_veto_blocks_even_with_high_concordance():
    rows = [r("A", 0, 0, 0, 10), r("B", 10, 10, 10, 0)]
    summary, pairs = electre_i(rows, WEIGHTS, .8, VETO)
    assert pairs[0]["concordancia_ab"] == pytest.approx(sum(WEIGHTS[k] for k in ("f1","f2","f3")))
    assert pairs[0]["vetos_ab"] == "c4"
    assert pairs[0]["situacao"] == "incomparaveis"
    assert summary["choice_kernel"] == ["A", "B"]


def test_kernel_from_acyclic_nontransitive_graph():
    graph = [
        [False, True, False],
        [False, False, True],
        [False, False, False],
    ]
    result = _acyclic_choice_kernel(graph)
    assert result["acyclic"] is True
    assert result["kernel_indices"] == [0, 2]


def test_mutual_outranking_is_not_misreported_as_indifference():
    # Mesmo custo e heterogeneidade, mas objetivos químicos conflitantes.
    # Ambos contam com a coalizão custo + heterogeneidade + um desvio químico.
    rows = [r("A", 0, 0, 10, 0), r("B", 0, 10, 0, 0), r("C", 10, 20, 20, 10)]
    summary, pairs = electre_i(rows, WEIGHTS, .8, {k: 1 for k in WEIGHTS})
    assert pairs[0]["situacao"] == "sobreclassificacao_mutua"
    assert summary["choice_kernel"] is None
    assert {"A", "B"}.issubset(set(summary["cyclic_residue"]))


def test_reject_bad_parameters():
    rows = [r("A", 1, 2, 3, 4), r("B", 5, 6, 7, 8)]
    with pytest.raises(ValueError, match="limiar de concordância"):
        electre_i(rows, WEIGHTS, .3, VETO)
    with pytest.raises(ValueError, match="pesos devem somar"):
        electre_i(rows, {**WEIGHTS, "f1": .4}, .8, VETO)
    with pytest.raises(ValueError, match="veto relativo"):
        electre_i(rows, WEIGHTS, .8, {**VETO, "f2": 0})
    with pytest.raises(ValueError, match="repetidos"):
        electre_i([r("A", 1, 2, 3, 4), r("A", 5, 6, 7, 8)], WEIGHTS, .8, VETO)


def test_matrix_from_repository_if_present():
    """Teste de integração; ignora somente se o checkout não tiver a matriz D023."""
    root = Path(__file__).resolve().parents[1]
    matrix = root / "results/mcda/matriz_decisao.csv"
    pesos = root / "results/mcda/pesos_ahp.json"
    if not matrix.exists() or not pesos.exists():
        pytest.skip("Arquivo oficial não montado neste ambiente de testes")
    with matrix.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    weights = json.loads(pesos.read_text(encoding="utf-8"))["weights"]
    assert len(rows) == 91
    s, pairs = electre_i(rows, weights, .8, VETO)
    assert s["unordered_pairs"] == 4095
    assert s["outranking_arcs"] == 902
    assert s["pair_types"]["incomparaveis"] == 3193
    assert s["choice_kernel"] == [
        "A001", "A002", "A014", "A016", "A020", "A034", "A060", "A062", "A066"
    ]
    assert len(pairs) == 4095
