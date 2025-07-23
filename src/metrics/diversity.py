from src.ga.sessiongene import SessionGene
from typing import List


def gene_distance(g1: SessionGene, g2: SessionGene) -> float:
    """
    Computes a normalized distance between two SessionGene objects.
    Each differing field adds 1 point; result is normalized to [0, 1].

    Args:
        g1, g2: SessionGene objects.

    Returns:
        float: Normalized gene difference.
    """
    score = 0
    if g1.course_id != g2.course_id:
        score += 1
    if g1.instructor_id != g2.instructor_id:
        score += 1
    if g1.group_id != g2.group_id:
        score += 1
    if g1.room_id != g2.room_id:
        score += 1
    if set(g1.quanta) != set(g2.quanta):
        score += 1
    return score / 5  # Normalize to [0, 1]


def individual_distance(ind1: List[SessionGene], ind2: List[SessionGene]) -> float:
    """
    Computes the average gene-level distance between two individuals.

    Args:
        ind1, ind2: Lists of SessionGene objects representing two individuals.

    Returns:
        float: Average distance between corresponding genes.
    """
    return sum(gene_distance(g1, g2) for g1, g2 in zip(ind1, ind2)) / len(ind1)


def average_pairwise_diversity(population: List[List[SessionGene]]) -> float:
    """
    Calculates the average pairwise diversity in a population.

    Args:
        population: List of individuals, each being a list of SessionGene.

    Returns:
        float: Average pairwise distance between individuals.
    """
    total = 0
    count = 0

    for i in range(len(population)):
        for j in range(i + 1, len(population)):
            total += individual_distance(population[i], population[j])
            count += 1
    return total / count if count else 0
