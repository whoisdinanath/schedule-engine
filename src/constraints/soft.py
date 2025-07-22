"""
Soft constraint penalty functions for UCTP.
Each function returns an integer penalty representing violations of a quality rule.
These do not impact feasibility, but aim to improve real-world schedule quality.
"""

from typing import List
from collections import defaultdict
from src.entities.decoded_session import CourseSession

# ---------------------------
# Magic numbers (tunable)
# ---------------------------
MAX_SESSION_COALESCENCE = 3  # Max preferred quanta per session block
MIDDAY_BREAK_START_QUANTA = 48  # 12:00 (96 quanta per day)
MIDDAY_BREAK_END_QUANTA = 52  # 13:00
EARLIEST_ALLOWED_QUANTA = 32  # e.g., 08:00
LATEST_ALLOWED_QUANTA = 76  # e.g., 19:00
QUANTA_PER_DAY = 96
MAX_SESSIONS_PER_DAY = 5


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
    )  # group_id -> day_idx -> set of quanta

    for session in sessions:
        for group_id in session.group_ids:
            for q in session.session_quanta:
                day = q // QUANTA_PER_DAY
                group_day_quanta[group_id][day].add(q % QUANTA_PER_DAY)

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
            day = q // QUANTA_PER_DAY
            instructor_day_quanta[iid][day].add(q % QUANTA_PER_DAY)

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
#  Ineed to change logic to: (if break falls on given quanta: then: no penalty: else how many quanta differene on nearest allocated time :  that is penalty )


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
    break_quanta = set(range(MIDDAY_BREAK_START_QUANTA, MIDDAY_BREAK_END_QUANTA))

    group_day_quanta = defaultdict(lambda: defaultdict(set))

    for session in sessions:
        for gid in session.group_ids:
            for q in session.session_quanta:
                day = q // QUANTA_PER_DAY
                group_day_quanta[gid][day].add(q % QUANTA_PER_DAY)

    for days in group_day_quanta.values():
        for quanta in days.values():
            if break_quanta & quanta:
                continue  # No penalty if group is free during break
            # Compute min distance to break window
            nearest_dist = min(abs(q - bq) for q in quanta for bq in break_quanta)
            penalty += nearest_dist

    return penalty


# 4. Session Coalescence Penalty
def course_split_penalty(sessions: List[CourseSession]) -> int:
    """Calculate penalty for sessions that are split into small blocks.

    Penalizes course sessions that are broken into blocks smaller than the
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
            day = q // QUANTA_PER_DAY
            course_day_quanta[cid][day].append(q % QUANTA_PER_DAY)

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


# 5. Early/Late Session Penalty
def early_or_late_session_penalty(sessions: List[CourseSession]) -> int:
    """Calculate penalty for sessions scheduled outside preferred hours.

    Penalizes sessions that start too early or end too late in the day
    to maintain reasonable academic hours.

    Args:
        sessions: List of course sessions to evaluate.

    Returns:
        Total penalty points for sessions outside preferred time range.
    """
    penalty = 0
    for session in sessions:
        for q in session.session_quanta:
            within_day = q % QUANTA_PER_DAY
            if (
                within_day < EARLIEST_ALLOWED_QUANTA
                or within_day > LATEST_ALLOWED_QUANTA
            ):
                penalty += 1
                break  # Only penalize once per session
    return penalty
