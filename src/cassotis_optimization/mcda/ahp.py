"""D024: pesos AHP e consistência com julgamentos rastreáveis.

Os julgamentos são subjetivos e fornecidos pelo grupo, não inferidos dos dados.
Os pesos adotados seguem o método de média das colunas normalizadas (SpiceLogic).
O CR utiliza o maior autovalor da matriz recíproca original.
"""

from __future__ import annotations

import math
from itertools import combinations
from typing import Any

import numpy as np

RI = {1: 0.0, 2: 0.0, 3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24,
      7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def pairwise_matrix(preferences: dict[str, Any]) -> tuple[tuple[str, ...], np.ndarray]:
    """Constrói a matriz usando cada uma das n(n-1)/2 comparações uma vez."""
    criteria = preferences["criteria"]
    ids = tuple(c["id"] for c in criteria)
    n = len(ids)
    if n < 2 or n > 10 or len(set(ids)) != n:
        raise ValueError("São necessários entre 2 e 10 critérios com IDs distintos.")
    if any(c.get("direction") != "min" for c in criteria):
        raise ValueError("Todos os critérios registrados neste cenário devem ser minimizados.")

    index = {name: i for i, name in enumerate(ids)}
    matrix = np.eye(n, dtype=float)
    seen: set[frozenset[str]] = set()
    for choice in preferences["comparisons"]:
        left, right = choice["left"], choice["right"]
        if left not in index or right not in index or left == right:
            raise ValueError(f"Comparação desconhecida ou inválida: {left}/{right}.")
        pair = frozenset((left, right))
        if pair in seen:
            raise ValueError(f"Comparação duplicada: {left}/{right}.")
        seen.add(pair)
        intensity = choice["intensity"]
        if type(intensity) is not int or intensity not in range(1, 10):
            raise ValueError("A intensidade Saaty deve ser inteira entre 1 e 9.")
        preferred = choice.get("preferred")
        if intensity == 1 and preferred is not None:
            raise ValueError("Empate (intensidade 1) deve ter preferred=null.")
        if intensity > 1 and preferred not in (left, right):
            raise ValueError("A preferência deve identificar exatamente um dos dois critérios.")
        if not str(choice.get("justification", "")).strip():
            raise ValueError(f"Justificativa ausente para {left}/{right}.")
        value = 1.0 if intensity == 1 else (
            float(intensity) if preferred == left else 1.0 / intensity
        )
        i, j = index[left], index[right]
        matrix[i, j] = value
        matrix[j, i] = 1.0 / value

    required = {frozenset(pair) for pair in combinations(ids, 2)}
    if seen != required:
        missing = sorted(tuple(sorted(pair)) for pair in required - seen)
        raise ValueError(f"Comparações par a par incompletas: {missing}.")
    return ids, matrix


def calculate_ahp(preferences: dict[str, Any]) -> dict[str, Any]:
    """Produz pesos (média de colunas), autovalor e razão de consistência."""
    ids, matrix = pairwise_matrix(preferences)
    n = len(ids)
    config = preferences["calculation"]
    if config["weights_method"] != "normalized_column_row_mean":
        raise ValueError("Método de pesos não suportado.")
    if config["consistency_method"] != "principal_eigenvalue":
        raise ValueError("Método de consistência não suportado.")
    normalized = matrix / matrix.sum(axis=0)
    weights = normalized.mean(axis=1)

    eigenvalues = np.linalg.eigvals(matrix)
    eigenvalue = max(float(value.real) for value in eigenvalues)
    if not np.isfinite(eigenvalue):
        raise ValueError("Autovalor não finito.")
    ci = max(0.0, (eigenvalue - n) / (n - 1))
    ri = RI[n]
    if n == 4 and not math.isclose(float(config["random_index_n4"]), ri):
        raise ValueError("RI informado diverge de 0,90 para quatro critérios.")
    cr = ci / ri if ri > 0 else 0.0
    threshold = float(config["maximum_consistency_ratio"])
    if not (0.0 < threshold <= 1.0):
        raise ValueError("Limite de consistência inválido.")

    return {
        "decision_id": preferences.get("decision_id", "D024"),
        "scenario": preferences["scenario"],
        "criterion_order": list(ids),
        "weights": {name: float(weights[i]) for i, name in enumerate(ids)},
        "matrix": matrix.tolist(),
        "normalized_matrix": normalized.tolist(),
        "weight_method": config["weights_method"],
        "lambda_max": eigenvalue,
        "consistency_index": ci,
        "random_index": ri,
        "consistency_ratio": cr,
        "maximum_consistency_ratio": threshold,
        "consistent": bool(cr <= threshold),
        "note": "CR usa autovalor principal; os pesos usam médias das colunas normalizadas.",
    }
