"""Executa ELECTRE I (D025), sem alterar matriz D023 nem resultados da GVNS.

Executar na raiz do checkout: python scripts/run_electre.py
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from cassotis_optimization.mcda.electre import CRITERIA, electre_i

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=ROOT / "results/mcda/matriz_decisao.csv")
    parser.add_argument("--weights", type=Path, default=ROOT / "results/mcda/pesos_ahp.json")
    parser.add_argument("--parameters", type=Path, default=ROOT / "data/parametros_electre.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results/mcda")
    args = parser.parse_args()

    params = json.loads(args.parameters.read_text(encoding="utf-8"))
    ahp = json.loads(args.weights.read_text(encoding="utf-8"))
    if params["variant"] != "ELECTRE I":
        raise ValueError("A variante selecionada não é ELECTRE I.")
    if tuple(params["criterion_order"]) != CRITERIA or tuple(ahp["criterion_order"]) != CRITERIA:
        raise ValueError("A ordem dos critérios deve ser f1, f2, f3, c4.")
    if not ahp["consistent"]:
        raise ValueError("A matriz AHP registrada não passou no teste de consistência.")
    if params["criteria_direction"] != "min":
        raise ValueError("Esta implementação considera todos os critérios de minimização.")
    if args.matrix.resolve() == args.weights.resolve() or args.matrix.resolve() == args.parameters.resolve():
        raise ValueError("Entradas não podem apontar para o mesmo arquivo.")
    with args.matrix.open(encoding="utf-8", newline="") as stream:
        alternatives = list(csv.DictReader(stream))
    summary, details = electre_i(
        alternatives=alternatives,
        weights=ahp["weights"],
        concordance_threshold=float(params["concordance_threshold"]),
        veto_fractions=params["veto_fraction_of_observed_range"],
    )
    summary["scenario_status"] = params["status"]
    summary["input_sha256"] = {"matrix": sha256(args.matrix),
                                "weights": sha256(args.weights),
                                "parameters": sha256(args.parameters)}
    summary["preference_rationale"] = params["thresholds_rationale"]
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "electre_i_resumo.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    with (args.out / "electre_i_relacoes.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "a", "b", "concordancia_ab", "concordancia_ba", "vetos_ab", "vetos_ba",
            "sobreclassifica_ab", "sobreclassifica_ba", "situacao"
        ])
        writer.writeheader()
        writer.writerows(details)
    print(f"Alternativas: {summary['alternative_count']}; pares: {summary['unordered_pairs']}")
    print(f"Arcos de sobreclassificação: {summary['outranking_arcs']}")
    print(f"Pares incomparáveis: {summary['pair_types']['incomparaveis']}")
    print("Não sobreclassificadas por nenhuma:", ", ".join(summary["not_outranked_by_any"]))
    if summary["choice_kernel"] is not None:
        print("Núcleo de escolha:", ", ".join(summary["choice_kernel"]))
    else:
        print("Grafo cíclico residual: não foi declarado núcleo de escolha.")
    print("Cenário:", params["status"])


if __name__ == "__main__":
    main()
