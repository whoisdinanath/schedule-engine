"""Here I implemented the functions to generate an individual for the genetic algorithm.
- Previous Implementation was random initial population generation.
- It was fucked up, (since the first generation was fucked, then how could it generate a good population)
- Although the random generation could contribute for diversity, it didn't even converge after 50-60 ngens
- So I will implement a more structured way to generate the initial population.

    New Implementation:
- I will generate the initial population based on the courses, instructors, rooms, and groups.
"""

import random
from typing import Dict, List, Tuple
from src.encoders import QuantumTimeSystem
from src.entities import Course, Instructor, Group, Room
from src.ga_deap.sessiongene import SessionGene


def generate_individual(
    qts: QuantumTimeSystem,
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
    rooms: Dict[str, Room],
) -> List[SessionGene]:
    """
    Generate a list of SessionGene objects (1 gene per quantum session),
    based entirely on raw quantum units — no fixed duration enforced.

    Each course contributes `quanta_per_week` individual quanta
    (i.e., separate SessionGene instances).

    Args:
        qts (QuantumTimeSystem): Time system with quantum logic.
        courses: All course definitions.
        instructors: Instructor pool.
        groups: Student group pool.
        rooms: Room pool.

    Returns:
        List[SessionGene]: Individual chromosome consisting of multiple session genes.
    """
    individual = []

    for course in courses.values():
        if not course.qualified_instructor_ids or not course.enrolled_group_ids:
            continue

        group_id = random.choice(course.enrolled_group_ids)
        group = groups[group_id]

        for _ in range(course.quanta_per_week):
            instructor_id = random.choice(course.qualified_instructor_ids)
            instructor = instructors[instructor_id]

            # Filter suitable rooms
            suitable_rooms = [
                r
                for r in rooms.values()
                if r.is_suitable_for_course_type(course.required_room_features)
            ]
            if not suitable_rooms:
                continue
            room = random.choice(suitable_rooms)

            # Get available quanta intersection
            group_quanta = group.available_quanta
            instructor_quanta = (
                instructor.available_quanta
                if not instructor.is_full_time
                else qts.get_all_operating_quanta()
            )
            room_quanta = room.available_quanta

            available_quanta = list(group_quanta & instructor_quanta & room_quanta)
            if not available_quanta:
                continue

            q = random.choice(available_quanta)

            session = SessionGene(
                course_id=course.course_id,
                instructor_id=instructor_id,
                group_id=group_id,
                room_id=room.room_id,
                quanta=[q],  # just 1 quantum — no fixed length
            )
            individual.append(session)

    return individual
