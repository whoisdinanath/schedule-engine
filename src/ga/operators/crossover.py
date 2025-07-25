import random
from typing import List
from src.ga.sessiongene import SessionGene


def crossover_uniform(
    ind1: List[SessionGene], ind2: List[SessionGene], cx_prob: float = 0.5
):
    """
    Performs Uniform Crossover Between Two Individual Chromosomes

    Args:
        ind1, ind2 (List[SessionGene]): Two individuals to perform crossover on.
        cx_prob (float): Probability of crossover for each gene.

    """
    for i in range(len(ind1)):
        if random.random() < cx_prob:
            # Swap genes between the two individuals
            ind1[i], ind2[i] = ind2[i], ind1[i]

    return ind1, ind2  # Return after processing ALL genes
