from deap import creator, base
from typing import List
from src.ga.sessiongene import SessionGene

# Fitness: Single objective as of now:
# Will implement multiobjective in next version :
# eaa muji kina chaldaina? ekchhin comment hanxu, pachchi kholxu


# In Future
# DEAP initializtion logic:
# yo creator.create bhanne logic lai; centralized garera: eutai
# creator_registry.py file ma rakhna parxa.

# Fitness: Single Objective, Minimizing Problem for PenaltyScoring
# creator.create("FitnessMin", base.Fitness, weights=(-1.0,))

#  MultiObjective Fitness: (Hard, Soft) Constraints;
# In Future Implement hasattr here.
# (-1.0, -0.1) normalized weight foro hard and soft constraints. Since, SC = 500 so normalize it by 0.01. to make
creator.create("FitnessMulti", base.Fitness, weights=(-1.0, -0.01))
creator.create("Individual", list, fitness=creator.FitnessMulti)


def create_individual(gene_list: List[SessionGene]) -> creator.Individual:
    """
    Wraps a lis tof SessionGene Objects into a DEAP Individual.
        Args:
            gene_list (List[SessionGene]): List of SessionGene objects representing the individual's genes.

        Returns:
            creator.Individual: A new individual initialized with the provided genes.
    """
    return creator.Individual(gene_list)
