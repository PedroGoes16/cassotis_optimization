"""D027: sensibilidade reproducivel PROMETHEE I/II com D023, D024 e D026.

Exemplo (checkout do repositorio):
    python scripts/analyze_promethee_sensitivity.py

Gera dois CSVs e um JSON sem modificar matriz, pesos AHP ou parametros-base.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from cassotis_optimization.mcda.promethee import CRITERIA, promethee_i_ii

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parameters_at(q_fraction: float, p_fraction: float) -> dict[str, dict[str, Any]]:
    """Uma hipotese uniforme relativa a amplitude observada em cada criterio."""
    if not (math.isfinite(q_fraction) and math.isfinite(p_fraction)
            and 0 <= q_fraction < p_fraction <= 1):
        raise ValueError("Limiares devem obedecer 0 <= q < p <= 1")
    return {
        k: {
            "function": "v_shape_with_indifference",
            "q_fraction_of_observed_range": q_fraction,
            "p_fraction_of_observed_range": p_fraction,
        }
        for k in CRITERIA
    }


def _weights_with_cost_share(original: dict[str, float], share: float) -> dict[str, float]:
    """Perturbacao contrafactual: alterar custo e redistribuir outros proporcionalmente."""
    if not math.isfinite(share) or not (0 < share < 1):
        raise ValueError("Peso de custo deve estar entre 0 e 1 (exclusivos)")
    if set(original) != set(CRITERIA) or not math.isclose(sum(original.values()), 1, abs_tol=1e-10):
        raise ValueError("Pesos AHP incompletos ou sem soma unitaria")
    remaining_old = sum(original[k] for k in CRITERIA if k != "f1")
    if remaining_old <= 0:
        raise ValueError("Os outros criterios precisam ter pesos positivos")
    weights = {
        k: (share if k == "f1" else original[k] * (1 - share) / remaining_old)
        for k in CRITERIA
    }
    assert math.isclose(sum(weights.values()), 1, abs_tol=1e-10)
    return weights


def _report_for(
    scenario_id: str,
    label: str,
    q_fraction: float,
    p_fraction: float,
    alternatives: list[dict[str, str]],
    weights: dict[str, float],
) -> dict[str, Any]:
    summary, ranking, _ = promethee_i_ii(
        alternatives, weights, _parameters_at(q_fraction, p_fraction)
    )
    by_id = {r["alternative_id"]: r for r in ranking}
    if not {"A020", "A016", "A002"}.issubset(by_id):
        raise ValueError("Faltam alternativas de referencia oficiais")
    return {
        "cenario": scenario_id,
        "descricao": label,
        "q_frac": q_fraction,
        "p_frac": p_fraction,
        "peso_f1": weights["f1"],
        "peso_f2": weights["f2"],
        "peso_f3": weights["f3"],
        "peso_c4": weights["c4"],
        "primeiro": ranking[0]["alternative_id"],
        "segundo": ranking[1]["alternative_id"],
        "terceiro": ranking[2]["alternative_id"],
        "phi_primeiro": ranking[0]["phi_net"],
        "margem_primeiro_segundo": ranking[0]["phi_net"] - ranking[1]["phi_net"],
        "posicao_A020": by_id["A020"]["rank_promethee_ii"],
        "posicao_A016": by_id["A016"]["rank_promethee_ii"],
        "posicao_A002": by_id["A002"]["rank_promethee_ii"],
        "phi_A020": by_id["A020"]["phi_net"],
        "phi_A016": by_id["A016"]["phi_net"],
        "phi_A002": by_id["A002"]["phi_net"],
        "incomparaveis_promethee_i": summary["promethee_i_pair_types"]["incomparaveis"],
        "nao_superadas_promethee_i": ";".join(summary["promethee_i_unbeaten"]),
    }


def analyze(
    alternatives: list[dict[str, str]],
    ahp_weights: dict[str, float],
    base_preference_parameters: dict[str, dict[str, Any]],
    protocol: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Permite testar sem ler/escrever arquivos; nenhuma entrada e modificada."""
    if len(alternatives) != 91 or len({row["alternative_id"] for row in alternatives}) != 91:
        raise ValueError("A analise oficial exige 91 alternativas identificadas distintamente")
    expected = protocol["baseline"]
    q0, p0 = expected["q_fraction"], expected["p_fraction"]
    for k in CRITERIA:
        p = base_preference_parameters[k]
        if (p.get("function") != "v_shape_with_indifference"
                or not math.isclose(float(p["q_fraction_of_observed_range"]), q0, abs_tol=1e-12)
                or not math.isclose(float(p["p_fraction_of_observed_range"]), p0, abs_tol=1e-12)):
            raise ValueError("O arquivo de parametros da D026 nao corresponde ao baseline do protocolo")

    original = deepcopy(ahp_weights)
    thresholds: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for s in protocol["threshold_scenarios"]:
        if s["id"] in seen_ids:
            raise ValueError("IDs de cenarios repetidos")
        seen_ids.add(s["id"])
        thresholds.append(_report_for(
            s["id"], s["label"], float(s["q"]), float(s["p"]),
            alternatives, original,
        ))

    weights: list[dict[str, Any]] = []
    for cost_share in protocol["cost_weight_scenarios"]:
        share = float(cost_share)
        varied = _weights_with_cost_share(original, share)
        weights.append(_report_for(
            f"W{int(round(share*100)):02d}",
            f"Custo {share:.0%}; demais criterios proporcionais ao AHP",
            q0, p0, alternatives, varied,
        ))

    baseline_matches = [s for s in thresholds if s["q_frac"] == q0 and s["p_frac"] == p0]
    if len(baseline_matches) != 1:
        raise ValueError("O protocolo deve conter o cenário-base exatamente uma vez")
    base = baseline_matches[0]
    findings: dict[str, Any] = {
        "decision_id": "D027",
        "status": "SENSIBILIDADE_EXECUTADA_CENARIO_ACADEMICO",
        "alternative_count": len(alternatives),
        "threshold_scenario_count": len(thresholds),
        "weight_scenario_count": len(weights),
        "base_top1": base["primeiro"],
        "base_phi_top1": base["phi_primeiro"],
        "winner_is_stable_across_thresholds": len({x["primeiro"] for x in thresholds}) == 1,
        "threshold_winners": sorted({x["primeiro"] for x in thresholds}),
        "threshold_second_positions_of_A016": [s["posicao_A016"] for s in thresholds],
        "threshold_ranges": {
            "q_min": min(x["q_frac"] for x in thresholds),
            "q_max": max(x["q_frac"] for x in thresholds),
            "p_min": min(x["p_frac"] for x in thresholds),
            "p_max": max(x["p_frac"] for x in thresholds),
        },
        "weight_winners": {f"{x['peso_f1']:.2f}": x["primeiro"] for x in weights},
        "sensitivity_conclusions": [
            "Robustez observada apenas no conjunto discreto de cenarios explorados, nao em todas as preferencias possiveis.",
            "Limiares relativos sao hipoteses academicas sem calibracao operacional externa.",
            "Cenarios de pesos sao contrafactuais; matriz AHP D024 permanece inalterada.",
            "Os fluxos e posicoes PROMETHEE dependem das 91 alternativas em conjunto.",
        ],
    }
    assert original == ahp_weights
    return thresholds, weights, findings


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("Lista de cenarios vazia")
    with path.open("w", encoding="utf-8", newline="") as h:
        writer = csv.DictWriter(h, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=ROOT / "results/mcda/matriz_decisao.csv")
    parser.add_argument("--weights", type=Path, default=ROOT / "results/mcda/pesos_ahp.json")
    parser.add_argument("--parameters", type=Path, default=ROOT / "data/parametros_promethee.json")
    parser.add_argument("--protocol", type=Path, default=ROOT / "data/protocolo_sensibilidade_promethee.json")
    parser.add_argument("--out", type=Path, default=ROOT / "results/mcda")
    args = parser.parse_args()

    with args.matrix.open(encoding="utf-8", newline="") as h:
        matrix = list(csv.DictReader(h))
    ahp = json.loads(args.weights.read_text(encoding="utf-8"))
    params = json.loads(args.parameters.read_text(encoding="utf-8"))
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    if ahp.get("consistent") is not True:
        raise ValueError("Os pesos AHP devem passar no teste de consistencia D024")
    if tuple(ahp["criterion_order"]) != CRITERIA or tuple(params["criterion_order"]) != CRITERIA:
        raise ValueError("Ordem dos criterios divergente")
    limiares, pesos, resumo = analyze(
        matrix, ahp["weights"], params["preference_parameters"], protocol
    )
    resumo["input_sha256"] = {
        "matrix": _sha256(args.matrix),
        "weights": _sha256(args.weights),
        "parameters": _sha256(args.parameters),
        "protocol": _sha256(args.protocol),
    }
    args.out.mkdir(parents=True, exist_ok=True)
    _write_csv(args.out / "sensibilidade_promethee_limiares.csv", limiares)
    _write_csv(args.out / "sensibilidade_promethee_pesos.csv", pesos)
    (args.out / "sensibilidade_promethee_resumo.json").write_text(
        json.dumps(resumo, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print("D027 — sensibilidade PROMETHEE I/II")
    print("Limiar q/p, pesos AHP fixos:")
    for row in limiares:
        print(f"  {row['cenario']} q={row['q_frac']:.0%} p={row['p_frac']:.0%}: "
              f"1º={row['primeiro']}, 2º={row['segundo']}; "
              f"incomparaveis={row['incomparaveis_promethee_i']}")
    print("Peso custo variado, limiares q/p fixos em 1%/25%:")
    for row in pesos:
        print(f"  {row['cenario']} custo={row['peso_f1']:.0%}: "
              f"1º={row['primeiro']}; A020={row['posicao_A020']}º")
    print("CSV/JSON gravados em", args.out)


if __name__ == "__main__":
    main()
