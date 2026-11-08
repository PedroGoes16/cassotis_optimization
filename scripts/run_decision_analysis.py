"""Run the reproducible multicriteria analysis for Delivery 3.

The script consumes only the official, jointly nondominated solutions from
Delivery 2. It never reruns or changes the optimization experiments.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from cassotis_optimization.decision.criteria import recipe_heterogeneity
from cassotis_optimization.decision.electre import ElectreResult, electre_iii
from cassotis_optimization.decision.normalization import normalize_rows
from cassotis_optimization.decision.promethee import PrometheeResult, promethee_ii
from cassotis_optimization.evaluator import evaluate
from cassotis_optimization.io import load_instance
from cassotis_optimization.solution import Solution
from cassotis_optimization.visualization import plot_solution

ROOT = Path(__file__).resolve().parents[1]
CRITERIA = ("f1", "f2", "f3", "heterogeneity")
PROJECTIONS = (("f1", "f2"), ("f1", "f3"), ("f2", "f3"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict], fields: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_latex_alternatives(path: Path, rows: list[dict], selected_id: str) -> None:
    """Write the complete criterion table used by the cumulative report."""
    lines = [
        r"\begin{longtable}{lrrrr}",
        (
            r"\caption{Valores dos quatro critérios para todas as alternativas avaliadas. "
            r"A alternativa recomendada está em negrito.}\label{tab:todas_alternativas}\\"
        ),
        r"\toprule",
        (
            r"\textbf{Alt.} & \textbf{Custo (R\$ mi)} & $\boldsymbol{f_2}$ & "
            r"$\boldsymbol{f_3}$ & \textbf{Heterogeneidade} \\"
        ),
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        (
            r"\textbf{Alt.} & \textbf{Custo (R\$ mi)} & $\boldsymbol{f_2}$ & "
            r"$\boldsymbol{f_3}$ & \textbf{Heterogeneidade} \\"
        ),
        r"\midrule",
        r"\endhead",
        r"\midrule",
        r"\multicolumn{5}{r}{Continua na próxima página}\\",
        r"\endfoot",
        r"\bottomrule",
        r"\endlastfoot",
    ]
    for row in rows:
        alternative = row["alternative_id"]
        values = (
            f"{float(row['f1']) / 1_000_000:.2f}".replace(".", ","),
            f"{float(row['f2']):.4f}".replace(".", ","),
            f"{float(row['f3']):.4f}".replace(".", ","),
            f"{float(row['heterogeneity']):.6f}".replace(".", ","),
        )
        cells = (alternative, *values)
        if alternative == selected_id:
            cells = tuple(r"\textbf{" + cell + "}" for cell in cells)
        lines.append(" & ".join(cells) + r" \\")
    lines.append(r"\end{longtable}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _composition_key(solution: Solution) -> str:
    canonical = {
        pile_id: sorted(dict(counts).items())
        for pile_id, counts in sorted(solution.counts_by_pile().items())
    }
    return hashlib.sha256(
        json.dumps(canonical, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _front_run_ids(front_path: Path) -> list[str]:
    with front_path.open(encoding="utf-8", newline="") as file:
        rows = list(csv.DictReader(file))
    return sorted({run_id for row in rows for run_id in json.loads(row["run_ids"])})


def load_alternatives(front_path: Path, runs_dir: Path, instance_dir: Path) -> list[dict]:
    """Load, independently evaluate and deduplicate candidate compositions."""
    instance = load_instance(instance_dir)
    grouped: dict[str, dict] = {}
    for run_id in _front_run_ids(front_path):
        path = runs_dir / f"{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"Missing run file referenced by front: {path}")
        run = json.loads(path.read_text(encoding="utf-8"))
        solution = Solution(
            {pile_id: tuple(minerals) for pile_id, minerals in run["composition"].items()}
        )
        evaluation = evaluate(solution, instance)
        if not evaluation.feasible:
            raise ValueError(f"Official candidate {run_id} is no longer feasible")
        expected = (float(run["f1"]), float(run["f2"]), float(run["f3"]))
        actual = (
            evaluation.cost_rs,
            evaluation.f2_sio2_sq_dev,
            evaluation.f3_al2o3_sq_dev,
        )
        if any(abs(a - b) > 1e-8 * max(1.0, abs(b)) for a, b in zip(actual, expected)):
            raise ValueError(f"Re-evaluation diverges from stored objectives for {run_id}")

        key = _composition_key(solution)
        if key not in grouped:
            grouped[key] = {
                "composition_key": key,
                "run_ids": [],
                "methods": [],
                "f1": actual[0],
                "f2": actual[1],
                "f3": actual[2],
                "heterogeneity": recipe_heterogeneity(solution, instance),
                "solution": solution,
            }
        grouped[key]["run_ids"].append(run_id)
        grouped[key]["methods"].append(run["method"])

    alternatives = sorted(
        grouped.values(),
        key=lambda row: tuple(row[criterion] for criterion in CRITERIA) + (row["composition_key"],),
    )
    for index, row in enumerate(alternatives, 1):
        row["alternative_id"] = f"A{index:03d}"
        row["run_ids"] = sorted(set(row["run_ids"]))
        row["methods"] = sorted(set(row["methods"]))
    return alternatives


def _thresholds(protocol: dict, scale: float = 1.0) -> tuple[dict, dict, dict]:
    baseline = protocol["baseline"]
    q = {criterion: baseline["q"] * scale for criterion in CRITERIA}
    p = {criterion: baseline["p"] * scale for criterion in CRITERIA}
    veto = {criterion: baseline["veto"] * scale for criterion in CRITERIA}
    return q, p, veto


def _electre_choice(
    electre: ElectreResult,
    promethee: PrometheeResult,
    normalized: list[dict[str, float]],
    alternative_ids: list[str],
) -> int:
    """Resolve ELECTRE's maximal set using the registered additional rule."""
    if not electre.maximal:
        candidates = tuple(range(len(normalized)))
    else:
        candidates = electre.maximal
    return min(
        candidates,
        key=lambda index: (
            -promethee.net_flow[index],
            max(normalized[index].values()),
            alternative_ids[index],
        ),
    )


def _weight_profiles(protocol: dict) -> list[tuple[str, dict[str, float]]]:
    profiles = [("equal", dict(protocol["baseline"]["weights"]))]
    priority = float(protocol["sensitivity"]["priority_weight"])
    other = float(protocol["sensitivity"]["other_weights"])
    for focus in CRITERIA:
        profiles.append(
            (f"priority_{focus}", {criterion: priority if criterion == focus else other for criterion in CRITERIA})
        )
    return profiles


def _rank_rows(
    alternatives: list[dict],
    promethee: PrometheeResult,
    electre: ElectreResult,
) -> tuple[list[dict], list[dict]]:
    promethee_rows = []
    for rank, index in enumerate(promethee.ranking, 1):
        promethee_rows.append(
            {
                "rank": rank,
                "alternative_id": alternatives[index]["alternative_id"],
                "positive_flow": promethee.positive_flow[index],
                "negative_flow": promethee.negative_flow[index],
                "net_flow": promethee.net_flow[index],
            }
        )
    maximal = set(electre.maximal)
    electre_rows = []
    for rank, index in enumerate(electre.ranking, 1):
        electre_rows.append(
            {
                "display_rank": rank,
                "alternative_id": alternatives[index]["alternative_id"],
                "net_credibility": electre.net_credibility[index],
                "maximal": index in maximal,
            }
        )
    return promethee_rows, electre_rows


def _plot_selected(
    alternatives: list[dict],
    promethee_index: int,
    electre_index: int,
    out: Path,
) -> None:
    labels = {
        "f1": "Custo total (R$)",
        "f2": "Desvio quadrático SiO₂",
        "f3": "Desvio quadrático Al₂O₃",
    }
    for x, y in PROJECTIONS:
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.scatter([row[x] for row in alternatives], [row[y] for row in alternatives], color="0.7", s=26, label="Alternativas")
        ax.scatter(alternatives[promethee_index][x], alternatives[promethee_index][y], marker="*", s=180, color="#1565c0", edgecolor="white", label="PROMETHEE II")
        ax.scatter(alternatives[electre_index][x], alternatives[electre_index][y], marker="X", s=110, color="#ef6c00", edgecolor="white", label="ELECTRE III")
        ax.set_xlabel(labels[x]); ax.set_ylabel(labels[y]); ax.grid(alpha=0.2); ax.legend()
        ax.set_title(f"Alternativas e escolhas multicritério: {x} x {y}")
        fig.tight_layout()
        fig.savefig(out / f"selected_{x}_{y}.png", dpi=160)
        plt.close(fig)


def run_analysis(protocol_path: Path, instance_dir: Path, results_dir: Path, out: Path) -> dict:
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if protocol["status"] != "CONSOLIDADO":
        raise ValueError("Delivery 3 protocol must be CONSOLIDADO before final analysis")
    alternatives = load_alternatives(
        results_dir / "pareto_joint.csv", results_dir / "runs", instance_dir
    )
    raw_rows = [{criterion: row[criterion] for criterion in CRITERIA} for row in alternatives]
    normalized, fitted = normalize_rows(raw_rows, CRITERIA)
    alternative_ids = [row["alternative_id"] for row in alternatives]

    weights = protocol["baseline"]["weights"]
    q, p, veto = _thresholds(protocol)
    promethee = promethee_ii(normalized, weights, q, p)
    electre = electre_iii(
        normalized,
        weights,
        q,
        p,
        veto,
        credibility_cutoff=protocol["baseline"]["electre_credibility_cutoff"],
    )
    promethee_choice = promethee.ranking[0]
    electre_choice = _electre_choice(electre, promethee, normalized, alternative_ids)

    alternative_rows: list[dict] = []
    for index, row in enumerate(alternatives):
        alternative_rows.append(
            {
                "alternative_id": row["alternative_id"],
                "run_ids": json.dumps(row["run_ids"], ensure_ascii=False),
                "methods": json.dumps(row["methods"], ensure_ascii=False),
                **{criterion: row[criterion] for criterion in CRITERIA},
                **{f"norm_{criterion}": normalized[index][criterion] for criterion in CRITERIA},
            }
        )
    write_csv(
        out / "alternatives.csv",
        alternative_rows,
        ("alternative_id", "run_ids", "methods") + CRITERIA + tuple(f"norm_{c}" for c in CRITERIA),
    )
    promethee_rows, electre_rows = _rank_rows(alternatives, promethee, electre)
    write_csv(out / "promethee_ranking.csv", promethee_rows, tuple(promethee_rows[0]))
    write_csv(out / "electre_ranking.csv", electre_rows, tuple(electre_rows[0]))
    write_latex_alternatives(out / "alternatives_table.tex", alternative_rows, alternative_ids[electre_choice])

    sensitivity_rows: list[dict] = []
    for profile_name, profile_weights in _weight_profiles(protocol):
        for threshold_scale in protocol["sensitivity"]["threshold_scales"]:
            sq, sp, sv = _thresholds(protocol, float(threshold_scale))
            spr = promethee_ii(normalized, profile_weights, sq, sp)
            sel = electre_iii(
                normalized,
                profile_weights,
                sq,
                sp,
                sv,
                credibility_cutoff=protocol["baseline"]["electre_credibility_cutoff"],
            )
            p_choice = spr.ranking[0]
            e_choice = _electre_choice(sel, spr, normalized, alternative_ids)
            sensitivity_rows.append(
                {
                    "weight_profile": profile_name,
                    "threshold_scale": threshold_scale,
                    "promethee_winner": alternative_ids[p_choice],
                    "electre_choice": alternative_ids[e_choice],
                    "electre_maximal_count": len(sel.maximal),
                    "electre_incomparable_pairs": len(sel.incomparable_pairs),
                    "electre_choice_promethee_rank": spr.ranking.index(e_choice) + 1,
                    "electre_choice_display_rank": sel.ranking.index(e_choice) + 1,
                }
            )
    write_csv(out / "sensitivity.csv", sensitivity_rows, tuple(sensitivity_rows[0]))

    _plot_selected(alternatives, promethee_choice, electre_choice, out)
    instance = load_instance(instance_dir)
    final_solution = alternatives[electre_choice]["solution"]
    figure = plot_solution(
        final_solution,
        instance,
        f"Solução final {alternative_ids[electre_choice]}",
    )
    figure.savefig(out / "final_solution.png", dpi=160, bbox_inches="tight")
    plt.close(figure)

    scale_payload = {
        criterion: {"minimum": fitted.minimum[criterion], "maximum": fitted.maximum[criterion]}
        for criterion in CRITERIA
    }
    analysis = {
        "protocol": str(protocol_path),
        "candidate_run_count": len(_front_run_ids(results_dir / "pareto_joint.csv")),
        "unique_composition_count": len(alternatives),
        "normalization": scale_payload,
        "baseline": {
            "promethee_choice": alternative_ids[promethee_choice],
            "electre_maximal": [alternative_ids[index] for index in electre.maximal],
            "electre_choice_after_tie_break": alternative_ids[electre_choice],
            "electre_incomparable_pairs": len(electre.incomparable_pairs),
            "consensus": promethee_choice == electre_choice,
            "final_recommendation": alternative_ids[electre_choice],
            "final_criteria": {
                criterion: alternatives[electre_choice][criterion] for criterion in CRITERIA
            },
        },
        "sensitivity": {
            "scenario_count": len(sensitivity_rows),
            "promethee_winner_frequency": dict(Counter(row["promethee_winner"] for row in sensitivity_rows)),
            "electre_choice_frequency": dict(Counter(row["electre_choice"] for row in sensitivity_rows)),
        },
    }
    write_json(out / "analysis.json", analysis)
    write_json(
        out / "selected_solution.json",
        {
            "alternative_id": alternative_ids[electre_choice],
            "run_ids": alternatives[electre_choice]["run_ids"],
            "criteria": {criterion: alternatives[electre_choice][criterion] for criterion in CRITERIA},
            "composition": {pile: list(minerals) for pile, minerals in final_solution.composition.items()},
        },
    )
    return analysis


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, default=ROOT / "data" / "protocolo_entrega3.json")
    parser.add_argument("--instance", type=Path, default=ROOT / "data" / "example_instance")
    parser.add_argument("--results", type=Path, default=ROOT / "results" / "multi_final")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "decision_final")
    args = parser.parse_args()
    analysis = run_analysis(args.protocol.resolve(), args.instance.resolve(), args.results.resolve(), args.out.resolve())
    print(json.dumps(analysis, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
