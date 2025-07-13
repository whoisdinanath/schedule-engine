from deap import creator, base, tools
import random
from typing import Any, List


def register_individual_classes():
    """
    Register individual classes for the genetic algorithm.
    """
    creator.create("FitnessMax", base.Fitness, weights=(1.0,))  # for minimization
    creator.create("Individual", list, fitness=creator.FitnessMax)


def setup_toolbox(individual_generator_fn) -> base.Toolbox:
    """
    Returns a DEAP toolbox with registered functions


    Args:
        individual_generator_fn (callable): A function to generate one individuals.

    Returns:
        base.Toolbox: A DEAP toolbox with registered functions.
    """

    toolbox = base.Toolbox()
    toolbox.register(
        "individual", tools.initIterate, creator.Individual, individual_generator_fn
    )
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    return toolbox
