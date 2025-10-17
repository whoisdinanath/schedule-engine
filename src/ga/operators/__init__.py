"""
GA Operators Package

Exports genetic operators and repair heuristics.
"""

from src.ga.operators.mutation import mutate_individual, mutate_gene
from src.ga.operators.crossover import crossover_course_group_aware, crossover_uniform
from src.ga.operators.repair import repair_individual
from src.ga.operators.repair_registry import (
    get_all_repair_heuristics,
    get_enabled_repair_heuristics,
    get_repair_statistics_template,
)

__all__ = [
    # Mutation operators
    "mutate_individual",
    "mutate_gene",
    # Crossover operators
    "crossover_course_group_aware",
    "crossover_uniform",
    # Repair operators
    "repair_individual",
    # Repair registry
    "get_all_repair_heuristics",
    "get_enabled_repair_heuristics",
    "get_repair_statistics_template",
]
