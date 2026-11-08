import pytest

from cassotis_optimization.decision.criteria import recipe_heterogeneity
from cassotis_optimization.domain import GroupSpec, Mineral, Pile, ProblemInstance
from cassotis_optimization.solution import Solution


def _instance() -> ProblemInstance:
    minerals = {
        "A": Mineral("A", 100, 60, 5, 1, 0, 4, True, False),
        "B": Mineral("B", 100, 60, 5, 1, 0, 4, True, False),
    }
    group = GroupSpec("Sinter1", 0, None, 100, 0, 5, 100, 0, 1, 100)
    piles = {
        "P1": Pile("P1", "Sinter1", 4),
        "P2": Pile("P2", "Sinter1", 4),
    }
    return ProblemInstance(minerals, {"Sinter1": group}, piles)


def test_equal_recipes_have_zero_heterogeneity() -> None:
    solution = Solution({"P1": ("A", "B"), "P2": ("A", "B")})
    assert recipe_heterogeneity(solution, _instance()) == pytest.approx(0.0)


def test_opposite_recipes_have_positive_known_heterogeneity() -> None:
    solution = Solution({"P1": ("A", "A"), "P2": ("B", "B")})
    assert recipe_heterogeneity(solution, _instance()) == pytest.approx(0.5)
