import random
from typing import List
from src.ga.sessiongene import SessionGene


def crossover_course_group_aware(
    ind1: List[SessionGene], ind2: List[SessionGene], cx_prob: float = 0.5
):
    """
    Position-Independent Crossover that preserves (course, group) structure.

    Instead of swapping entire genes by index, this operator matches genes by their
    (course_id, group_ids) identity and swaps ONLY mutable attributes (instructor,
    room, time slots). This ensures the fundamental (course, group) enrollment
    structure is never corrupted, even if gene positions differ between individuals.

    CRITICAL: This is the recommended crossover for timetabling problems where
    chromosome structure represents fixed course-group enrollments. It enables
    future features like gene sorting, compaction, and clustering without risk
    of creating duplicate or missing (course, group) pairs.

    Args:
        ind1, ind2 (List[SessionGene]): Two individuals to perform crossover on.
        cx_prob (float): Probability of swapping attributes for each gene pair.
                        Default 0.5 means each gene has 50% chance of exchange.

    Returns:
        tuple: (ind1, ind2) with swapped attributes (not swapped genes)

    Raises:
        ValueError: If individuals have mismatched (course, group) pairs,
                   indicating structural corruption in the population.

    Example:
        Parent 1: Gene(MATH101, GroupA, Instructor=I1, Room=R1, Time=[10,11,12])
        Parent 2: Gene(MATH101, GroupA, Instructor=I2, Room=R2, Time=[20,21,22])

        After crossover (50% prob):
        Child 1:  Gene(MATH101, GroupA, Instructor=I2, Room=R2, Time=[20,21,22])
        Child 2:  Gene(MATH101, GroupA, Instructor=I1, Room=R1, Time=[10,11,12])

        Note: MATH101-GroupA still exists in both (no duplication/loss)
    """
    # Build lookup tables: (course_id, tuple(sorted(group_ids))) -> gene
    # We sort group_ids to ensure consistent key regardless of list order
    gene_map1 = {(gene.course_id, tuple(sorted(gene.group_ids))): gene for gene in ind1}
    gene_map2 = {(gene.course_id, tuple(sorted(gene.group_ids))): gene for gene in ind2}

    # Verify both individuals have same (course, group) pairs
    # This catches any corruption early with a clear error message
    keys1 = set(gene_map1.keys())
    keys2 = set(gene_map2.keys())

    if keys1 != keys2:
        missing_in_ind1 = keys2 - keys1
        missing_in_ind2 = keys1 - keys2
        raise ValueError(
            f"❌ CROSSOVER ERROR: Individuals have mismatched (course, group) pairs!\n"
            f"   Individual 1 has {len(keys1)} pairs, Individual 2 has {len(keys2)} pairs.\n"
            f"   Missing in Individual 1: {missing_in_ind1}\n"
            f"   Missing in Individual 2: {missing_in_ind2}\n"
            f"   This indicates population corruption or invalid mutation."
        )

    # For each (course, group) pair, probabilistically swap ATTRIBUTES
    # Note: We iterate over keys1, but could use keys2 (they're identical)
    for key in gene_map1.keys():
        if random.random() < cx_prob:
            gene1 = gene_map1[key]
            gene2 = gene_map2[key]

            # Swap ONLY mutable attributes (NOT course_id or group_ids)
            # This preserves the fundamental chromosome structure
            gene1.instructor_id, gene2.instructor_id = (
                gene2.instructor_id,
                gene1.instructor_id,
            )
            gene1.room_id, gene2.room_id = gene2.room_id, gene1.room_id
            gene1.quanta, gene2.quanta = gene2.quanta, gene1.quanta

    return ind1, ind2


def crossover_uniform(
    ind1: List[SessionGene], ind2: List[SessionGene], cx_prob: float = 0.5
):
    """
    ⚠️  DEPRECATED: Position-Dependent Uniform Crossover

    This operator swaps entire genes by array index. It is ONLY SAFE if ALL
    individuals in the population have genes in IDENTICAL POSITIONS representing
    the SAME (course, group) pairs.

    RISK: If gene positions differ between individuals (e.g., due to sorting,
    custom seeding, or repair operators), this will create DUPLICATE and MISSING
    (course, group) pairs, violating the incomplete_or_extra_sessions constraint.

    RECOMMENDATION: Use crossover_course_group_aware() instead for robustness
    and future-proofing.

    Args:
        ind1, ind2 (List[SessionGene]): Two individuals to perform crossover on.
        cx_prob (float): Probability of crossover for each gene position.

    Returns:
        tuple: (ind1, ind2) with swapped genes
    """
    for i in range(len(ind1)):
        if random.random() < cx_prob:
            # Swap ENTIRE genes between the two individuals
            # DANGER: If gene[i] in ind1 ≠ gene[i] in ind2, this creates corruption
            ind1[i], ind2[i] = ind2[i], ind1[i]

    return ind1, ind2  # Return after processing ALL genes
