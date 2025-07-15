import json
from src.entities import Course, Instructor, Room, Group
from typing import Dict, List
from src.encoders import QuantumTimeSystem


def encode_availability(availability_dict: Dict, qts: QuantumTimeSystem) -> set:
    """
    Converts human-readable availability into a set of quantum indices.

    Args:
        availability_dict (Dict): Dictionary of availability per day, each with a list of {"start", "end"} time pairs.
        qts (QuantumTimeSystem): Instance of QuantumTimeSystem for time conversion.

    Returns:
        set: A set of quantum indices representing available times.

    Example:
        {
            "Monday": [{"start": "08:00", "end": "10:00"}]
        } → {32, 33, 34, 35, 36, 37, 38, 39}
    """
    quanta = set()
    for day, periods in availability_dict.items():
        for period in periods:
            start_q = qts.time_to_quanta(day, period["start"])
            end_q = qts.time_to_quanta(day, period["end"])
            quanta.update(range(start_q, end_q))
    return quanta


def load_instructors(path: str, qts: QuantumTimeSystem) -> Dict[str, Instructor]:
    """
    Loads instructor data from a JSON file and encodes availability.

    Args:
        path (str): Path to the instructor JSON file.
        qts (QuantumTimeSystem): QuantumTimeSystem instance for time conversion.

    Returns:
        Dict[str, Instructor]: Dictionary of Instructor objects indexed by instructor ID.
    """
    data = json.load(open(path))
    instructors = {}
    for item in data:
        # Handle availability - if not provided, assume full-time
        availability = item.get("availability", {})
        is_full_time = not bool(
            availability
        )  # If no availability specified, assume full-time
        available_quanta = (
            encode_availability(availability, qts) if availability else set()
        )

        # Extract qualified courses from JSON data
        qualified_courses = item.get("courses", [])

        instructors[item["id"]] = Instructor(
            instructor_id=item["id"],
            name=item["name"],
            qualified_courses=qualified_courses,
            is_full_time=is_full_time,
            available_quanta=available_quanta,
        )
    return instructors


def load_courses(path: str) -> Dict[str, Course]:
    """
    Loads course data from a JSON file.

    Args:
        path (str): Path to the course JSON file.

    Returns:
        Dict[str, Course]: Dictionary of Course objects indexed by course ID.
    """
    data = json.load(open(path))
    courses = {}
    for item in data:
        course = Course(
            course_id=item["cid"],
            name=item["name"],
            quanta_per_week=item["weekly_sessions"],
            required_room_features=item["type"].lower(),
            enrolled_group_ids=[item["group_id"]],
            qualified_instructor_ids=[item["instructor_id"]],
        )
        # Store instructor_id for linking
        course.instructor_id = item["instructor_id"]
        courses[item["cid"]] = course
    return courses


def load_groups(path: str, qts: QuantumTimeSystem) -> Dict[str, Group]:
    """
    Loads group data from a JSON file. Handles both parent and subgroup structures.

    Args:
        path (str): Path to the group JSON file.
        qts (QuantumTimeSystem): QuantumTimeSystem instance for time conversion.

    Returns:
        Dict[str, Group]: Dictionary of Group objects indexed by group/subgroup ID.
    """
    data = json.load(open(path))
    groups = {}
    for item in data:
        parent_id = item["group_id"]
        student_count = item["student_count"]
        subgroups = item.get("subgroups", [])
        group_availability = item.get("availability", {})
        available_quanta = (
            encode_availability(group_availability, qts)
            if group_availability
            else qts.get_all_operating_quanta()  # Default to all operating hours
        )

        # Get enrolled courses - handle different data formats
        enrolled_courses = item.get("courses", [])
        if not enrolled_courses:
            # If no courses specified, this might be handled later through course-group mapping
            enrolled_courses = []

        if subgroups:
            per_subgroup = student_count // len(subgroups)
            for sub_id in subgroups:
                groups[sub_id] = Group(
                    group_id=sub_id,
                    name=f"{item['name']} Sub {sub_id[-1]}",
                    student_count=per_subgroup,
                    enrolled_courses=enrolled_courses,
                    available_quanta=available_quanta,
                )

        groups[parent_id] = Group(
            group_id=parent_id,
            name=item["name"],
            student_count=student_count,
            enrolled_courses=enrolled_courses,
            available_quanta=available_quanta,
        )
    return groups


def load_rooms(path: str, qts: QuantumTimeSystem) -> Dict[str, Room]:
    """
    Loads room data from a JSON file and encodes availability.

    Args:
        path (str): Path to the room JSON file.
        qts (QuantumTimeSystem): QuantumTimeSystem instance for time conversion.

    Returns:
        Dict[str, Room]: Dictionary of Room objects indexed by room ID.
    """
    data = json.load(open(path))
    rooms = {}
    for item in data:
        room_availability = item.get("availability", {})
        available_quanta = (
            encode_availability(room_availability, qts)
            if room_availability
            else qts.get_all_operating_quanta()
        )
        rooms[item["room_id"]] = Room(
            room_id=item["room_id"],
            name=item.get("name", item["room_id"]),
            capacity=item["capacity"],
            room_features=item.get("type", "general").lower(),
            available_quanta=available_quanta,
        )
    return rooms


def link_courses_and_instructors(
    courses: Dict[str, Course], instructors: Dict[str, Instructor]
) -> None:
    """
    Links courses and instructors based on the loaded data.
    Updates instructor qualified_courses and course qualified_instructor_ids.

    Args:
        courses: Dictionary of Course objects
        instructors: Dictionary of Instructor objects
    """
    # Clear existing links
    for instructor in instructors.values():
        instructor.qualified_courses = []

    for course in courses.values():
        course.qualified_instructor_ids = []

    # Re-establish links based on course data
    for course in courses.values():
        # Each course should have an instructor_id in the JSON
        if hasattr(course, "instructor_id"):
            instructor_id = course.instructor_id
            if instructor_id in instructors:
                # Add course to instructor's qualified courses
                if course.course_id not in instructors[instructor_id].qualified_courses:
                    instructors[instructor_id].qualified_courses.append(
                        course.course_id
                    )

                # Add instructor to course's qualified instructors
                if instructor_id not in course.qualified_instructor_ids:
                    course.qualified_instructor_ids.append(instructor_id)
