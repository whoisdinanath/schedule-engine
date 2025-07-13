import random
from typing import Dict, List, Tuple
from src.encoders import QuantumTimeSystem
from src.entities import Course


def generate_individual(
    qts: QuantumTimeSystem,
    courses: Dict[str, Course],
    instructors: Dict,
    groups: Dict,
    rooms: Dict,
) -> List[Tuple[str, str, str]]:
    """Randomly generates an one individual for the genetic algorithm.

    Args:
        qts (QuantumTimeSystem): _description_
        courses (Dict[str,Course]): _description_
        instructors (Dict): _description_
        groups (Dict): _description_
        rooms (Dict): _description_

    Returns:
        List[Tuple[time_quanta, room_id, instructor_id]]
        where each element represents assignment for a course session.
    """
    individual = [] # Initialize an empty individual as a list
    for course in courses.values():
        for _ in range(course.quanta_per_week):
            time=random.randint(0, qts.TOTAL_WEEKLY_QUANTA-1)
            room = random.choice(list(rooms.keys()))
            instructor = random.choice(course.qualified_instructor_ids)
            individual.append((time, room, instructor))
    return individual
    