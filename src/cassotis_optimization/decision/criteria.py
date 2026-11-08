"""Additional decision criteria that are not optimization objectives."""

from __future__ import annotations

from collections import defaultdict

from cassotis_optimization.domain import ProblemInstance
from cassotis_optimization.solution import Solution


def recipe_heterogeneity(solution: Solution, instance: ProblemInstance) -> float:
    """Mean squared distance from each pile recipe to its group mean recipe.

    A recipe is the vector of mineral mass proportions in a pile. Because every
    truck has the same capacity, truck-count proportions are exactly mass
    proportions. The value is zero when all piles feeding each equipment have
    the same recipe and increases as their compositions diverge.

    Each pile has the same operational importance in the average, irrespective
    of its total mass. The criterion is minimized.
    """
    counts = solution.counts_by_pile()
    piles_by_group: dict[str, list[str]] = defaultdict(list)
    for pile_id, pile in instance.piles.items():
        piles_by_group[pile.group_id].append(pile_id)

    squared_distances: list[float] = []
    mineral_ids = tuple(instance.minerals)
    for pile_ids in piles_by_group.values():
        recipes: list[dict[str, float]] = []
        for pile_id in pile_ids:
            total = instance.piles[pile_id].n_trucks
            recipes.append(
                {mineral_id: counts[pile_id][mineral_id] / total for mineral_id in mineral_ids}
            )

        mean_recipe = {
            mineral_id: sum(recipe[mineral_id] for recipe in recipes) / len(recipes)
            for mineral_id in mineral_ids
        }
        squared_distances.extend(
            sum(
                (recipe[mineral_id] - mean_recipe[mineral_id]) ** 2
                for mineral_id in mineral_ids
            )
            for recipe in recipes
        )

    if not squared_distances:
        raise ValueError("The instance must contain at least one pile")
    return sum(squared_distances) / len(squared_distances)
