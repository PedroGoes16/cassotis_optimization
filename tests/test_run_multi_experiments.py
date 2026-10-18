"""Verificacoes do executor e do agrupamento de resultados."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("run_multi_experiments", ROOT / "scripts/run_multi_experiments.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_protocol_expands_to_32_parameter_sets():
    protocol = json.loads((ROOT / "data/protocolo_entrega2.json").read_text(encoding="utf-8"))
    configs = MODULE.configurations(protocol, MODULE.METHODS)
    assert len(configs) == 32
    assert len({(method, name) for method, name, _ in configs}) == 32


def test_pareto_collapses_duplicate_objective_values_preserving_origins():
    def row(name, seed, f1, f2, f3, feasible=True):
        return {"run_id": name, "seed": seed, "configuration": "c1", "scalar_feasible": feasible,
                "original_feasible": True, "f1": f1, "f2": f2, "f3": f3}
    rows = [
        row("a", 4001, 1.0, 1.0, 3.0),
        row("b", 4002, 1.0, 1.0, 3.0),
        row("c", 4002, 2.0, 2.0, 4.0),  # Dominado por a e b
        row("d", 4001, 2.0, 2.0, 0.0),  # Nao dominado em 3D
        row("e", 4001, 0.0, 0.0, 0.0, feasible=False),
    ]
    front = MODULE.unique_pareto_rows(rows)
    assert len(front) == 2
    assert front[0]["run_ids"] == ["a", "b"]
    assert set(front[0]["seeds"]) == {4001, 4002}


def test_signature_changes_with_config():
    assert MODULE.signature({"seed": 4001}) == MODULE.signature({"seed": 4001})
    assert MODULE.signature({"seed": 4001}) != MODULE.signature({"seed": 4002})


def test_file_fingerprints_are_portable_and_detect_changes(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    first.mkdir()
    second.mkdir()
    (first / "minerals.csv").write_bytes(b"name,value\nM1,2\n")
    (second / "minerals.csv").write_bytes(b"name,value\r\nM1,2\r\n")
    names = ("minerals.csv",)
    assert MODULE.file_fingerprints(first, names) == MODULE.file_fingerprints(second, names)
    (second / "minerals.csv").write_bytes(b"name,value\nM1,3\n")
    assert MODULE.file_fingerprints(first, names) != MODULE.file_fingerprints(second, names)


def test_source_fingerprints_detect_source_change(tmp_path):
    script = tmp_path / "scripts" / "run_multi_experiments.py"
    module = tmp_path / "src" / "cassotis_optimization" / "module.py"
    script.parent.mkdir(parents=True)
    module.parent.mkdir(parents=True)
    script.write_text("print('run')\n", encoding="utf-8")
    module.write_text("VALUE = 1\n", encoding="utf-8")
    before = MODULE.source_fingerprints(tmp_path)
    module.write_text("VALUE = 2\n", encoding="utf-8")
    after = MODULE.source_fingerprints(tmp_path)
    assert before != after
