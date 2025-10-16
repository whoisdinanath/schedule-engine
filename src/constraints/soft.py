"""
Soft constraint penalty functions for UCTP.
Each function returns an integer penalty representing violations of a quality rule.
These do not impact feasibility, but aim to improve real-world schedule quality.

IMPORTANT: Uses CONTINUOUS quantum system. All time conversions must go through
QuantumTimeSystem. Never use QUANTA_PER_DAY or day = q // QUANTA_PER_DAY.
"""

from typing import List
from collections import defaultdict
from src.entities.decoded_session import CourseSession
from src.encoder.quantum_time_system import QuantumTimeSystem
from config.time_config import (
    MAX_SESSION_COALESCENCE,
    MAX_SESSIONS_PER_DAY,
    get_midday_break_quanta,
    get_preferred_time_range_quanta,
    quantum_to_day_and_within_day,
)

# Global QuantumTimeSystem instance (initialized once)
_QTS = QuantumTimeSystem()


# 1. Group Compactness: penalize gaps in daily group schedule
def group_gaps_penalty(sessions: List[CourseSession]) -> int:
    """Calculate penalty for gaps in daily group schedules.

    Penalizes idle time slots between the first and last session of each group
    on each day to encourage compact schedules.

    Args:
        sessions: List of course sessions to evaluate.

    Returns:
        Total penalty points for group schedule gaps.
    """
    penalty = 0
    group_day_quanta = defaultdict(
        lambda: defaultdict(set)
    )  # group_id -> day_name -> set of within-day quanta

    for session in sessions:
        for group_id in session.group_ids:
            for q in session.session_quanta:
                day, within_day = quantum_to_day_and_within_day(q, _QTS)
                group_day_quanta[group_id][day].add(within_day)

    for days in group_day_quanta.values():
        for quanta in days.values():
            if not quanta:
                continue
            min_q, max_q = min(quanta), max(quanta)
            span = max_q - min_q + 1
            idle_slots = span - len(quanta)
            penalty += idle_slots

    return penalty


# 2. Instructor Compactness
def instructor_gaps_penalty(sessions: List[CourseSession]) -> int:
    """Calculate penalty for gaps in daily instructor schedules.

    Penalizes idle time slots between the first and last session of each
    instructor on each day to encourage compact teaching schedules.

    Args:
        sessions: List of course sessions to evaluate.

    Returns:
        Total penalty points for instructor schedule gaps.
    """
    penalty = 0
    instructor_day_quanta = defaultdict(lambda: defaultdict(set))

    for session in sessions:
        iid = session.instructor_id
        for q in session.session_quanta:
            day, within_day = quantum_to_day_and_within_day(q, _QTS)
            instructor_day_quanta[iid][day].add(within_day)

    for days in instructor_day_quanta.values():
        for quanta in days.values():
            if not quanta:
                continue
            min_q, max_q = min(quanta), max(quanta)
            span = max_q - min_q + 1
            idle_slots = span - len(quanta)
            penalty += idle_slots

    return penalty


# 3. Group Midday Break Violation
def group_midday_break_violation(sessions: List[CourseSession]) -> int:
    """
    Penalizes groups that do not have a break during the midday break period.

    For each group per day, if no session falls in the break window,
    penalize by the minimum distance from any scheduled quantum to the break block.

    Args:
        sessions (List[CourseSession]): List of CourseSession objects.

    Returns:
        int: Total break violation penalty across all groups and days.
    """
    penalty = 0
    # Get break quanta for each day (day_name -> set of within-day quanta)
    break_quanta_by_day = get_midday_break_quanta(_QTS)

    group_day_quanta = defaultdict(lambda: defaultdict(set))

    for session in sessions:
        for gid in session.group_ids:
            for q in session.session_quanta:
                day, within_day = quantum_to_day_and_within_day(q, _QTS)
                group_day_quanta[gid][day].add(within_day)

    for days in group_day_quanta.values():
        for day_name, quanta in days.items():
            # Get break quanta for this specific day
            if day_name not in break_quanta_by_day:
                continue  # No break defined for this day

            break_quanta = break_quanta_by_day[day_name]

            if break_quanta & quanta:
                continue  # No penalty if group is free during break
            # Compute min distance to break window
            nearest_dist = min(abs(q - bq) for q in quanta for bq in break_quanta)
            penalty += nearest_dist

    return penalty


# 4. Session Coalescence Penalty
def course_split_penalty(sessions: List[CourseSession]) -> int:
    """Calculate penalty for sessions that are split into small blocks.

    Penalizes course sessions that are broken into blocks smaller or larger than the
    preferred coalescence size to encourage longer continuous sessions.

    Args:
        sessions: List of course sessions to evaluate.

    Returns:
        Total penalty points for undersized session blocks.
    """
    penalty = 0
    course_day_quanta = defaultdict(lambda: defaultdict(list))

    for session in sessions:
        cid = session.course_id
        for q in session.session_quanta:
            day, within_day = quantum_to_day_and_within_day(q, _QTS)
            course_day_quanta[cid][day].append(within_day)

    for days in course_day_quanta.values():
        for quanta in days.values():
            quanta.sort()
            block_size = 1
            for i in range(1, len(quanta)):
                if quanta[i] == quanta[i - 1] + 1:
                    block_size += 1
                else:
                    if block_size < MAX_SESSION_COALESCENCE:
                        penalty += 1
                    block_size = 1
            if block_size < MAX_SESSION_COALESCENCE:
                penalty += 1

    return penalty


# # 5. Early/Late Session Penalty
# def early_or_late_session_penalty(sessions: List[CourseSession]) -> int:
#     """Calculate penalty for sessions scheduled outside preferred hours.

#     Penalizes sessions that start too early or end too late in the day
#     to maintain reasonable academic hours.

#     Args:
#         sessions: List of course sessions to evaluate.

#     Returns:
#         Total penalty points for sessions outside preferred time range.
#     """
#     penalty = 0
#     # Get preferred time ranges for each day (day_name -> (earliest, latest) within-day quanta)
#     earliest_quanta, latest_quanta = get_preferred_time_range_quanta(_QTS)

#     for session in sessions:
#         session_violates = False
#         for q in session.session_quanta:
#             day, within_day = quantum_to_day_and_within_day(q, _QTS)

#             # Check if this day has preferred hours defined
#             if day not in earliest_quanta or day not in latest_quanta:
#                 continue

#             if within_day < earliest_quanta[day] or within_day > latest_quanta[day]:
#                 session_violates = True
#                 break  # Only penalize once per session

#         if session_violates:
#             penalty += 1

#     return penalty


# ---------------------------
# Soft Constraint Registry
# ---------------------------
def get_all_soft_constraints():
    """
    Returns a dictionary of all available soft constraint functions.

    Returns:
        Dict[str, callable]: Mapping of constraint names to their functions.
    """
    return {
        "group_gaps_penalty": group_gaps_penalty,
        "instructor_gaps_penalty": instructor_gaps_penalty,
        "group_midday_break_violation": group_midday_break_violation,
        "course_split_penalty": course_split_penalty,
        # "early_or_late_session_penalty": early_or_late_session_penalty,
    }
    


def get_enabled_soft_constraints():
    """
    Returns only the enabled soft constraints based on config.

    Returns:
        Dict[str, dict]: Mapping of enabled constraint names to their config (function, weight).
    """
    from config.constraints import SOFT_CONSTRAINTS_CONFIG

    all_constraints = get_all_soft_constraints()
    enabled = {}

    for name, config in SOFT_CONSTRAINTS_CONFIG.items():
        if config["enabled"] and name in all_constraints:
            enabled[name] = {
                "function": all_constraints[name],
                "weight": config["weight"],
            }

    return enabled
