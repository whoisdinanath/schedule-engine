from typing import Dict, List
from entities.course import Course
from src.entities.decoded_session import CourseSession
from collections import defaultdict


def no_group_overlap(sessions: List[CourseSession]) -> int:
    """
    Counts how many times a group is assigned to multiple sessions at the same time.

    Args:
        sessions (List[CourseSession]): List of all decoded sessions.

    Returns:
        int: Total number of group-time conflicts.
    """
    conflict_count = 0
    group_time_map = {}  # Maps (group_id, time_quanta) to count of sessions

    for session in sessions:
        for gid in session.group_ids:
            for q in session.session_quanta:
                key = (gid, q)
                if key in group_time_map:
                    conflict_count += 1
                else:
                    # The 'else' block is executed when the (group_id, time_quanta) key is not already in the group_time_map.
                    # It adds this key to the map and associates it with the session's course_id.
                    # This helps track which group is scheduled at which time, so future overlaps can be detected.
                    group_time_map[key] = session.course_id  #

    return conflict_count


def no_instructor_conflict(sessions: List[CourseSession]) -> int:
    """
    Counts how many times an instructor is assigned to multiple sessions at the same time.
    """
    conflicts = 0
    instructor_time_map = {}

    for session in sessions:
        iid = session.instructor_id
        for q in session.session_quanta:
            key = (iid, q)
            if key in instructor_time_map:
                conflicts += 1
            else:
                instructor_time_map[key] = session.course_id

    return conflicts


def instructor_not_qualified(
    sessions: List[CourseSession], course_map: Dict[str, Course]
) -> int:
    """
    Checks how many sessions are assigned to unqualified instructors.
    """
    violations = 0

    for session in sessions:
        qualified = course_map[session.course_id].qualified_instructor_ids
        if session.instructor_id not in qualified:
            violations += 1

    return violations


def room_type_mismatch(sessions: List[CourseSession]) -> int:
    """
    Counts how many sessions are scheduled in rooms that don't match required features.
    """
    violations = 0

    for session in sessions:
        if session.room.room_features != session.required_room_features:
            violations += 1

    return violations


def availability_violations(sessions: List[CourseSession]) -> int:
    """
    Counts how many sessions are scheduled during unavailable time slots for
    the group, instructor, or room.
    """
    violations = 0

    for session in sessions:
        for q in session.session_quanta:
            if (
                q not in session.instructor.available_quanta
                or q not in session.group.available_quanta
                or q not in session.room.available_quanta
            ):
                violations += 1
                break  # Only count one violation per session

    return violations


def incomplete_or_extra_sessions(
    sessions: List[CourseSession], course_map: Dict[str, Course]
) -> int:
    """
    Verifies that each course is scheduled for exactly the required number of quanta.

    Returns the number of courses that are under- or over-scheduled.
    """
    quanta_counter = defaultdict(int)

    for session in sessions:
        quanta_counter[session.course_id] += len(session.session_quanta)

    violations = 0
    for cid, course in course_map.items():
        if quanta_counter[cid] != course.quanta_per_week:
            violations += 1

    return violations
