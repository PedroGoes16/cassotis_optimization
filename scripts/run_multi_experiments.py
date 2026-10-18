"""Entrega 2: execução reproduzível da Soma Ponderada e epsilon-restrito.

O piloto usa os parametros e sementes de data/protocolo_entrega2.json.
A etapa final so e liberada apos o status do protocolo mudar para CONGELADO.

Exemplos (executar da raiz com pip install -e .):
    python scripts/run_multi_experiments.py --phase pilot --max-runs 2 --out results/multi_smoke
    python scripts/run_multi_experiments.py --phase pilot
    python scripts/run_multi_experiments.py --phase final
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import statistics
import subprocess
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cassotis_optimization.algorithms.gvns import GVNSConfig, run_gvns
from cassotis_optimization.io import load_instance
from cassotis_optimization.multiobjective.multiobjective import EpsilonLimits, Weights
from cassotis_optimization.multiobjective.normalizacao import load_bounds, normalized_objectives
from cassotis_optimization.multiobjective.pareto import nondominated_indices
from cassotis_optimization.multiobjective.planejamento import epsilon_grid, weight_grid

ROOT = Path(__file__).resolve().parents[1]
METHODS = ("weighted_sum", "epsilon_restricted")
PROJECTIONS = (("f1", "f2"), ("f1", "f3"), ("f2", "f3"))
INSTANCE_FILES = ("minerals.csv", "groups.csv", "piles.csv")
CSV_FIELDS = (
    "run_id", "phase", "method", "configuration", "seed", "original_feasible",
    "scalar_feasible", "f1", "f2", "f3", "norm_f1", "norm_f2", "norm_f3",
    "scalar_objective", "total_violation", "epsilon_violation_f2",
    "epsilon_violation_f3", "evaluations", "first_feasible_at",
    "runtime_seconds", "iterations", "improvements", "weights", "epsilon_limits",
    "code_version", "config_hash",
)


def git_version() -> str:
    try:
        value = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no"], cwd=ROOT,
            check=True, capture_output=True, text=True,
        ).stdout.strip()
        return value + ("-dirty" if dirty else "")
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def signature(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def file_fingerprints(directory: Path, paths: tuple[str, ...]) -> dict[str, str]:
    """Identifica conteúdo textual, sem depender do caminho ou de CRLF/LF."""
    return {
        name: hashlib.sha256(
            (directory / name).read_text(encoding="utf-8").encode("utf-8")
        ).hexdigest()
        for name in sorted(paths)
    }


def source_fingerprints(root: Path) -> dict[str, str]:
    """Assina o executor e o núcleo Python usado na geração dos resultados."""
    package = root / "src" / "cassotis_optimization"
    paths = ["scripts/run_multi_experiments.py"] + [
        path.relative_to(root).as_posix() for path in package.rglob("*.py")
    ]
    return file_fingerprints(root, tuple(paths))


def configurations(protocol: dict, methods: tuple[str, ...]) -> list[tuple[str, str, dict]]:
    """Uma configuracao por combinacao de pesos ou par de epsilons."""
    configurations_list: list[tuple[str, str, dict]] = []

    if "weighted_sum" in methods:
        spec = protocol["weighted_sum"]
        grid = weight_grid(spec["simplex_denominator"], spec["include_equal_weights"])
        if len(grid) != spec["expected_configurations"]:
            raise ValueError("A quantidade de pesos diverge do protocolo")
        for index, weights in enumerate(grid, 1):
            configurations_list.append(("weighted_sum", f"w{index:02d}", {"weights": asdict(weights)}))

    if "epsilon_restricted" in methods:
        spec = protocol["epsilon_restricted"]
        if spec["primary_objective"] != "f1":
            raise ValueError("Esta implementacao epsilon-restrita fixa f1 como objetivo principal")
        grid = epsilon_grid(spec["levels_f2"], spec["levels_f3"])
        if len(grid) != spec["expected_configurations"]:
            raise ValueError("A quantidade de epsilons diverge do protocolo")
        for index, limits in enumerate(grid, 1):
            configurations_list.append(("epsilon_restricted", f"e{index:02d}", {"epsilon_limits": asdict(limits)}))

    return configurations_list


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(row[key], ensure_ascii=False) if isinstance(row.get(key), (dict, list)) else row.get(key) for key in fields})


def unique_pareto_rows(rows: list[dict]) -> list[dict]:
    """Filtro em 3D, depois agrupa objetivos numericamente coincidentes.

    A informacao de origem e mantida mesmo se mais de uma seed/config gerou
    o mesmo vetor objetivo. Rounding e aplicado apenas para consolidar pontos
    na figura (custo com centavos, desvios com 10 casas).
    """
    eligible = [row for row in rows if row["scalar_feasible"] and row["original_feasible"]]
    nondominated = [eligible[i] for i in nondominated_indices(eligible)]
    grouped: dict[tuple[float, float, float], dict] = {}
    for row in nondominated:
        key = (round(row["f1"], 2), round(row["f2"], 10), round(row["f3"], 10))
        if key not in grouped:
            grouped[key] = {"f1": row["f1"], "f2": row["f2"], "f3": row["f3"], "run_ids": [], "seeds": [], "configurations": []}
        grouped[key]["run_ids"].append(row["run_id"])
        grouped[key]["seeds"].append(row["seed"])
        grouped[key]["configurations"].append(row["configuration"])
    return sorted(grouped.values(), key=lambda r: (r["f1"], r["f2"], r["f3"]))


def plot_projections(front: list[dict], method: str, seeds: list[int], out: Path) -> None:
    palette = plt.get_cmap("tab10")
    colors = {seed: palette(i % 10) for i, seed in enumerate(sorted(set(seeds)))}
    pretty = {"f1": "Custo total (R$)", "f2": "Desvio quadratico SiO2", "f3": "Desvio quadratico Al2O3"}

    for x, y in PROJECTIONS:
        fig, ax = plt.subplots(figsize=(7, 5))
        plotted = set()
        for row in front:
            # Pontos com origem em varias seeds sao marcados com circulo preto
            source_seeds = sorted(set(row["seeds"]))
            seed = source_seeds[0]
            if len(source_seeds) == 1:
                label = f"Seed {seed}" if seed not in plotted else None
                ax.scatter(row[x], row[y], color=colors[seed], s=48, alpha=0.85, label=label)
                plotted.add(seed)
            else:
                label = "Multiplas seeds" if "multi" not in plotted else None
                ax.scatter(row[x], row[y], color="black", marker="D", s=55, alpha=0.9, label=label)
                plotted.add("multi")
        if not front:
            ax.text(0.5, 0.5, "Nenhuma solucao factivel nao dominada", ha="center", va="center", transform=ax.transAxes)
        ax.set_xlabel(pretty[x]); ax.set_ylabel(pretty[y]); ax.grid(alpha=0.2)
        ax.set_title(f"{method}: fronteira nao dominada 3D projetada em {x} x {y}")
        if plotted:
            ax.legend(fontsize="small")
        fig.tight_layout()
        fig.savefig(out / f"pareto_{method}_{x}_{y}.png", dpi=160)
        plt.close(fig)


def analyze(rows: list[dict], out: Path, methods: tuple[str, ...], seeds: list[int], *, complete: bool) -> dict:
    output = {"completed_runs": len(rows), "complete": complete, "methods": {}}
    # A analise estatistica usa as cinco replicacoes factiveis de cada configuracao.
    per_config = []
    for (method, configuration), group in sorted(
        ((k, list(g)) for k, g in _group_by_configuration(rows).items())
    ):
        feasible_group = [row for row in group if row["scalar_feasible"]]
        item = {"method": method, "configuration": configuration,
                "runs": len(group), "scalar_feasible_runs": len(feasible_group)}
        for objective in ("f1", "f2", "f3"):
            values = [row[objective] for row in feasible_group]
            item[f"{objective}_min"] = min(values) if values else None
            item[f"{objective}_mean"] = statistics.mean(values) if values else None
            item[f"{objective}_std"] = statistics.stdev(values) if len(values) > 1 else (0.0 if values else None)
            item[f"{objective}_max"] = max(values) if values else None
        per_config.append(item)
    stat_fields = ("method", "configuration", "runs", "scalar_feasible_runs") + tuple(
        f"{objective}_{stat}" for objective in ("f1", "f2", "f3")
        for stat in ("min", "mean", "std", "max")
    )
    write_csv(out / "stats_by_configuration.csv", per_config, stat_fields)
    for method in methods:
        method_rows = [row for row in rows if row["method"] == method]
        front = unique_pareto_rows(method_rows)
        fields = ("f1", "f2", "f3", "run_ids", "seeds", "configurations")
        write_csv(out / f"pareto_{method}.csv", front, fields)
        plot_projections(front, method, seeds, out)
        counts = Counter(row["configuration"] for row in method_rows if row["scalar_feasible"])
        seed_contributions = Counter(seed for point in front for seed in set(point["seeds"]))
        method_stats = {
            "runs": len(method_rows),
            "original_feasible_runs": sum(row["original_feasible"] for row in method_rows),
            "scalar_feasible_runs": sum(row["scalar_feasible"] for row in method_rows),
            "unique_nondominated_vectors": len(front),
            "scalar_feasible_by_configuration": dict(sorted(counts.items())),
            "nondominated_points_by_seed": dict(sorted(seed_contributions.items())),
        }
        output["methods"][method] = method_stats
    # Frente conjunta para comparar os dois metodos, sem substituir as duas
    # frentes individuais exigidas no enunciado.
    if set(methods) == set(METHODS):
        pooled = unique_pareto_rows(rows)
        write_csv(out / "pareto_joint.csv", pooled,
                  ("f1", "f2", "f3", "run_ids", "seeds", "configurations"))
        output["joint_nondominated_vectors"] = len(pooled)
    write_json(out / "analysis.json", output)
    return output


def _group_by_configuration(rows: list[dict]) -> dict[tuple[str, str], list[dict]]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for row in rows:
        grouped[(row["method"], row["configuration"])].append(row)
    return grouped


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("pilot", "final"), default="pilot")
    parser.add_argument("--protocol", type=Path, default=ROOT / "data/protocolo_entrega2.json")
    parser.add_argument("--instance", type=Path, default=ROOT / "data/example_instance")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=list(METHODS))
    parser.add_argument("--max-runs", type=int, help="Limita a qtd de execucoes para smoke (usar --out separado).")
    parser.add_argument("--budget", type=int, help="Sobrescreve orcamento apenas no piloto/smoke")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    protocol_path = args.protocol.resolve()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if args.phase == "final":
        if protocol["status"] != "CONGELADO":
            parser.error("Execucao final bloqueada: congele o protocolo (status=CONGELADO) apos analisar o piloto.")
        if args.max_runs is not None or args.budget is not None:
            parser.error("Execucao final nao aceita --max-runs nem --budget")
    if args.max_runs is not None and args.max_runs < 1:
        parser.error("--max-runs deve ser positivo")

    phase_config = protocol[args.phase]
    seeds = phase_config["seeds"]
    budget = args.budget if args.budget is not None else phase_config["max_evaluations"]
    if budget < 1 or len(set(seeds)) != len(seeds):
        parser.error("Orcamento/seeds invalidos")

    selected_methods = tuple(dict.fromkeys(args.methods))
    configurations_list = configurations(protocol, selected_methods)
    jobs = [(method, name, params, seed) for method, name, params in configurations_list for seed in seeds]
    planned = len(jobs)
    if args.max_runs is not None:
        jobs = jobs[:args.max_runs]
    out = args.out or ROOT / "results" / ("multi_pilot" if args.phase == "pilot" else "multi_final")
    out = out.resolve()

    # Nao confundir uma amostra parcial com o piloto/final completos.
    complete = len(jobs) == planned and len(selected_methods) == len(METHODS)
    if (args.max_runs is not None or args.budget is not None or not complete) and args.out is None:
        parser.error("Rodadas parciais/smoke precisam de --out explicito para nao sobrescrever a fase completa")

    if args.dry_run:
        print(json.dumps({"phase": args.phase, "planned_runs": planned, "selected_runs": len(jobs), "budget": budget, "out": str(out), "methods": selected_methods}, indent=2))
        return

    out.mkdir(parents=True, exist_ok=True)
    instance = load_instance(args.instance)
    bounds = load_bounds(ROOT / protocol["reference_file"])
    version = git_version()
    instance_files = file_fingerprints(args.instance, INSTANCE_FILES)
    code_files = source_fingerprints(ROOT)
    run_dir = out / "runs"
    run_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for index, (method, name, params, seed) in enumerate(jobs, 1):
        run_id = f"{method}_{name}_seed{seed}"
        weights = Weights(**params["weights"]) if "weights" in params else None
        epsilons = EpsilonLimits(**params["epsilon_limits"]) if "epsilon_limits" in params else None
        config = GVNSConfig(
            objective=method,
            seed=seed,
            max_evaluations=budget,
            sample_size=protocol["gvns"]["sample_size"],
            p1_positions=protocol["gvns"]["p1_positions"],
            p2_chain_length=protocol["gvns"]["p2_chain_length"],
            p3_piles=protocol["gvns"]["p3_piles"],
            bounds=bounds,
            weights=weights,
            epsilon_limits=epsilons,
        )
        config_hash = signature({"signature_version": 2, "config": asdict(config),
                                 "instance_files": instance_files, "code_files": code_files,
                                 "phase": args.phase, "protocol": protocol})
        record_path = run_dir / f"{run_id}.json"
        if record_path.exists():
            record = json.loads(record_path.read_text(encoding="utf-8"))
            if record["config_hash"] != config_hash:
                raise ValueError(
                    f"Assinatura divergente no arquivo existente: {record_path}. "
                    "Resultados legados usam outra assinatura; preserve-os e use --out "
                    "para uma pasta nova. Não misture código, instância ou protocolos distintos."
                )
            print(f"[{index}/{len(jobs)}] retomando {run_id}", flush=True)
        else:
            result = run_gvns(instance, config)
            evaluation = result.best.evaluation
            normalized = normalized_objectives(evaluation, bounds)
            v2 = max(0.0, normalized[1] - epsilons.f2) if epsilons else 0.0
            v3 = max(0.0, normalized[2] - epsilons.f3) if epsilons else 0.0
            record = {
                "run_id": run_id, "phase": args.phase, "method": method,
                "configuration": name, "seed": seed,
                "original_feasible": evaluation.feasible,
                "scalar_feasible": result.best.feasible,
                "f1": evaluation.cost_rs, "f2": evaluation.f2_sio2_sq_dev,
                "f3": evaluation.f3_al2o3_sq_dev,
                "norm_f1": normalized[0], "norm_f2": normalized[1], "norm_f3": normalized[2],
                "scalar_objective": result.best.objective,
                "total_violation": result.best.violation,
                "epsilon_violation_f2": v2, "epsilon_violation_f3": v3,
                "evaluations": result.evaluations,
                "first_feasible_at": result.first_feasible_at,
                "runtime_seconds": result.runtime_seconds,
                "iterations": result.iterations, "improvements": result.improvements,
                "weights": params.get("weights"), "epsilon_limits": params.get("epsilon_limits"),
                "code_version": version, "config_hash": config_hash,
                "parameters": asdict(config), "stats": result.stats,
                "history": result.history_as_dicts(),
                "composition": {key: list(value) for key, value in result.best.solution.composition.items()},
            }
            write_json(record_path, record)
            print(f"[{index}/{len(jobs)}] {run_id}: original={evaluation.feasible} escalar={result.best.feasible} f=({record['f1']:.0f}, {record['f2']:.5f}, {record['f3']:.5f}) tempo={result.runtime_seconds:.1f}s", flush=True)
        rows.append(record)
        # Arquivos recuperaveis caso uma execucao longa seja interrompida.
        write_csv(out / "summary.csv", rows, CSV_FIELDS)
    analysis = analyze(rows, out, selected_methods, seeds, complete=complete)
    write_json(out / "manifest.json", {
        "phase": args.phase, "protocol_path": str(protocol_path), "protocol": protocol,
        "instance": str(args.instance.resolve()), "git_version": version,
        "signature_version": 2, "instance_files": instance_files, "code_files": code_files,
        "planned_runs": planned, "selected_runs": len(jobs), "complete": complete,
        "analysis": analysis,
    })
    print(json.dumps(analysis, indent=2, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
