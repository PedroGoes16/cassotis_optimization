"""ELECTRE III credibility relation and transparent exploitation rule."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ElectreResult:
    credibility: tuple[tuple[float, ...], ...]
    net_credibility: tuple[float, ...]
    ranking: tuple[int, ...]
    maximal: tuple[int, ...]
    incomparable_pairs: tuple[tuple[int, int], ...]


def _partial_concordance(disadvantage: float, q: float, p: float) -> float:
    if disadvantage <= q:
        return 1.0
    if disadvantage >= p:
        return 0.0
    return (p - disadvantage) / (p - q)


def _discordance(disadvantage: float, p: float, veto: float) -> float:
    if disadvantage <= p:
        return 0.0
    if disadvantage >= veto:
        return 1.0
    return (disadvantage - p) / (veto - p)


def electre_iii(
    rows: Sequence[Mapping[str, float]],
    weights: Mapping[str, float],
    q: Mapping[str, float],
    p: Mapping[str, float],
    veto: Mapping[str, float],
    *,
    credibility_cutoff: float = 0.65,
) -> ElectreResult:
    """Apply ELECTRE III to normalized minimization criteria.

    The credibility matrix follows the standard concordance-discordance
    construction. Its exploitation is explicit: ``a`` strictly outranks ``b``
    when credibility(a,b) reaches the cutoff and the reverse does not. Maximal
    alternatives have no strict predecessor. Net credibility provides a stable
    complete display ranking, but does not erase the reported incomparabilities.
    """
    if len(rows) < 2:
        raise ValueError("ELECTRE III requires at least two alternatives")
    if not 0 < credibility_cutoff <= 1:
        raise ValueError("credibility_cutoff must be in (0, 1]")
    if not weights or any(weight < 0 for weight in weights.values()) or sum(weights.values()) <= 0:
        raise ValueError("Weights must be non-negative with a positive sum")
    for criterion in weights:
        if (
            criterion not in q
            or criterion not in p
            or criterion not in veto
            or q[criterion] < 0
            or p[criterion] <= q[criterion]
            or veto[criterion] <= p[criterion]
        ):
            raise ValueError(f"Invalid q/p/veto thresholds for {criterion}")

    total_weight = sum(weights.values())
    n = len(rows)
    credibility = [[0.0] * n for _ in range(n)]
    for a in range(n):
        for b in range(n):
            if a == b:
                credibility[a][b] = 1.0
                continue
            concordances: dict[str, float] = {}
            discordances: dict[str, float] = {}
            for criterion in weights:
                disadvantage = rows[a][criterion] - rows[b][criterion]
                concordances[criterion] = _partial_concordance(
                    disadvantage, q[criterion], p[criterion]
                )
                discordances[criterion] = _discordance(
                    disadvantage, p[criterion], veto[criterion]
                )
            global_concordance = sum(
                weights[criterion] * concordances[criterion] for criterion in weights
            ) / total_weight
            sigma = global_concordance
            if global_concordance < 1.0:
                for criterion in weights:
                    discordance = discordances[criterion]
                    if discordance > global_concordance:
                        sigma *= (1.0 - discordance) / (1.0 - global_concordance)
            credibility[a][b] = sigma

    def strict(a: int, b: int) -> bool:
        return (
            credibility[a][b] >= credibility_cutoff
            and credibility[b][a] < credibility_cutoff
        )

    maximal = tuple(a for a in range(n) if not any(strict(b, a) for b in range(n) if b != a))
    incomparable = tuple(
        (a, b)
        for a in range(n)
        for b in range(a + 1, n)
        if credibility[a][b] < credibility_cutoff and credibility[b][a] < credibility_cutoff
    )
    net = tuple(
        sum(credibility[a][b] - credibility[b][a] for b in range(n) if b != a) / (n - 1)
        for a in range(n)
    )
    ranking = tuple(sorted(range(n), key=lambda index: (-net[index], index)))
    return ElectreResult(
        credibility=tuple(tuple(row) for row in credibility),
        net_credibility=net,
        ranking=ranking,
        maximal=maximal,
        incomparable_pairs=incomparable,
    )
