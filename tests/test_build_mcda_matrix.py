"""Testes da D023 sem exigir o checkout completo nem iniciar a GVNS."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_mcda_matrix.py"
SPEC = importlib.util.spec_from_file_location("build_mcda_matrix", SCRIPT)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_c4_homogeneity_of_recipe_not_chemical_quality():
    specs = {"P1": ("Sinter1", 2), "P2": ("Sinter1", 2)}
    identical = {"P1": ["M1", "M2"], "P2": ["M1", "M2"]}
    different = {"P1": ["M1", "M1"], "P2": ["M2", "M2"]}
    assert MODULE.recipe_heterogeneity(identical, specs) == pytest.approx(0.0)
    assert MODULE.recipe_heterogeneity(different, specs) == pytest.approx(0.5)


def test_c4_is_group_specific():
    specs = {"P1": ("Sinter1", 2), "P2": ("Sinter2", 2)}
    different = {"P1": ["M1", "M1"], "P2": ["M2", "M2"]}
    # Grupos diferentes não devem ser forçados à mesma receita.
    assert MODULE.recipe_heterogeneity(different, specs) == pytest.approx(0.0)


def test_c4_accounts_for_pile_sizes():
    specs = {"P1": ("Sinter1", 2), "P2": ("Sinter1", 4)}
    x = {"P1": ["M1", "M1"], "P2": ["M2"] * 4}
    # Receita global = 1/3 M1 e 2/3 M2; distâncias = 2/3, 1/3.
    assert MODULE.recipe_heterogeneity(x, specs) == pytest.approx(0.5)


def test_rejects_invalid_pile_sizes():
    with pytest.raises(ValueError, match="esperado 3 caminhões"):
        MODULE._validate_composition({"P1": ["M1"]}, {"P1": ("Sinter1", 3)})

def test_spearman_with_ties_and_conflict():
    assert MODULE.spearman([1, 2, 3], [3, 2, 1]) == pytest.approx(-1)
    assert MODULE.spearman([1, 1, 1], [1, 2, 3]) is None
    assert MODULE.rank_average([1, 1, 2]) == [1.5, 1.5, 3]
    a = [{"c4": 2, "f1": 20}, {"c4": 3, "f1": 10}]
    assert MODULE.conflicts(a, "f1")["opposed_pairs"] == 1


def write_fixture(tmp_path: Path, distinct_compositions=False):
    root = tmp_path / "example"
    root.mkdir()
    piles = root / "piles.csv"
    piles.write_text("pile_id,group_id,mass_kt\nP1,Sinter1,4\nP2,Sinter1,4\n")
    out = tmp_path / "results"
    runs = out / "runs"
    runs.mkdir(parents=True)
    records = [
        ("weighted_sum_w01_seed2021", 100.0, 5.0, 3.0, {"P1": ["M1", "M2"], "P2": ["M1", "M1"]}),
        ("epsilon_restricted_e01_seed2021", 110.0, 4.0, 2.0, {"P1": ["M1", "M1"], "P2": ["M1", "M1"]}),
        ("epsilon_restricted_e02_seed2021", 110.0, 4.0, 2.0,
         {"P1": ["M2", "M2"], "P2": ["M1", "M2"]} if distinct_compositions else
         {"P1": ["M1", "M1"], "P2": ["M1", "M1"]}),
    ]
    for id_, f1, f2, f3, composition in records:
        rec = {
            "run_id": id_, "f1": f1, "f2": f2, "f3": f3,
            "original_feasible": True, "scalar_feasible": True,
            "method": "weighted_sum" if id_.startswith("weighted") else "epsilon_restricted",
            "configuration": id_.split("_")[-2], "seed": 2021,
            "composition": composition,
        }
        (runs / f"{id_}.json").write_text(json.dumps(rec))
    with (out / "pareto_joint.csv").open("w", newline="") as file:
        w = csv.writer(file)
        w.writerow(["f1", "f2", "f3", "run_ids", "seeds", "configurations"])
        w.writerow([100, 5, 3, json.dumps([records[0][0]]), "[2021]", '["w01"]'])
        w.writerow([110, 4, 2, json.dumps([records[1][0], records[2][0]]), "[2021]", '["e01","e02"]'])
    return out, piles


def test_build_matrix_and_audit(tmp_path):
    source, piles = write_fixture(tmp_path)
    matrix, audit = MODULE.build_matrix(source, piles, expected_alternatives=2)
    assert [x["alternative_id"] for x in matrix] == ["A001", "A002"]
    assert [x["c4"] for x in matrix] == pytest.approx([0.25, 0])
    assert audit["alternative_count"] == 2
    assert audit["origin_run_count"] == 3
    out = tmp_path / "final"
    MODULE.write_outputs(matrix, audit, out)
    assert len(MODULE._read_csv(out / "matriz_decisao.csv")) == 2
    assert json.loads((out / "diagnostico_d023.json").read_text())["alternative_count"] == 2


def test_refuse_to_collapse_distinct_compositions(tmp_path):
    source, piles = write_fixture(tmp_path, distinct_compositions=True)
    with pytest.raises(ValueError, match="composições diferentes"):
        MODULE.build_matrix(source, piles, expected_alternatives=2)


def test_detects_missing_origin(tmp_path):
    source, piles = write_fixture(tmp_path)
    (source / "runs" / "epsilon_restricted_e02_seed2021.json").unlink()
    with pytest.raises(FileNotFoundError, match="não encontrada"):
        MODULE.build_matrix(source, piles, expected_alternatives=2)


def test_fails_on_wrong_expected_size(tmp_path):
    source, piles = write_fixture(tmp_path)
    with pytest.raises(ValueError, match="Esperadas 91 alternativas"):
        MODULE.build_matrix(source, piles, expected_alternatives=91)
