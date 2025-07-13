import random
from typing import List, Tuple
from deap import tools


def custom_crossover(ind1, ind2):
    """
    Simple one point crossover for the course timetable genome
    """
    return tools.cxOnePoint(ind1, ind2)


def custom_mutation(individual, qts_max_quanta: int):
    """Mutate an individual's time assignments randomly.
    This mutation randomly changes the time of one session in the individual's schedule.

    Args:
        individual (SessionGene): The individual to mutate.
        qts_max_quanta (int): The maximum number of quanta.
    """
    for i in range(len(individual)):
        if random.random() < 0.1:
            time, room, inst = individual[i]
            new_time = random.randint(0, qts_max_quanta - 1)
            individual[i] = (new_time, room, inst)
    return (individual,)
