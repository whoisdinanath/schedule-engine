from deap import creator, base
from typing import List
from src.ga.sessiongene import SessionGene

# Fitness: Single objective as of now:
# Will implement multiobjective in next version :
# eaa muji kina chaldaina? ekchhin comment hanxu, pachchi kholxu

# Fitness: Single Objective, Minimizing Problem for PenaltyScoring
creator.create("FitnessMin", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.FitnessMin)


def create_individual(gene_list: List[SessionGene]) -> creator.Individual:
    """
    Wraps a lis tof SessionGene Objects into a DEAP Individual.
        Args:
            gene_list (List[SessionGene]): List of SessionGene objects representing the individual's genes.

        Returns:
            creator.Individual: A new individual initialized with the provided genes.
    """
    return creator.Individual(gene_list)
