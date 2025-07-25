import random
from src.ga.sessiongene import SessionGene


def mutate_gene(gene: SessionGene, context) -> SessionGene:
    """
    Performs constraint-aware mutation on a single gene
    """
    # Get course info for constraint-aware mutation
    course = context["courses"].get(gene.course_id)

    # Find qualified instructors for this course
    qualified_instructors = [
        inst_id
        for inst_id, inst in context["instructors"].items()
        if gene.course_id in getattr(inst, "qualified_courses", [gene.course_id])
    ]
    new_instructor = random.choice(
        qualified_instructors
        if qualified_instructors
        else list(context["instructors"].keys())
    )

    # Find compatible groups for this course
    compatible_groups = [
        grp_id
        for grp_id, grp in context["groups"].items()
        if gene.course_id in getattr(grp, "enrolled_courses", [gene.course_id])
    ]
    new_group = random.choice(
        compatible_groups if compatible_groups else list(context["groups"].keys())
    )

    # Use course's required quanta count if available
    num_quanta = (
        getattr(course, "quanta_per_week", len(gene.quanta))
        if course
        else len(gene.quanta)
    )
    num_quanta = min(num_quanta, len(context["available_quanta"]))

    new_quanta = random.sample(list(context["available_quanta"]), num_quanta)

    return SessionGene(
        course_id=gene.course_id,  # Keep course the same
        instructor_id=new_instructor,
        group_id=new_group,
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
