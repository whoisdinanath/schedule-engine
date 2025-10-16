from typing import Dict, List
from src.entities.course import Course
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
    sessions: List[CourseSession], course_map: Dict[tuple, Course]
) -> int:
    """
    Checks how many sessions are assigned to unqualified instructors.
    """
    violations = 0

    for session in sessions:
        # Construct tuple key from course_id and course_type
        course_key = (session.course_id, session.course_type)
        if course_key not in course_map:
            continue  # Skip if course not found

        qualified = course_map[course_key].qualified_instructor_ids
        if session.instructor_id not in qualified:
            violations += 1

    return violations


def room_type_mismatch(sessions: List[CourseSession]) -> int:
    """
    Counts how many sessions are scheduled in rooms that don't match required features.
    Checks if required features are a subset of available room features.
    """
    violations = 0

    for session in sessions:
        # Convert both to sets for subset comparison
        required_features = (
            set(session.required_room_features)
            if isinstance(session.required_room_features, list)
            else {session.required_room_features}
        )
        room_features = (
            set(session.room.room_features)
            if isinstance(session.room.room_features, list)
            else {session.room.room_features}
        )

        # Check if all required features are present in room features
        if not required_features.issubset(room_features):
            violations += 1

    return violations


def availability_violations(sessions: List[CourseSession]) -> int:
    """
    Counts how many sessions are scheduled during unavailable time slots for
    the group, instructor, or room.

    For multi-group sessions, checks availability for all assigned groups.
    """
    violations = 0

    for session in sessions:
        for q in session.session_quanta:
            # Check if quantum is unavailable for instructor or room
            if (
                q not in session.instructor.available_quanta
                or q not in session.room.available_quanta
            ):
                violations += 1
                break  # Only count one violation per session

        # For multi-group sessions, check all groups' availability
        # If primary group exists, use it; otherwise skip group availability check
        if session.group:
            for q in session.session_quanta:
                if q not in session.group.available_quanta:
                    violations += 1
                    break  # Only count one violation per session

    return violations


def incomplete_or_extra_sessions(
    sessions: List[CourseSession], course_map: Dict[tuple, Course]
) -> int:
    """
    Verifies that each course is scheduled for exactly the required number of quanta
    PER GROUP that is enrolled in that course.

    New Architecture:
    - Courses are taught per group (not globally)
    - Theory sessions may use parent groups (whole class)
    - Practical sessions may use subgroups
    - Must check: each (course, group) combination has correct quanta

    IMPORTANT: course_map keys are tuples (course_code, course_type), but
    session.course_id is just the course_code string. Must extract course_code
    from tuple keys for proper comparison.

    Returns:
        Number of (course, group) combinations that are under- or over-scheduled.

    Example:
        If BAE2 is enrolled in ENME 151 (5 quanta/week),
        we should have exactly 5 quanta for (ENME 151, BAE2) combination.
    """
    # Count quanta per (course_code, course_type, group_id) combination
    # Use (course_code, course_type) to distinguish theory from practical
    course_group_quanta = defaultdict(int)

    for session in sessions:
        course_code = session.course_id  # This is just the course code string
        course_type = session.course_type  # This is "theory" or "practical"

        # Each session can have multiple groups (multi-group sessions)
        # Count quanta for each group separately
        for group_id in session.group_ids:
            # Key must match course_map key structure: (course_code, course_type)
            key = ((course_code, course_type), group_id)
            course_group_quanta[key] += len(session.session_quanta)

    violations = 0

    # Check each course's enrolled groups
    # course_key is (course_code, course_type) tuple
    for course_key, course in course_map.items():
        expected_quanta = course.quanta_per_week
        enrolled_groups = course.enrolled_group_ids

        # For each group enrolled in this course
        for group_id in enrolled_groups:
            # Use same key structure as counting above
            key = (course_key, group_id)
            actual_quanta = course_group_quanta.get(key, 0)

            # Check if scheduled correctly for this (course, group) pair
            if actual_quanta != expected_quanta:
                violations += 1

    return violations


# ---------------------------
# Hard Constraint Registry
# ---------------------------
def get_all_hard_constraints():
    """
    Returns a dictionary of all available hard constraint functions.

    Returns:
        Dict[str, callable]: Mapping of constraint names to their functions.
    """
    return {
        "no_group_overlap": no_group_overlap,
        "no_instructor_conflict": no_instructor_conflict,
        "instructor_not_qualified": instructor_not_qualified,
        "room_type_mismatch": room_type_mismatch,
        "availability_violations": availability_violations,
        "incomplete_or_extra_sessions": incomplete_or_extra_sessions,
    }


def get_enabled_hard_constraints():
    """
    Returns only the enabled hard constraints based on config.

    Returns:
        Dict[str, dict]: Mapping of enabled constraint names to their config (function, weight).
    """
    from config.constraints import HARD_CONSTRAINTS_CONFIG

    all_constraints = get_all_hard_constraints()
    enabled = {}

    for name, config in HARD_CONSTRAINTS_CONFIG.items():
        if config["enabled"] and name in all_constraints:
            enabled[name] = {
                "function": all_constraints[name],
                "weight": config["weight"],
            }

    return enabled
