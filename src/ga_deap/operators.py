import random
from typing import List, Tuple
from deap import tools

from .sessiongene import SessionGene
from src.encoders import QuantumTimeSystem


def custom_crossover(ind1, ind2):
    """
    Simple one point crossover for the course timetable genome
    """
    return tools.cxOnePoint(ind1, ind2)


# def custom_mutation(individual, qts_max_quanta: int):
#     """Mutate an individual's time assignments randomly.
#     This mutation randomly changes the time of one session in the individual's schedule.

#     Args:
#         individual (SessionGene): The individual to mutate.
#         qts_max_quanta (int): The maximum number of quanta.
#     """
#     for i in range(len(individual)):
#         if random.random() < 0.1:
#             time, room, inst = individual[i]
#             new_time = random.randint(0, qts_max_quanta - 1)
#             individual[i] = (new_time, room, inst)
#     return (individual,)


def custom_mutation(
    individual: List[SessionGene],
    qts: QuantumTimeSystem,
    courses: dict,
    instructors: dict,
    groups: dict,
    rooms: dict,
    mutation_rate: float = 0.1,
):
    """
    Mutates an individual by randomly modifying quanta, instructor, or room of each session gene.

    Args:
        individual (List[SessionGene]): The schedule (chromosome) to mutate.
        qts (QuantumTimeSystem): The quantum time system.
        courses (dict): All courses.
        instructors (dict): All instructors.
        groups (dict): All student groups.
        rooms (dict): All rooms.
        mutation_rate (float): Probability of mutation per gene.

    Returns:
        Tuple: The mutated individual wrapped in a tuple (as required by DEAP).
    """
    for session in individual:
        if random.random() > mutation_rate:
            continue  # No mutation

        course = courses[session.course_id]
        group = groups[session.group_id]
        instructor = instructors[session.instructor_id]
        room = rooms[session.room_id]

        # --- Mutate Instructor ---
        new_instructor_id = session.instructor_id
        if course.qualified_instructor_ids:
            new_instructor_id = random.choice(course.qualified_instructor_ids)

        new_instructor = instructors[new_instructor_id]
        instructor_quanta = (
            new_instructor.available_quanta
            if not new_instructor.is_full_time
            else qts.get_all_operating_quanta()
        )

        # --- Mutate Room ---
        suitable_rooms = [
            r
            for r in rooms.values()
            if r.is_suitable_for_course_type(course.required_room_features)
        ]
        new_room = random.choice(suitable_rooms)
        new_room_quanta = new_room.available_quanta

        # --- Mutate Quanta ---
        valid_quanta = group.available_quanta & instructor_quanta & new_room_quanta
        if not valid_quanta:
            continue  # No available quanta — skip this mutation

        new_q = random.choice(list(valid_quanta))
        session.instructor_id = new_instructor_id
        session.room_id = new_room.room_id
        session.quanta = [new_q]

    return (individual,)
