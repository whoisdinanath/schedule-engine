from typing import List, TYPE_CHECKING
from src.ga.sessiongene import SessionGene
from src.ga.creator_registry import get_creator

# Get centralized creator instance
creator = get_creator()

if TYPE_CHECKING:
    from deap.creator import Individual as IndividualType


def create_individual(gene_list: List[SessionGene]):
    """
    Wraps a list of SessionGene Objects into a DEAP Individual.

    Args:
        gene_list (List[SessionGene]): List of SessionGene objects representing the individual's genes.

    Returns:
        creator.Individual: A new individual initialized with the provided genes.
    """
    return creator.Individual(gene_list)
