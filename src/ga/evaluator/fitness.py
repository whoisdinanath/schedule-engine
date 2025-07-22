from typing import List, Dict, Tuple
from src.decoder.individual_decoder import decode_individual
from src.ga.sessiongene import SessionGene
from src.entities.course import Course
from src.entities.instructor import Instructor
from src.entities.group import Group

from src.constraints.hard import no_group_overlap, no_instructor_conflict
from src.constraints.soft import group_gap_penalty


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

    hard = 0
    hard += no_group_overlap(sessions)
    hard += no_instructor_conflict(sessions)

    soft = 0
    soft += group_gap_penalty(sessions)
    # If you want single objective optimization: you can reutrn only hard, or hard+soft
    # If you want multi-objective optimization: return (hard, soft) for NSGA-II or simiolar appraoch algos.
    #  DEAP expects a tuple if only single value is to be reurned then
    # return (hard,) or (hard + soft,)

    return (hard, soft)  # Must be a tuple for DEAP compatibility
