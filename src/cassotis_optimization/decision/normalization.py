"""Fixed min-max scaling for a finite multicriteria alternative set."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class MinMaxScale:
    minimum: dict[str, float]
    maximum: dict[str, float]


def fit_minmax(rows: Sequence[Mapping[str, float]], criteria: Sequence[str]) -> MinMaxScale:
    if not rows:
        raise ValueError("At least one alternative is required")
    minimum = {criterion: min(float(row[criterion]) for row in rows) for criterion in criteria}
    maximum = {criterion: max(float(row[criterion]) for row in rows) for criterion in criteria}
    return MinMaxScale(minimum=minimum, maximum=maximum)


def normalize_rows(
    rows: Sequence[Mapping[str, float]],
    criteria: Sequence[str],
    scale: MinMaxScale | None = None,
) -> tuple[list[dict[str, float]], MinMaxScale]:
    """Normalize minimization criteria to [0, 1], where zero is best."""
    fitted = scale or fit_minmax(rows, criteria)
    normalized: list[dict[str, float]] = []
    for row in rows:
        item: dict[str, float] = {}
        for criterion in criteria:
            lower = fitted.minimum[criterion]
            upper = fitted.maximum[criterion]
            width = upper - lower
            item[criterion] = 0.0 if width == 0 else (float(row[criterion]) - lower) / width
        normalized.append(item)
    return normalized, fitted
