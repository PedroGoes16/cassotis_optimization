"""D026 — PROMETHEE I/II com preferências graduais, rastreável e independente da GVNS.

Todas as funções f1/f2/f3/c4 são minimizadas. Para cada (a,b),
melhoria_j(a,b) = g_j(b) - g_j(a) > 0 favorece a.

PROMETHEE I: ordenação parcial pelos fluxos de saída/entrada.
PROMETHEE II: ordenação completa pelo fluxo líquido.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

CRITERIA = ("f1", "f2", "f3", "c4")
EPS = 1e-12


def v_shape_with_indifference(improvement: float, q: float, p: float) -> float:
    """Função tipo V com indiferença: 0 em d<=q; 1 em d>=p; linear no meio.

    A função é aplicada a uma *melhoria* (critério de minimização):
    melhoria(a,b) = desempenho(b) - desempenho(a).
    """
    if not (math.isfinite(improvement) and math.isfinite(q) and math.isfinite(p)):
        raise ValueError("Melhoria e limiares precisam ser finitos.")
    if not (0 <= q < p):
        raise ValueError("Limiar inválido: necessário 0 <= q < p.")
    if improvement <= q:
        return 0.0
    if improvement >= p:
        return 1.0
    return (improvement - q) / (p - q)


def _validate_inputs(
    alternatives: Sequence[Mapping[str, Any]],
    weights: Mapping[str, float],
    preference_parameters: Mapping[str, Mapping[str, Any]],
) -> tuple[list[str], list[dict[str, float]], dict[str, float], dict[str, dict[str, float]]]:
    if len(alternatives) < 2:
        raise ValueError("PROMETHEE exige pelo menos duas alternativas.")
    if set(weights) != set(CRITERIA):
        raise ValueError("Os pesos precisam identificar f1/f2/f3/c4 exatamente.")
    if set(preference_parameters) != set(CRITERIA):
        raise ValueError("Os parâmetros precisam identificar f1/f2/f3/c4 exatamente.")
    if any(not isinstance(w, (int, float)) or not math.isfinite(w) or w <= 0
           for w in weights.values()):
        raise ValueError("Pesos devem ser positivos e finitos.")
    if not math.isclose(sum(weights.values()), 1.0, rel_tol=0, abs_tol=1e-10):
        raise ValueError("Pesos precisam somar 1 (não os re-normalizamos silenciosamente).")

    ids: list[str] = []
    data: list[dict[str, float]] = []
    for raw in alternatives:
        alt_id = raw.get("alternative_id")
        if not isinstance(alt_id, str) or not alt_id.strip():
            raise ValueError("Identificador de alternativa ausente ou inválido.")
        ids.append(alt_id)
        row: dict[str, float] = {}
        for criterion in CRITERIA:
            try:
                val = float(raw[criterion])
            except (TypeError, KeyError, ValueError) as exc:
                raise ValueError(f"Valor inválido: {alt_id}/{criterion}.") from exc
            if not math.isfinite(val):
                raise ValueError(f"Valor não finito: {alt_id}/{criterion}.")
            row[criterion] = val
        data.append(row)
    if len(set(ids)) != len(ids):
        raise ValueError("Identificadores de alternativas duplicados.")

    thresholds: dict[str, dict[str, float]] = {}
    for key in CRITERIA:
        setup = preference_parameters[key]
        if setup.get("function") != "v_shape_with_indifference":
            raise ValueError(f"Função de preferência não suportada para {key}.")
        try:
            q_fraction = float(setup["q_fraction_of_observed_range"])
            p_fraction = float(setup["p_fraction_of_observed_range"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"q/p ausentes ou inválidos para {key}.") from exc
        if not all(map(math.isfinite, (q_fraction, p_fraction))) or not (
            0 <= q_fraction < p_fraction <= 1
        ):
            raise ValueError(f"Limiares relativos precisam satisfazer 0<=q<p<=1: {key}.")
        observed = [row[key] for row in data]
        span = max(observed) - min(observed)
        # Critério constante é admitido: contribui preferência zero para todo par.
        thresholds[key] = {
            "observed_min": min(observed),
            "observed_max": max(observed),
            "observed_range": span,
            "q_fraction": q_fraction,
            "p_fraction": p_fraction,
            "q_absolute": q_fraction * span,
            "p_absolute": p_fraction * span,
        }
    return ids, data, {k: float(weights[k]) for k in CRITERIA}, thresholds


def _compare_flows(
    a_plus: float, a_minus: float, b_plus: float, b_minus: float
) -> str:
    """Comparação parcial PROMETHEE I, utilizando EPS apenas para ruído FP."""
    eq_plus = math.isclose(a_plus, b_plus, rel_tol=0, abs_tol=EPS)
    eq_minus = math.isclose(a_minus, b_minus, rel_tol=0, abs_tol=EPS)
    if eq_plus and eq_minus:
        return "indiferentes"
    a_dominates = (a_plus >= b_plus - EPS and a_minus <= b_minus + EPS)
    b_dominates = (b_plus >= a_plus - EPS and b_minus <= a_minus + EPS)
    if a_dominates and not b_dominates:
        return "a_preferida"
    if b_dominates and not a_dominates:
        return "b_preferida"
    return "incomparaveis"


def promethee_i_ii(
    alternatives: Sequence[Mapping[str, Any]],
    weights: Mapping[str, float],
    preference_parameters: Mapping[str, Mapping[str, Any]],
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Calcula ambos os métodos sobre as mesmas alternativas e parâmetros.

    Retorna: resumo, ranking PROMETHEE II, pares PROMETHEE I.
    A classificação do PROMETHEE I é fundamentada nos fluxos; o ranking II
    nunca é reaproveitado para inventar preferência em I.
    """
    ids, data, ws, thresholds = _validate_inputs(alternatives, weights, preference_parameters)
    n = len(ids)
    pos_sums = [0.0] * n
    neg_sums = [0.0] * n

    # Preferências direcionais agregadas por comparação de duas alternativas.
    for i in range(n):
        for j in range(i + 1, n):
            p_ij = p_ji = 0.0
            for key in CRITERIA:
                info = thresholds[key]
                span = info["observed_range"]
                if span == 0:
                    continue
                d_ij = data[j][key] - data[i][key]
                q_abs, p_abs = info["q_absolute"], info["p_absolute"]
                p_ij += ws[key] * v_shape_with_indifference(d_ij, q_abs, p_abs)
                p_ji += ws[key] * v_shape_with_indifference(-d_ij, q_abs, p_abs)
            pos_sums[i] += p_ij
            neg_sums[j] += p_ij
            pos_sums[j] += p_ji
            neg_sums[i] += p_ji

    flows = []
    for i, alt_id in enumerate(ids):
        phi_pos = pos_sums[i] / (n - 1)
        phi_neg = neg_sums[i] / (n - 1)
        flows.append({
            "alternative_id": alt_id,
            "phi_positive": phi_pos,
            "phi_negative": phi_neg,
            "phi_net": phi_pos - phi_neg,
            **data[i],
        })

    ordered = sorted(flows, key=lambda v: (-v["phi_net"], v["alternative_id"]))
    for i, item in enumerate(ordered):
        # Competição com empates: mesmo fluxo líquido em EPS => mesma posição.
        if i and math.isclose(item["phi_net"], ordered[i - 1]["phi_net"],
                              rel_tol=0, abs_tol=EPS):
            item["rank_promethee_ii"] = ordered[i - 1]["rank_promethee_ii"]
        else:
            item["rank_promethee_ii"] = i + 1

    counts = {"a_preferida": 0, "b_preferida": 0, "indiferentes": 0, "incomparaveis": 0}
    pairs = []
    has_incoming_preference = {alt_id: False for alt_id in ids}
    for i in range(n):
        for j in range(i + 1, n):
            a, b = flows[i], flows[j]
            relation = _compare_flows(
                a["phi_positive"], a["phi_negative"],
                b["phi_positive"], b["phi_negative"],
            )
            counts[relation] += 1
            if relation == "a_preferida":
                has_incoming_preference[b["alternative_id"]] = True
            elif relation == "b_preferida":
                has_incoming_preference[a["alternative_id"]] = True
            pairs.append({
                "a": ids[i], "b": ids[j],
                "phi_positive_a": a["phi_positive"],
                "phi_negative_a": a["phi_negative"],
                "phi_positive_b": b["phi_positive"],
                "phi_negative_b": b["phi_negative"],
                "relation_promethee_i": relation,
            })

    summary: dict[str, Any] = {
        "method": "PROMETHEE I/II",
        "description": "I: relacao parcial (fluxos separados); II: ranking (fluxo liquido)",
        "alternative_count": n,
        "unordered_pairs": len(pairs),
        "criterion_order": list(CRITERIA),
        "weights": ws,
        "criteria_direction": "min",
        "preference_function": "v_shape_with_indifference",
        "observed_thresholds": thresholds,
        "promethee_i_pair_types": counts,
        "promethee_i_unbeaten": [a["alternative_id"] for a in ordered
                                 if not has_incoming_preference[a["alternative_id"]]],
        "promethee_ii_top": [
            {k: item[k] for k in ("alternative_id", "rank_promethee_ii", "phi_positive",
                                      "phi_negative", "phi_net")}
            for item in ordered[:10]
        ],
        "zero_sum_net_flow": sum(item["phi_net"] for item in flows),
        "note": (
            "Limiar q/p relativo a amplitude observada nao resulta dos pesos AHP. "
            "PROMETHEE I pode registrar incomparabilidade mesmo quando II ordena o par. "
            "A ordenacao depende do conjunto de alternativas e dos parametros de preferencia."
        ),
    }
    return summary, ordered, pairs
