from typing import List
from src.entities.decoded_session import CourseSession


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
