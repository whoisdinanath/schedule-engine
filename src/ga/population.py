from typing import List
import random

from src.ga.sessiongene import SessionGene
from src.ga.individual import create_individual

# from src
# Or Separately I need to write population initialization logic. for population generation with min constraint vilation


def generate_random_gene(
    possible_courses,
    possible_instructors,
    possible_groups,
    possible_rooms,
    available_quanta,
) -> SessionGene:
    course = random.choice(possible_courses)

    # Try to find a qualified instructor (constraint-aware)
    qualified_instructors = [
        inst
        for inst in possible_instructors
        if course.course_id in getattr(inst, "qualified_courses", [course.course_id])
    ]
    instructor = random.choice(
        qualified_instructors if qualified_instructors else possible_instructors
    )

    # Try to find a compatible group (constraint-aware)
    compatible_groups = [
        grp
        for grp in possible_groups
        if course.course_id in getattr(grp, "enrolled_courses", [course.course_id])
    ]
    group = random.choice(compatible_groups if compatible_groups else possible_groups)

    room = random.choice(possible_rooms)

    # Use course's required quanta count if available
    num_quanta = getattr(course, "quanta_per_week", random.randint(1, 4))
    num_quanta = min(
        num_quanta, len(available_quanta)
    )  # Ensure we don't exceed available

    # You may want to base this on course.quanta_per_week
    quanta = random.sample(list(available_quanta), num_quanta)

    return SessionGene(
        course_id=course.course_id,
        instructor_id=instructor.instructor_id,
        group_id=group.group_id,
        room_id=room.room_id,
        quanta=quanta,
    )


def generate_population(n: int, session_count: int, context) -> List:
    """
    Gnerates a List of DEAP Individuduals (chromosomas) of size = n

    Args:
        n(int): Number of individuals to generate
        session_count(int): Number of sessions per individual ?
        context(dict): Include 'courses', instructors, groups, rooms, available_quanta

    Returns:
        List: Population of DEAP Individuals.
    """
    population = []  # Empty list to hold the population
    for _ in range(n):
        genes = [
            generate_random_gene(
                list(context["courses"].values()),
                list(context["instructors"].values()),
                list(context["groups"].values()),
                list(context["rooms"].values()),
                context["available_quanta"],
            )
            for _ in range(session_count)
        ]
        population.append(create_individual(genes))

    return population
