import random
from src.ga.sessiongene import SessionGene


def mutate_gene(gene: SessionGene, context) -> SessionGene:
    """
    Performs the Mutation on a single gene (e.g. change time or instructor)

    """
    new_quanta = random.sample(list(context["available_quanta"]), len(gene.quanta))

    return SessionGene(
        course_id=gene.course_id,
        instructor_id=random.choice(list(context["instructors"].keys())),
        group_id=gene.group_id,
        room_id=random.choice(list(context["rooms"].keys())),
        quanta=new_quanta,
    )


def mutate_individual(individual, context, mut_prob=0.2):
    """
    applies mutaiton to an individual by randomly modifying some genes.

    Args:
        individual: List of SessiongEne
        context: Dict with instructor, rooms, available_quanta,
        mut_prob (float): Probability of mutation for each gene.
    """
    for i in range(len(individual)):
        if random.random() < mut_prob:
            individual[i] = mutate_gene(individual[i], context)
    return (individual,)  # Return as a tuple for DEAP compatibility
