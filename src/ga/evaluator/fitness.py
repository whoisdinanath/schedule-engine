from typing import List, Dict, Tuple
from src.decoder.individual_decoder import decode_individual
from src.ga.sessiongene import SessionGene
from src.entities.course import Course
from src.entities.instructor import Instructor
from src.entities.group import Group

# Hard Constraints (only those confirmed to exist)
from src.constraints.hard import (
    no_group_overlap,
    no_instructor_conflict,
    instructor_not_qualified,
    room_type_mismatch,
    availability_violations,
    incomplete_or_extra_sessions,
)

# Soft Constraints
from src.constraints.soft import (
    group_gaps_penalty,
    instructor_gaps_penalty,
    group_midday_break_violation,
    course_split_penalty,
    early_or_late_session_penalty,
)


def evaluate(
    individual: List[SessionGene],
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
) -> Tuple[int, int]:
    """
    Evaluates a timetable individual using both hard and soft constraints.

    Hard constraints affect feasibility and must ideally reach zero.
    Soft constraints reflect schedule quality and should be minimized.

    Returns:
        Tuple[int, int]: (hard_penalty_score, soft_penalty_score)
    """
    sessions = decode_individual(individual, courses, instructors, groups)

    # Hard constraint penalty
    hard_penalty = 0
    hard_penalty += no_group_overlap(sessions)
    hard_penalty += no_instructor_conflict(sessions)
    hard_penalty += instructor_not_qualified(sessions, courses)
    hard_penalty += room_type_mismatch(sessions)
    hard_penalty += availability_violations(sessions)
    hard_penalty += incomplete_or_extra_sessions(sessions, courses)

    # Soft constraint penalty
    soft_penalty = 0
    soft_penalty += group_gaps_penalty(sessions)
    soft_penalty += instructor_gaps_penalty(sessions)
    soft_penalty += group_midday_break_violation(sessions)
    soft_penalty += course_split_penalty(sessions)
    soft_penalty += early_or_late_session_penalty(sessions)

    return (hard_penalty, soft_penalty)
