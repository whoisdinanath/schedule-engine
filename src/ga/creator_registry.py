"""
Centralized DEAP creator registry for GA types.

This module initializes all DEAP creator types used throughout the GA pipeline.
Centralizing creator logic prevents duplicate registrations and ensures consistent
fitness function definitions across the codebase.

Usage:
    Import this module before using any creator types:
    >>> from src.ga.creator_registry import get_creator
    >>> creator = get_creator()
    >>> individual = creator.Individual([gene1, gene2, ...])
"""

from deap import creator, base


def _initialize_creator():
    """
    Initialize DEAP creator types if not already registered.

    Creates:
        - FitnessMulti: Multi-objective fitness with weights (-1.0, -0.01)
                        for hard and soft constraint minimization
        - Individual: List-based individual with FitnessMulti fitness

    Weights rationale:
        - Hard constraints: weight=-1.0 (strict violations)
        - Soft constraints: weight=-0.01 (normalized from ~500 range)
    """
    # Only create if not already registered (prevents DEAP re-registration errors)
    if not hasattr(creator, "FitnessMulti"):
        creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -0.01))

    if not hasattr(creator, "Individual"):
        creator.create("Individual", list, fitness=creator.FitnessMulti)


def get_creator():
    """
    Get the initialized DEAP creator instance.

    Returns:
        creator: DEAP creator with registered types (FitnessMulti, Individual)

    Example:
        >>> from src.ga.creator_registry import get_creator
        >>> creator = get_creator()
        >>> ind = creator.Individual()
    """
    _initialize_creator()
    return creator


# Auto-initialize on module import for convenience
_initialize_creator()
