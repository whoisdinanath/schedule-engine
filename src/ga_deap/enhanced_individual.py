"""
Enhanced Individual Generation with Parallel Session Scheduling

This module improves the individual generation to better utilize resources
and schedule multiple courses in parallel when possible.
"""

import random
from typing import Dict, List, Set, Tuple
from collections import defaultdict
from src.encoders import QuantumTimeSystem
from src.entities import Course, Instructor, Group, Room
from src.ga_deap.sessiongene import SessionGene


def generate_enhanced_individual(
    qts: QuantumTimeSystem,
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
    rooms: Dict[str, Room],
) -> List[SessionGene]:
    """
    Enhanced individual generation that schedules multiple courses in parallel
    when resources allow (different rooms, instructors, groups).

    This approach:
    1. Groups courses by their requirements
    2. Schedules non-conflicting courses in the same time slots
    3. Utilizes subgroups for parallel scheduling
    4. Maximizes resource utilization

    Args:
        qts: Time system with quantum logic
        courses: All course definitions
        instructors: Instructor pool
        groups: Student group pool (including subgroups)
        rooms: Room pool

    Returns:
        List[SessionGene]: Enhanced individual with parallel scheduling
    """
    individual = []

    # Track resource usage during scheduling
    resource_usage = {
        "quantum_instructor": set(),  # (quantum, instructor_id)
        "quantum_room": set(),  # (quantum, room_id)
        "quantum_group": set(),  # (quantum, group_id)
    }

    # Build course requirements and schedule systematically
    course_sessions = []

    for course in courses.values():
        if not course.qualified_instructor_ids or not course.enrolled_group_ids:
            continue

        # For each required session of this course
        for session_num in range(course.quanta_per_week):
            # Try to use subgroups if available
            available_groups = []

            for group_id in course.enrolled_group_ids:
                if group_id in groups:
                    group = groups[group_id]
                    available_groups.append(group_id)

                    # Check if this group has subgroups
                    if hasattr(group, "subgroups") and group.subgroups:
                        # Use subgroups for more granular scheduling
                        for subgroup_id in group.subgroups:
                            if subgroup_id in groups:
                                available_groups.append(subgroup_id)

            if not available_groups:
                continue

            # Choose the most suitable group (prefer subgroups for flexibility)
            group_id = random.choice(available_groups)
            group = groups[group_id]

            course_sessions.append(
                {
                    "course": course,
                    "group_id": group_id,
                    "group": group,
                    "session_num": session_num,
                }
            )

    # Sort sessions by complexity (courses with fewer options first)
    course_sessions.sort(key=lambda x: len(x["course"].qualified_instructor_ids))

    # Schedule sessions using parallel scheduling approach
    for session_info in course_sessions:
        course = session_info["course"]
        group_id = session_info["group_id"]
        group = session_info["group"]

        # Find available instructors for this course
        available_instructors = [
            instructor_id
            for instructor_id in course.qualified_instructor_ids
            if instructor_id in instructors
        ]

        if not available_instructors:
            continue

        # Find suitable rooms
        suitable_rooms = [
            room
            for room in rooms.values()
            if room.is_suitable_for_course_type(course.required_room_features)
        ]

        if not suitable_rooms:
            continue

        # Find the best time slot that allows parallel scheduling
        best_quantum = None
        best_instructor = None
        best_room = None

        # Get all possible time slots
        group_quanta = group.available_quanta
        all_operating_quanta = qts.get_all_operating_quanta()

        # Try to find a time slot that maximizes parallel scheduling
        for quantum in group_quanta:
            if quantum not in all_operating_quanta:
                continue

            # Check if this quantum allows for parallel scheduling
            for instructor_id in available_instructors:
                instructor = instructors[instructor_id]

                # Check instructor availability
                if (
                    not instructor.is_full_time
                    and quantum not in instructor.available_quanta
                ):
                    continue

                # Check if instructor is already booked at this time
                if (quantum, instructor_id) in resource_usage["quantum_instructor"]:
                    continue

                # Check if group is already booked at this time
                if (quantum, group_id) in resource_usage["quantum_group"]:
                    continue

                # Find an available room
                for room in suitable_rooms:
                    # Check room availability
                    if quantum not in room.available_quanta:
                        continue

                    # Check if room is already booked at this time
                    if (quantum, room.room_id) in resource_usage["quantum_room"]:
                        continue

                    # Check room capacity
                    if group.student_count > room.capacity:
                        continue

                    # Found a valid combination!
                    best_quantum = quantum
                    best_instructor = instructor_id
                    best_room = room
                    break

                if best_quantum is not None:
                    break

            if best_quantum is not None:
                break

        # Schedule the session if we found a valid slot
        if (
            best_quantum is not None
            and best_instructor is not None
            and best_room is not None
        ):
            session = SessionGene(
                course_id=course.course_id,
                instructor_id=best_instructor,
                group_id=group_id,
                room_id=best_room.room_id,
                quanta=[best_quantum],
            )
            individual.append(session)

            # Update resource usage
            resource_usage["quantum_instructor"].add((best_quantum, best_instructor))
            resource_usage["quantum_room"].add((best_quantum, best_room.room_id))
            resource_usage["quantum_group"].add((best_quantum, group_id))

    return individual


def generate_parallel_aware_individual(
    qts: QuantumTimeSystem,
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
    rooms: Dict[str, Room],
) -> List[SessionGene]:
    """
    Alternative implementation that focuses on maximizing parallel scheduling
    by scheduling all courses for each time slot before moving to the next.
    """
    individual = []

    # Get all available time slots
    all_quanta = qts.get_all_operating_quanta()

    # Build requirements for each course session
    required_sessions = []
    for course in courses.values():
        if not course.qualified_instructor_ids or not course.enrolled_group_ids:
            continue

        for _ in range(course.quanta_per_week):
            required_sessions.append(course)

    # For each time slot, try to schedule as many non-conflicting courses as possible
    for quantum in all_quanta:
        scheduled_in_slot = set()
        used_instructors = set()
        used_rooms = set()
        used_groups = set()

        # Shuffle sessions to avoid bias
        random.shuffle(required_sessions)

        for course in required_sessions[:]:  # Copy list to allow modification
            # Skip if already scheduled
            if id(course) in scheduled_in_slot:
                continue

            # Find available resources for this course at this time
            available_instructors = [
                iid
                for iid in course.qualified_instructor_ids
                if iid in instructors and iid not in used_instructors
            ]

            available_groups = [
                gid
                for gid in course.enrolled_group_ids
                if gid in groups and gid not in used_groups
            ]

            # Also check subgroups
            subgroup_candidates = []
            for gid in course.enrolled_group_ids:
                if gid in groups:
                    group = groups[gid]
                    if hasattr(group, "subgroups") and group.subgroups:
                        for subgroup_id in group.subgroups:
                            if subgroup_id in groups and subgroup_id not in used_groups:
                                subgroup_candidates.append(subgroup_id)

            available_groups.extend(subgroup_candidates)

            if not available_instructors or not available_groups:
                continue

            # Find suitable rooms
            suitable_rooms = [
                room
                for room in rooms.values()
                if (
                    room.is_suitable_for_course_type(course.required_room_features)
                    and room.room_id not in used_rooms
                    and quantum in room.available_quanta
                )
            ]

            if not suitable_rooms:
                continue

            # Try to schedule this course
            for instructor_id in available_instructors:
                instructor = instructors[instructor_id]

                # Check instructor availability
                if (
                    not instructor.is_full_time
                    and quantum not in instructor.available_quanta
                ):
                    continue

                for group_id in available_groups:
                    group = groups[group_id]

                    # Check group availability
                    if quantum not in group.available_quanta:
                        continue

                    for room in suitable_rooms:
                        # Check room capacity
                        if group.student_count > room.capacity:
                            continue

                        # Schedule the session
                        session = SessionGene(
                            course_id=course.course_id,
                            instructor_id=instructor_id,
                            group_id=group_id,
                            room_id=room.room_id,
                            quanta=[quantum],
                        )
                        individual.append(session)

                        # Mark resources as used
                        used_instructors.add(instructor_id)
                        used_rooms.add(room.room_id)
                        used_groups.add(group_id)
                        scheduled_in_slot.add(id(course))
                        required_sessions.remove(course)

                        # Break out of all loops for this course
                        break
                    else:
                        continue
                    break
                else:
                    continue
                break

    return individual


# Integration function to replace the original
def generate_individual(
    qts: QuantumTimeSystem,
    courses: Dict[str, Course],
    instructors: Dict[str, Instructor],
    groups: Dict[str, Group],
    rooms: Dict[str, Room],
) -> List[SessionGene]:
    """
    Main function that uses the enhanced parallel scheduling approach.
    """
    # Try the enhanced approach first
    individual = generate_enhanced_individual(qts, courses, instructors, groups, rooms)

    # If we don't have enough sessions, supplement with the original method
    total_required_sessions = sum(course.quanta_per_week for course in courses.values())

    if len(individual) < total_required_sessions * 0.8:  # If we scheduled less than 80%
        # Fall back to parallel-aware approach
        individual = generate_parallel_aware_individual(
            qts, courses, instructors, groups, rooms
        )

    return individual
