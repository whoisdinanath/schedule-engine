from typing import List
import random

from src.ga.sessiongene import SessionGene
from src.ga.individual import create_individual

# from src


def generate_random_gene(
    possible_courses,
    possible_instructors,
    possible_groups,
    possible_rooms,
    available_quanta,
) -> SessionGene:
    course = random.choice(possible_courses)
    instructor = random.choice(possible_instructors)
    group = random.choice(possible_groups)
    room = random.choice(possible_rooms)

    num_quanta = random.randint(1, 4)

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
