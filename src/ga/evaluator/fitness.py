from typing import List, Dict, Tuple
from src.decoder.individual_decoder import decode_individual
from src.constraints.hard import no_group_overlap, no_instructor_conflict
from src.ga.sessiongene import SessionGene
from src.entities.course import Course
from src.entities.instructor import Instructor
from src.entities.group import Group


def evaluate(
    individual: List[SessionGene],
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
) -> Tuple[float]:
    """
    Evaluates the fitness of an individual based on hard constraint violations.

    Returns:
        Tuple[float]: A single-element tuple representing the penalty score
                      (lower is better).
    """
    sessions = decode_individual(individual, courses, instructors, groups)

    penalty = 0
    penalty += no_group_overlap(sessions)
    penalty += no_instructor_conflict(sessions)

    return (penalty,)  # Must be a tuple for DEAP compatibility
