"""
Simple constraint checker for evolution tracking
"""

from typing import Dict, List, Any
from src.ga_deap.sessiongene import SessionGene
from src.entities import Course, Instructor, Group, Room


def check_all_constraints(
    individual: List[SessionGene],
    qts,
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
    rooms: Dict[str, Room],
) -> Dict[str, int]:
    """
    Simple constraint checking function for evolution tracking.
    Returns a dictionary of constraint violations.
    """
    violations = {
        "hard_violations": 0,
        "soft_violations": 0,
        "instructor_conflicts": 0,
        "room_conflicts": 0,
        "group_conflicts": 0,
        "capacity_violations": 0,
    }

    # Track resource usage
    used_slots = set()

    for session in individual:
        if session.course_id not in courses:
            continue

        course = courses[session.course_id]

        if session.instructor_id not in instructors:
            continue

        instructor = instructors[session.instructor_id]

        if session.group_id not in groups:
            continue

        group = groups[session.group_id]

        if session.room_id not in rooms:
            continue

        room = rooms[session.room_id]

        for quantum in session.quanta:
            # Check for conflicts
            instructor_slot = (quantum, session.instructor_id)
            room_slot = (quantum, session.room_id)
            group_slot = (quantum, session.group_id)

            if instructor_slot in used_slots:
                violations["instructor_conflicts"] += 1
                violations["hard_violations"] += 1
            else:
                used_slots.add(instructor_slot)

            if room_slot in used_slots:
                violations["room_conflicts"] += 1
                violations["hard_violations"] += 1
            else:
                used_slots.add(room_slot)

            if group_slot in used_slots:
                violations["group_conflicts"] += 1
                violations["hard_violations"] += 1
            else:
                used_slots.add(group_slot)

        # Check room capacity
        if group.size > room.capacity:
            violations["capacity_violations"] += 1
            violations["hard_violations"] += 1

        # Check instructor qualification (soft constraint)
        if session.course_id not in instructor.qualified_courses:
            violations["soft_violations"] += 1

    return violations
