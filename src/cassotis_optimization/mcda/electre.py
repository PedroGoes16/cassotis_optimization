"""ELECTRE I (D025): concordância ponderada, veto e núcleo de sobreclassificação.

Todos os critérios são de minimização. A matriz de decisões é um conjunto de
alternativas fixo, sem reexecutar a GVNS. Os limiares são preferências, não são
ajustados automaticamente para favorecer uma alternativa.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

CRITERIA = ("f1", "f2", "f3", "c4")


def _check_inputs(
    alternatives: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    concordance_threshold: float,
    veto_fractions: Mapping[str, float],
) -> tuple[list[str], dict[str, float], dict[str, float], dict[str, float]]:
    if len(alternatives) < 2:
        raise ValueError("ELECTRE exige pelo menos duas alternativas.")
    if set(weights) != set(CRITERIA) or set(veto_fractions) != set(CRITERIA):
        raise ValueError("Os pesos e os vetos devem identificar exatamente f1, f2, f3 e c4.")
    if not math.isfinite(concordance_threshold) or not 0.5 < concordance_threshold <= 1:
        raise ValueError("O limiar de concordância deve estar em (0,5; 1].")
    if any(not math.isfinite(v) or v <= 0 for v in weights.values()):
        raise ValueError("Os pesos devem ser finitos e positivos.")
    if not math.isclose(sum(weights.values()), 1.0, abs_tol=1e-10, rel_tol=0):
        raise ValueError("Os pesos devem somar 1.")
    if any(not math.isfinite(v) or not 0 < v <= 1 for v in veto_fractions.values()):
        raise ValueError("Cada veto relativo deve estar em (0; 1].")

    ids: list[str] = []
    values_by_key: dict[str, list[float]] = {k: [] for k in CRITERIA}
    for row in alternatives:
        alternative_id = row.get("alternative_id")
        if not isinstance(alternative_id, str) or not alternative_id:
            raise ValueError("Toda alternativa deve possuir um identificador não vazio.")
        ids.append(alternative_id)
        for key in CRITERIA:
            try:
                value = float(row[key])
            except (KeyError, ValueError, TypeError) as exc:
                raise ValueError(f"Critério inválido {key} em {alternative_id}.") from exc
            if not math.isfinite(value):
                raise ValueError(f"Valor não finito de {key} em {alternative_id}.")
            values_by_key[key].append(value)
    if len(set(ids)) != len(ids):
        raise ValueError("Identificadores de alternativas repetidos.")
    ranges = {k: max(v) - min(v) for k, v in values_by_key.items()}
    if any(delta <= 0 for delta in ranges.values()):
        raise ValueError("Todo critério precisa variar na matriz para normalizar seu veto.")
    absolute_vetos = {k: ranges[k] * veto_fractions[k] for k in CRITERIA}
    return ids, {k: float(weights[k]) for k in CRITERIA}, ranges, absolute_vetos


def _acyclic_choice_kernel(relation: Sequence[Sequence[bool]]) -> dict:
    """Núcleo por eliminação sucessiva das fontes; válido somente se o grafo for acíclico.

    Fontes = nós sem arcos de entrada no grafo residual. Em cada rodada,
    incluem-se as fontes no núcleo e removem-se seus sucessores diretos.
    Em um DAG, isso garante independência interna e cobertura externa.
    Ciclos restantes são explicitados, sem apresentar um falso núcleo.
    """
    n = len(relation)
    remaining = set(range(n))
    chosen: list[int] = []
    waves: list[dict] = []
    while remaining:
        sources = sorted(i for i in remaining if not any(relation[j][i] for j in remaining))
        if not sources:
            return {"acyclic": False, "kernel_indices": None,
                    "cyclic_residue_indices": sorted(remaining), "waves": waves}
        removed = set(sources)
        for i in sources:
            removed.update(j for j in remaining if relation[i][j])
        chosen.extend(sources)
        waves.append({"sources_indices": sources, "removed_count": len(removed)})
        remaining -= removed

    selected = set(chosen)
    if any(relation[i][j] for i in chosen for j in chosen if i != j):
        raise AssertionError("O núcleo calculado não é internamente independente.")
    if any(not any(relation[i][j] for i in chosen) for j in range(n) if j not in selected):
        raise AssertionError("O núcleo calculado não cobre todas as outras alternativas.")
    return {"acyclic": True, "kernel_indices": chosen,
            "cyclic_residue_indices": [], "waves": waves}


def electre_i(
    alternatives: Sequence[Mapping[str, object]],
    weights: Mapping[str, float],
    concordance_threshold: float,
    veto_fractions: Mapping[str, float],
) -> tuple[dict, list[dict]]:
    """Retorna diagnóstico e todas as comparações não ordenadas, sem ranking artificial.

    Concordância: soma de w_j onde f_j(a) <= f_j(b).
    Veto: se f_j(a)-f_j(b) > v_j * (max_j-min_j), bloqueia aSb.
    Sobreclassificação: C(a,b) >= limiar e nenhum veto.
    """
    ids, ws, ranges, veto_abs = _check_inputs(
        alternatives, weights, concordance_threshold, veto_fractions
    )
    n = len(ids)
    data = [{k: float(row[k]) for k in CRITERIA} for row in alternatives]
    relation = [[False] * n for _ in range(n)]
    details: list[dict] = []
    vetoed_after_concordance = 0
    approved_by_concordance = 0
    for i in range(n):
        for j in range(i + 1, n):
            a, b = data[i], data[j]
            c_ab = sum(ws[k] for k in CRITERIA if a[k] <= b[k])
            c_ba = sum(ws[k] for k in CRITERIA if b[k] <= a[k])
            veto_ab = [k for k in CRITERIA if a[k] - b[k] > veto_abs[k] + 1e-12]
            veto_ba = [k for k in CRITERIA if b[k] - a[k] > veto_abs[k] + 1e-12]
            admissible_ab = c_ab >= concordance_threshold - 1e-12
            admissible_ba = c_ba >= concordance_threshold - 1e-12
            approved_by_concordance += int(admissible_ab) + int(admissible_ba)
            vetoed_after_concordance += int(admissible_ab and bool(veto_ab))
            vetoed_after_concordance += int(admissible_ba and bool(veto_ba))
            s_ab = admissible_ab and not veto_ab
            s_ba = admissible_ba and not veto_ba
            relation[i][j] = s_ab
            relation[j][i] = s_ba
            if s_ab and s_ba:
                state = "sobreclassificacao_mutua"
            elif s_ab:
                state = "a_sobreclassifica_b"
            elif s_ba:
                state = "b_sobreclassifica_a"
            else:
                state = "incomparaveis"
            details.append({
                "a": ids[i], "b": ids[j],
                "concordancia_ab": c_ab, "concordancia_ba": c_ba,
                "vetos_ab": ";".join(veto_ab), "vetos_ba": ";".join(veto_ba),
                "sobreclassifica_ab": s_ab, "sobreclassifica_ba": s_ba,
                "situacao": state,
            })

    incoming = [sum(relation[j][i] for j in range(n)) for i in range(n)]
    outgoing = [sum(relation[i][j] for j in range(n)) for i in range(n)]
    kernel = _acyclic_choice_kernel(relation)
    groups = {kind: sum(x["situacao"] == kind for x in details) for kind in (
        "a_sobreclassifica_b", "b_sobreclassifica_a",
        "sobreclassificacao_mutua", "incomparaveis"
    )}
    summary = {
        "method": "ELECTRE I — concordancia e veto absoluto relativo a amplitude",
        "criteria": list(CRITERIA),
        "alternative_count": n,
        "unordered_pairs": len(details),
        "ordered_comparisons_passing_concordance": approved_by_concordance,
        "ordered_comparisons_vetoed": vetoed_after_concordance,
        "outranking_arcs": sum(outgoing),
        "pair_types": groups,
        "weights": ws,
        "concordance_threshold": float(concordance_threshold),
        "veto_relative_to_observed_range": {k: float(veto_fractions[k]) for k in CRITERIA},
        "observed_ranges": ranges,
        "veto_absolute": veto_abs,
        "not_outranked_by_any": [ids[i] for i, incoming_count in enumerate(incoming)
                                  if incoming_count == 0],
        "per_alternative": [
            {"alternative_id": ids[i], "incoming": incoming[i], "outgoing": outgoing[i]}
            for i in range(n)
        ],
        "graph_acyclic": kernel["acyclic"],
        "choice_kernel": ([ids[i] for i in kernel["kernel_indices"]]
                          if kernel["kernel_indices"] is not None else None),
        "cyclic_residue": [ids[i] for i in kernel["cyclic_residue_indices"]],
        "kernel_waves": [{"source_ids": [ids[i] for i in w["sources_indices"]],
                          "removed_count": w["removed_count"]} for w in kernel["waves"]],
        "caveat": (
            "O núcleo é uma seleção de escolha, não um ranking nem uma prova de ótima solução. "
            "Se o grafo tiver ciclos, este procedimento não declara núcleo e exige tratamento explícito."
        ),
    }
    return summary, details
