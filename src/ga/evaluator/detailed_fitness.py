from typing import List, Dict, Tuple
from src.decoder.individual_decoder import decode_individual
from src.ga.sessiongene import SessionGene
from src.entities.course import Course
from src.entities.instructor import Instructor
from src.entities.group import Group
from src.entities.room import Room

# Hard Constraints
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


def evaluate_detailed(
    individual: List[SessionGene],
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
    rooms: Dict[str, Room] = None,
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    Evaluates a timetable individual with detailed constraint breakdown.

    Returns:
        Tuple[Dict[str, int], Dict[str, int]]: (hard_constraint_details, soft_constraint_details)
    """
    # Get rooms from context if not provided
    if rooms is None:
        rooms = {}

    sessions = decode_individual(individual, courses, instructors, groups, rooms)

    # Hard constraint penalties (individual breakdown)
    hard_details = {
        "no_group_overlap": no_group_overlap(sessions),
        "no_instructor_conflict": no_instructor_conflict(sessions),
        "instructor_not_qualified": instructor_not_qualified(sessions, courses),
        "room_type_mismatch": room_type_mismatch(sessions),
        "availability_violations": availability_violations(sessions),
        "incomplete_or_extra_sessions": incomplete_or_extra_sessions(sessions, courses),
    }

    # Soft constraint penalties (individual breakdown)
    soft_details = {
        "group_gaps_penalty": group_gaps_penalty(sessions),
        "instructor_gaps_penalty": instructor_gaps_penalty(sessions),
        "group_midday_break_violation": group_midday_break_violation(sessions),
        "course_split_penalty": course_split_penalty(sessions),
        "early_or_late_session_penalty": early_or_late_session_penalty(sessions),
    }

    return hard_details, soft_details


def evaluate_from_detailed(
    hard_details: Dict[str, int], soft_details: Dict[str, int]
) -> Tuple[int, int]:
    """
    Convert detailed constraint breakdown to total penalties.

    Returns:
        Tuple[int, int]: (total_hard_penalty, total_soft_penalty)
    """
    total_hard = sum(hard_details.values())
    total_soft = sum(soft_details.values())
    return total_hard, total_soft
