"""PROMETHEE II with linear preference and indifference thresholds."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class PrometheeResult:
    positive_flow: tuple[float, ...]
    negative_flow: tuple[float, ...]
    net_flow: tuple[float, ...]
    ranking: tuple[int, ...]


def _validate(
    rows: Sequence[Mapping[str, float]],
    weights: Mapping[str, float],
    q: Mapping[str, float],
    p: Mapping[str, float],
) -> None:
    if len(rows) < 2:
        raise ValueError("PROMETHEE II requires at least two alternatives")
    if not weights or any(weight < 0 for weight in weights.values()):
        raise ValueError("Weights must be non-negative and non-empty")
    if sum(weights.values()) <= 0:
        raise ValueError("At least one weight must be positive")
    for criterion in weights:
        if criterion not in q or criterion not in p or q[criterion] < 0 or p[criterion] <= q[criterion]:
            raise ValueError(f"Invalid q/p thresholds for {criterion}")
        if any(criterion not in row for row in rows):
            raise KeyError(f"Missing criterion {criterion}")


def _preference(difference: float, q: float, p: float) -> float:
    if difference <= q:
        return 0.0
    if difference >= p:
        return 1.0
    return (difference - q) / (p - q)


def promethee_ii(
    rows: Sequence[Mapping[str, float]],
    weights: Mapping[str, float],
    q: Mapping[str, float],
    p: Mapping[str, float],
) -> PrometheeResult:
    """Rank alternatives for minimization criteria using PROMETHEE II.

    ``rows`` should normally contain normalized criterion values. For a pair
    (a, b), positive differences ``b - a`` mean that a is preferable because
    every criterion is minimized.
    """
    _validate(rows, weights, q, p)
    total_weight = sum(weights.values())
    n = len(rows)
    preference = [[0.0] * n for _ in range(n)]
    for a in range(n):
        for b in range(n):
            if a == b:
                continue
            preference[a][b] = sum(
                weights[criterion]
                * _preference(rows[b][criterion] - rows[a][criterion], q[criterion], p[criterion])
                for criterion in weights
            ) / total_weight

    positive = tuple(sum(preference[a]) / (n - 1) for a in range(n))
    negative = tuple(sum(preference[b][a] for b in range(n)) / (n - 1) for a in range(n))
    net = tuple(positive[a] - negative[a] for a in range(n))
    ranking = tuple(sorted(range(n), key=lambda index: (-net[index], index)))
    return PrometheeResult(positive, negative, net, ranking)
