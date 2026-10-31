"""Executa D026 PROMETHEE I/II sem alterar GVNS, D023, AHP ou ELECTRE.

Na raiz do checkout:
    python scripts/run_promethee.py
    python scripts/run_promethee.py --parameters data/meu_cenario_promethee.json \\
        --out results/mcda/promethee_meu_cenario
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from cassotis_optimization.mcda.promethee import CRITERIA, promethee_i_ii

ROOT = Path(__file__).resolve().parents[1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=ROOT / "results/mcda/matriz_decisao.csv")
    parser.add_argument("--weights", type=Path, default=ROOT / "results/mcda/pesos_ahp.json")
    parser.add_argument("--parameters", type=Path, default=ROOT / "data/parametros_promethee.json")
    parser.add_argument("--electre-summary", type=Path,
                        default=ROOT / "results/mcda/electre_i_resumo.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results/mcda")
    args = parser.parse_args()

    params = json.loads(args.parameters.read_text(encoding="utf-8"))
    ahp = json.loads(args.weights.read_text(encoding="utf-8"))
    if params.get("variant") != "PROMETHEE I/II":
        raise ValueError("Variante precisa ser PROMETHEE I/II.")
    if (tuple(params.get("criterion_order", [])) != CRITERIA
            or tuple(ahp.get("criterion_order", [])) != CRITERIA):
        raise ValueError("Ordem dos critérios precisa ser f1, f2, f3, c4.")
    if params.get("criteria_direction") != "min":
        raise ValueError("Os quatro critérios precisam ser de minimização.")
    if ahp.get("consistent") is not True:
        raise ValueError("Pesos AHP não confirmados como consistentes.")
    if len({args.matrix.resolve(), args.weights.resolve(), args.parameters.resolve()}) < 3:
        raise ValueError("Os arquivos de entrada devem ser distintos.")

    with args.matrix.open(encoding="utf-8", newline="") as handle:
        alternatives = list(csv.DictReader(handle))
    if len(alternatives) != 91:
        raise ValueError(f"Esperadas 91 alternativas na matriz oficial; recebidas {len(alternatives)}.")

    summary, ranking, pairs = promethee_i_ii(
        alternatives, ahp["weights"], params["preference_parameters"]
    )
    summary["decision_id"] = params["decision_id"]
    summary["scenario_status"] = params["status"]
    summary["scenario"] = params["scenario"]
    summary["preference_rationale"] = params["rationale"]
    summary["input_sha256"] = {
        "matrix": _sha(args.matrix), "weights": _sha(args.weights),
        "parameters": _sha(args.parameters),
    }

    if args.electre_summary.is_file():
        electre = json.loads(args.electre_summary.read_text(encoding="utf-8"))
        if electre.get("input_sha256", {}).get("matrix") != summary["input_sha256"]["matrix"]:
            raise ValueError("O ELECTRE salvo usou uma matriz diferente; impossível comparar.")
        if electre.get("input_sha256", {}).get("weights") != summary["input_sha256"]["weights"]:
            raise ValueError("O ELECTRE salvo usou pesos AHP diferentes; impossível comparar.")
        base = electre.get("choice_kernel")
        if base is not None:
            official_ids = {a["alternative_id"] for a in alternatives}
            if not set(base).issubset(official_ids):
                raise ValueError("Núcleo ELECTRE contém IDs ausentes da matriz atual.")
            for item in ranking:
                item["in_electre_kernel"] = item["alternative_id"] in base
            summary["electre_comparison"] = {
                "electre_kernel_size": len(base),
                "electre_kernel": base,
                "electre_ids_by_promethee_rank": [
                    {"alternative_id": row["alternative_id"],
                     "rank_promethee_ii": row["rank_promethee_ii"],
                     "phi_net": row["phi_net"]}
                    for row in ranking if row["alternative_id"] in base
                ],
                "promethee_top1_in_electre_kernel": ranking[0]["alternative_id"] in base,
                "caveat": "Interseção descritiva, não fusão automática dos dois métodos."
            }
        summary["input_sha256"]["electre_summary"] = _sha(args.electre_summary)
    else:
        for item in ranking:
            item["in_electre_kernel"] = ""
        summary["electre_comparison"] = None

    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "promethee_i_ii_resumo.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    ranking_path = args.out / "promethee_ii_ranking.csv"
    with ranking_path.open("w", encoding="utf-8", newline="") as handle:
        columns = ["rank_promethee_ii", "alternative_id", "phi_positive", "phi_negative",
                   "phi_net", "f1", "f2", "f3", "c4", "in_electre_kernel"]
        writer = csv.DictWriter(handle, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(ranking)
    with (args.out / "promethee_i_relacoes.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        columns = ["a", "b", "phi_positive_a", "phi_negative_a", "phi_positive_b",
                   "phi_negative_b", "relation_promethee_i"]
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(pairs)

    print(f"PROMETHEE I/II: {summary['alternative_count']} alternativas, "
          f"{summary['unordered_pairs']} pares")
    print(f"PROMETHEE I — incomparáveis: "
          f"{summary['promethee_i_pair_types']['incomparaveis']}")
    print("PROMETHEE II — cinco primeiros:")
    for row in ranking[:5]:
        print(f"  {row['rank_promethee_ii']:>2}. {row['alternative_id']}: "
              f"phi={row['phi_net']:.6f}")
    if summary["electre_comparison"]:
        print("Vencedor PROMETHEE II no núcleo ELECTRE:",
              summary["electre_comparison"]["promethee_top1_in_electre_kernel"])
    print("Status:", summary["scenario_status"])
    print("Arquivos:", ranking_path, args.out / "promethee_i_relacoes.csv")


if __name__ == "__main__":
    main()
