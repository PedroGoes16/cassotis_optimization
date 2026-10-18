"""Verifica a rodada oficial multiobjetivo sem modificar seus arquivos."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

from cassotis_optimization.evaluator import evaluate
from cassotis_optimization.io import load_instance
from cassotis_optimization.multiobjective.epsilon_restrito import epsilon_feasible
from cassotis_optimization.multiobjective.multiobjective import EpsilonLimits, Weights
from cassotis_optimization.multiobjective.normalizacao import load_bounds, normalized_objectives
from cassotis_optimization.multiobjective.pareto import nondominated_indices
from cassotis_optimization.multiobjective.soma_ponderada import weighted_sum
from cassotis_optimization.solution import Solution

ROOT = Path(__file__).resolve().parents[1]
OBJECTIVES = ("f1", "f2", "f3")


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def close(a: float, b: float) -> bool:
    return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)


def validate(results: Path, instance_path: Path, reference_path: Path) -> list[str]:
    """Recalcula avaliação, escalares, estatísticas e frentes da rodada oficial."""
    errors: list[str] = []
    manifest = json.loads((results / "manifest.json").read_text(encoding="utf-8"))
    protocol = manifest["protocol"]
    seeds = set(protocol["final"]["seeds"])
    instance = load_instance(instance_path)
    bounds = load_bounds(reference_path)
    rows = read_csv(results / "summary.csv")
    ids = {row["run_id"] for row in rows}
    if len(ids) != len(rows) or len(rows) != manifest["planned_runs"] or not manifest["complete"]:
        errors.append("A rodada é incompleta ou contém identificadores duplicados.")

    for row in rows:
        name = row["run_id"]
        record = json.loads((results / "runs" / f"{name}.json").read_text(encoding="utf-8"))
        solution = Solution({key: tuple(value) for key, value in record["composition"].items()})
        evaluation = evaluate(solution, instance)
        values = (evaluation.cost_rs, evaluation.f2_sio2_sq_dev, evaluation.f3_al2o3_sq_dev)
        normal = normalized_objectives(evaluation, bounds)
        for key, value, normalized in zip(OBJECTIVES, values, normal):
            if not close(float(row[key]), value) or not close(record[key], value):
                errors.append(f"{name}: valor {key} divergente")
            if not close(float(row[f"norm_{key}"]), normalized):
                errors.append(f"{name}: normalização {key} divergente")
            row[key] = float(row[key])
        if row["method"] == "weighted_sum":
            scalar = weighted_sum(evaluation, bounds, Weights(**record["weights"]))
            scalar_feasible = evaluation.feasible
        else:
            scalar = normal[0]
            scalar_feasible = epsilon_feasible(evaluation, bounds, EpsilonLimits(**record["epsilon_limits"]))
        if not close(float(row["scalar_objective"]), scalar):
            errors.append(f"{name}: objetivo escalar divergente")
        if (row["original_feasible"] == "True") != evaluation.feasible:
            errors.append(f"{name}: factibilidade original divergente")
        if (row["scalar_feasible"] == "True") != scalar_feasible:
            errors.append(f"{name}: factibilidade escalar divergente")
        if int(row["evaluations"]) != protocol["final"]["max_evaluations"]:
            errors.append(f"{name}: orçamento divergente")

    groups: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        groups.setdefault((row["method"], row["configuration"]), []).append(row)
    for method in ("weighted_sum", "epsilon_restricted"):
        configurations = [group for (name, _), group in groups.items() if name == method]
        if len(configurations) != protocol[method]["expected_configurations"]:
            errors.append(f"{method}: número de configurações divergente")
        for group in configurations:
            if {int(row["seed"]) for row in group} != seeds or len(group) != len(seeds):
                errors.append(f"{method}/{group[0]['configuration']}: seeds divergentes")

    for stat in read_csv(results / "stats_by_configuration.csv"):
        group = [row for row in groups[(stat["method"], stat["configuration"])]
                 if row["scalar_feasible"] == "True"]
        for key in OBJECTIVES:
            values = [row[key] for row in group]
            expected = {"min": min(values), "max": max(values), "mean": statistics.mean(values),
                        "std": statistics.stdev(values) if len(values) > 1 else 0.0}
            for suffix, value in expected.items():
                if not close(float(stat[f"{key}_{suffix}"]), value):
                    errors.append(f"{stat['configuration']}: estatística {key}_{suffix} divergente")

    def vector(row: dict) -> tuple[float, float, float]:
        return round(float(row["f1"]), 2), round(float(row["f2"]), 10), round(float(row["f3"]), 10)

    for method, filename in (("weighted_sum", "pareto_weighted_sum.csv"),
                             ("epsilon_restricted", "pareto_epsilon_restricted.csv"),
                             (None, "pareto_joint.csv")):
        eligible = [row for row in rows if (method is None or row["method"] == method)
                    and row["original_feasible"] == "True" and row["scalar_feasible"] == "True"]
        expected = {vector(eligible[i]) for i in nondominated_indices(eligible)}
        actual = {vector(row) for row in read_csv(results / filename)}
        if expected != actual:
            errors.append(f"{filename}: frente divergente")
        print(f"{filename}: {len(actual)} vetores distintos conferidos")
    print(f"{len(rows)} execuções; {len(errors)} divergências")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results/multi_final")
    parser.add_argument("--instance", type=Path, default=ROOT / "data/example_instance")
    parser.add_argument("--references", type=Path, default=ROOT / "data/referencias_multiobjetivo.json")
    args = parser.parse_args()
    errors = validate(args.results, args.instance, args.references)
    if errors:
        raise SystemExit("\n".join(errors))


if __name__ == "__main__":
    main()
