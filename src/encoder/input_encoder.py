"""
Input Data JSON Encoder Module

This module provides functions to load and encode input data from JSON files
into structured entities such as Course, Group, Instructor, and Room.

Functions:
- encode_availability
- load_instructors
- load_courses
- load_groups
- load_rooms
- link_courses_and_groups
- link_courses_and_instructors
"""

import json
from typing import Dict, List

from src.entities.course import Course
from src.entities.group import Group
from src.entities.instructor import Instructor
from src.entities.room import Room
from src.encoder.quantum_time_system import QuantumTimeSystem


def encode_availability(availability_dict: Dict, qts: QuantumTimeSystem) -> set:
    """
    Converts human-readable availability into a set of quantum indices.
    Automatically clips availability periods to operating hours.

    Args:
        availability_dict (Dict): Availability per weekday in format {"Monday": [{"start": "08:00", "end": "10:00"}, ...]}.
        qts (QuantumTimeSystem): An instance for time conversion.

    Returns:
        set: Set of integer quantum indices available.
    """
    quanta = set()
    for day, periods in availability_dict.items():
        day_cap = day.capitalize()

        # Skip if day is not operational
        if not qts.is_operational(day_cap):
            continue

        # Get operating hours for this day
        operating_hours = qts.operating_hours[day_cap]
        op_start_str, op_end_str = operating_hours
        op_start_minutes = int(op_start_str.split(":")[0]) * 60 + int(
            op_start_str.split(":")[1]
        )
        op_end_minutes = int(op_end_str.split(":")[0]) * 60 + int(
            op_end_str.split(":")[1]
        )

        for period in periods:
            # Parse availability period
            avail_start = period["start"]
            avail_end = period["end"]
            avail_start_minutes = int(avail_start.split(":")[0]) * 60 + int(
                avail_start.split(":")[1]
            )
            avail_end_minutes = int(avail_end.split(":")[0]) * 60 + int(
                avail_end.split(":")[1]
            )

            # Clip to operating hours
            clipped_start_minutes = max(avail_start_minutes, op_start_minutes)
            clipped_end_minutes = min(avail_end_minutes, op_end_minutes)

            # Skip if no overlap with operating hours
            if clipped_start_minutes >= clipped_end_minutes:
                continue

            # Convert back to HH:MM format
            clipped_start = (
                f"{clipped_start_minutes // 60:02d}:{clipped_start_minutes % 60:02d}"
            )
            clipped_end = (
                f"{clipped_end_minutes // 60:02d}:{clipped_end_minutes % 60:02d}"
            )

            # Encode the clipped period
            start_q = qts.time_to_quanta(day_cap, clipped_start)
            end_q = qts.time_to_quanta(day_cap, clipped_end)
            quanta.update(range(start_q, end_q))

    return quanta


def load_instructors(path: str, qts: QuantumTimeSystem) -> Dict[str, Instructor]:
    """
    Loads instructor data from JSON file and encodes their availability.

    Args:
        path (str): Path to JSON file.
        qts (QuantumTimeSystem): Time conversion system.

    Returns:
        Dict[str, Instructor]: Dictionary mapping instructor IDs to Instructor instances.
    """
    data = json.load(open(path))
    instructors = {}
    for item in data:
        availability = item.get("availability", {})
        is_full_time = not bool(availability)
        available_quanta = (
            encode_availability(availability, qts) if availability else set()
        )

        instructors[item["id"]] = Instructor(
            instructor_id=item["id"],
            name=item["name"],
            qualified_courses=item.get("courses", []),
            is_full_time=is_full_time,
            available_quanta=available_quanta,
        )
    return instructors


def load_courses(path: str) -> Dict[str, Course]:
    """
    Loads courses from FullSyllabusAll format and splits them into separate theory/practical subjects.

    Args:
        path (str): Path to the course JSON file.

    Returns:
        Dict[str, Course]: Dictionary of Course objects, with practical courses suffixed by "-PR".
    """
    data = json.load(open(path))
    courses = {}

    for item in data:
        course_code = item["CourseCode"].strip()
        name = item["CourseTitle"].strip()
        dept_list = [d.strip() for d in item.get("Dept", "GENERAL").split(",")]
        department = dept_list[0]
        semester = item.get("Semester", 1)
        credits = item.get("Credits", 3)

        L = item.get("L", 0)
        T = item.get("T", 0)
        P = item.get("P", 0)

        practical_features = item.get("PracticalRoomFeatures", "").strip()
        practical_features = [
            f.strip().lower() for f in practical_features.split(",") if f.strip()
        ]

        # Create theory course object if L + T > 0
        if L + T > 0:
            theory_id = course_code
            course = Course(
                course_id=theory_id,
                name=f"{name} (Theory)",
                quanta_per_week=L + T,
                required_room_features=["lecture room"],
                enrolled_group_ids=[],
                qualified_instructor_ids=[],
            )
            course.course_code = course_code
            course.department = department
            course.semester = semester
            course.credits = credits
            course.lecture_hours = L + T
            course.practical_hours = 0
            courses[theory_id] = course

        # Create practical course object if P > 0
        if P > 0:
            practical_id = course_code + "-PR"
            course = Course(
                course_id=practical_id,
                name=f"{name} (Practical)",
                quanta_per_week=P,
                required_room_features=practical_features or ["lab"],
                enrolled_group_ids=[],
                qualified_instructor_ids=[],
            )
            course.course_code = practical_id
            course.department = department
            course.semester = semester
            course.credits = credits
            course.lecture_hours = 0
            course.practical_hours = P
            courses[practical_id] = course

    return courses


def load_groups(path: str, qts: QuantumTimeSystem) -> Dict[str, Group]:
    """
    Loads student group data and encodes availability.

    NEW ARCHITECTURE: No parent groups!
    - Only creates subgroup entities if subgroups exist
    - If no subgroups, creates the group itself
    - All groups are independent, no parent-child relationship

    Args:
        path (str): Path to group JSON file.
        qts (QuantumTimeSystem): Time system to encode availability.

    Returns:
        Dict[str, Group]: Dictionary of group IDs to Group instances.
    """
    data = json.load(open(path))
    groups = {}

    for item in data:
        group_availability = item.get("availability", {})
        available_quanta = (
            encode_availability(group_availability, qts)
            if group_availability
            else qts.get_all_operating_quanta()
        )

        # Check if subgroups exist
        subgroups_data = item.get("subgroups", [])

        if subgroups_data:
            # If subgroups exist, ONLY create subgroups (no parent)
            for subgroup in subgroups_data:
                # Handle both old format (string) and new format (dict with id and student_count)
                if isinstance(subgroup, dict):
                    subgroup_id = subgroup["id"]
                    subgroup_count = subgroup.get(
                        "student_count", item["student_count"] // len(subgroups_data)
                    )
                else:
                    # Old format: subgroup is just a string ID
                    subgroup_id = subgroup
                    subgroup_count = item["student_count"] // len(subgroups_data)

                # Create subgroup with inherited courses and availability
                groups[subgroup_id] = Group(
                    group_id=subgroup_id,
                    name=f"{item['name']} - {subgroup_id}",
                    student_count=subgroup_count,
                    enrolled_courses=item.get("courses", []),
                    available_quanta=available_quanta,
                )
        else:
            # No subgroups, create the group itself
            group_id = item["group_id"]
            groups[group_id] = Group(
                group_id=group_id,
                name=item["name"],
                student_count=item["student_count"],
                enrolled_courses=item.get("courses", []),
                available_quanta=available_quanta,
            )

    return groups


def load_rooms(path: str, qts: QuantumTimeSystem) -> Dict[str, Room]:
    """
    Loads room data from JSON and encodes availability.

    Args:
        path (str): Path to room JSON file.
        qts (QuantumTimeSystem): Time conversion system.

    Returns:
        Dict[str, Room]: Dictionary of room IDs to Room objects.
    """
    data = json.load(open(path))
    rooms = {}
    for item in data:
        room_id = item["room_id"]
        if room_id in rooms:
            raise ValueError(f"Duplicate room ID found: {room_id}")
        availability = item.get("availability", {})
        available_quanta = (
            encode_availability(availability, qts)
            if availability
            else qts.get_all_operating_quanta()
        )

        # Use 'features' field directly, lowercased for consistency
        features = [f.strip().lower() for f in item.get("features", [])]

        rooms[room_id] = Room(
            room_id=room_id,
            name=item.get("name", room_id),
            capacity=item["capacity"],
            room_features=features,
            available_quanta=available_quanta,
        )
    return rooms


def link_courses_and_groups(
    courses: Dict[str, Course], groups: Dict[str, Group]
) -> None:
    """
    Links courses and groups based on group enrollment.

    Args:
        courses (Dict[str, Course]): Courses to update.
        groups (Dict[str, Group]): Groups with enrolled course codes.
    """
    for course in courses.values():
        course.enrolled_group_ids = []

    for group_id, group in groups.items():
        for course_code in group.enrolled_courses:
            if course_code in courses:
                if group_id not in courses[course_code].enrolled_group_ids:
                    courses[course_code].enrolled_group_ids.append(group_id)

    unassigned = [cid for cid, c in courses.items() if not c.enrolled_group_ids]
    if unassigned:
        print(f"Warning: Courses with no enrolled groups: {unassigned}")


def link_courses_and_instructors(
    courses: Dict[str, Course], instructors: Dict[str, Instructor]
) -> None:
    """
    Links instructors to the courses they are qualified to teach.

    Args:
        courses (Dict[str, Course]): Course dictionary.
        instructors (Dict[str, Instructor]): Instructor dictionary.
    """
    course_code_to_ids = {
        c.course_code: cid for cid, c in courses.items() if hasattr(c, "course_code")
    }

    for instructor in instructors.values():
        instructor.qualified_courses = []

    for course in courses.values():
        course.qualified_instructor_ids = []

    for instructor_id, instructor in instructors.items():
        for course_code in instructor.qualified_courses[:]:
            if course_code in courses:
                course = courses[course_code]
            elif course_code in course_code_to_ids:
                course = courses[course_code_to_ids[course_code]]
            else:
                continue

            if instructor_id not in course.qualified_instructor_ids:
                course.qualified_instructor_ids.append(instructor_id)
            if course.course_id not in instructor.qualified_courses:
                instructor.qualified_courses.append(course.course_id)
