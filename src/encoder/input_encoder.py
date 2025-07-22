"""
Input Data JSON Encoder Module

This module provides functions to load and encode input data from JSON files
into structured entities such as Course, Group, Instructor, and Room.

Functions:
- generate_instructors_from_courses
- generate_groups_from_courses
- generate_rooms_from_courses
- encode_availability
- load_instructors
- load_courses
- load_groups
- load_rooms
- link_courses_and_instructors
"""

import json
from src.entities.course import Course
from src.entities.group import Group
from src.entities.instructor import Instructor
from src.entities.room import Room
from src.encoder.quantum_time_system import QuantumTimeSystem

from typing import Dict, List


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
    Supports both Enhanced format and FullSyllabusAll format.

    Args:
        path (str): Path to the course JSON file.

    Returns:
        Dict[str, Course]: Dictionary of Course objects indexed by course ID.
    """
    data = json.load(open(path))
    courses = {}

    for i, item in enumerate(data):
        # Check if this is FullSyllabusAll format (has CourseCode, CourseTitle, etc.)
        if "CourseCode" in item and "CourseTitle" in item:
            # FullSyllabusAll format - Use CourseCode as course_id
            course_id = item["CourseCode"]  # Use actual course code as ID

            # Calculate weekly sessions based on L + T + P
            # Combine L and T as lecture hours, P as practical hours
            lecture_hours = item.get("L", 0) + item.get("T", 0)
            practical_hours = item.get("P", 0)

            # Convert total hours to sessions (assuming 15-minute quanta)
            total_hours = lecture_hours + practical_hours
            weekly_sessions = max(
                1, int(total_hours)
            )  # At least 1 session, ensure integer

            # Determine room features from practical requirements
            room_features = "lab" if practical_hours > 0 else "lecture"
            if item.get("PracticalRoomFeatures"):
                room_features = item["PracticalRoomFeatures"].lower()

            # Generate instructor ID based on department
            dept = item.get("Dept", "GENERAL")
            dept_list = [d.strip() for d in dept.split(",")]
            instructor_id = f"I_{dept_list[0]}"  # Use first department

            # Note: Group enrollment will be determined later from Groups.json data
            # Don't assign groups here - let the group data determine enrollment

            course = Course(
                course_id=course_id,
                name=item["CourseTitle"],
                quanta_per_week=weekly_sessions,
                required_room_features=room_features,
                enrolled_group_ids=[
                    "PLACEHOLDER"
                ],  # Temporary placeholder to pass validation
                qualified_instructor_ids=[instructor_id],
            )

            # Store additional metadata
            course.instructor_id = instructor_id
            course.course_code = item["CourseCode"]
            course.department = dept_list[0]
            course.semester = item.get("Semester", 1)
            course.credits = item.get("Credits", 3)
            course.lecture_hours = lecture_hours
            course.practical_hours = practical_hours

        else:
            # Enhanced format (existing logic)
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
            course_id = item["cid"]

        courses[course_id] = course

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


def link_courses_and_groups(
    courses: Dict[str, Course], groups: Dict[str, Group]
) -> None:
    """
    Links courses and groups based on the group enrollment data.
    Updates course enrolled_group_ids based on group enrollment data.

    Args:
        courses: Dictionary of Course objects
        groups: Dictionary of Group objects
    """
    # Clear existing course-group links in courses (remove placeholders)
    for course in courses.values():
        course.enrolled_group_ids = []

    # Re-establish links based on group enrollment data
    for group_id, group in groups.items():
        for course_code in group.enrolled_courses:
            # Find the course by course code
            if course_code in courses:
                # Add group to course's enrolled groups
                if group_id not in courses[course_code].enrolled_group_ids:
                    courses[course_code].enrolled_group_ids.append(group_id)

    # Validate that all courses have at least one group after linking
    unassigned_courses = []
    for course_id, course in courses.items():
        if not course.enrolled_group_ids:
            unassigned_courses.append(course_id)

    if unassigned_courses:
        print(
            f"Warning: The following courses have no enrolled groups: {unassigned_courses}"
        )
        print("These courses may not appear in any group's enrollment data.")


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
    # Save original instructor qualified courses before clearing
    instructor_original_courses = {}
    for instructor_id, instructor in instructors.items():
        instructor_original_courses[instructor_id] = instructor.qualified_courses.copy()

    # Clear existing links
    for instructor in instructors.values():
        instructor.qualified_courses = []

    for course in courses.values():
        course.qualified_instructor_ids = []

    # Create a mapping of course codes to course IDs for better matching
    course_code_to_id = {}
    for course_id, course in courses.items():
        if hasattr(course, "course_code"):
            course_code_to_id[course.course_code] = course_id

    # Re-establish links based on course data and instructor qualifications
    for course in courses.values():
        # Method 1: Direct instructor assignment from course data (if available)
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

    # Method 2: Link based on instructor's declared qualified courses
    for instructor_id, instructor in instructors.items():
        original_courses = instructor_original_courses[
            instructor_id
        ]  # Use saved original data

        for course_code in original_courses:
            # Try direct match first
            if course_code in courses:
                if course_code not in instructor.qualified_courses:
                    instructor.qualified_courses.append(course_code)
                if instructor_id not in courses[course_code].qualified_instructor_ids:
                    courses[course_code].qualified_instructor_ids.append(instructor_id)

            # Try course code mapping
            elif course_code in course_code_to_id:
                mapped_id = course_code_to_id[course_code]
                if mapped_id not in instructor.qualified_courses:
                    instructor.qualified_courses.append(mapped_id)
                if instructor_id not in courses[mapped_id].qualified_instructor_ids:
                    courses[mapped_id].qualified_instructor_ids.append(instructor_id)

    # Method 3: Ensure all courses have at least one qualified instructor
    # Assign unassigned courses to available instructors based on department
    for course_id, course in courses.items():
        if not course.qualified_instructor_ids:
            # Try to find instructor based on department
            dept = getattr(course, "department", "GENERAL")
            dept_instructor_id = f"I_{dept}"

            # If department-specific instructor exists, assign it
            if dept_instructor_id in instructors:
                course.qualified_instructor_ids.append(dept_instructor_id)
                if course_id not in instructors[dept_instructor_id].qualified_courses:
                    instructors[dept_instructor_id].qualified_courses.append(course_id)
            else:
                # Assign to first available instructor as fallback
                if instructors:
                    first_instructor = next(iter(instructors.keys()))
                    course.qualified_instructor_ids.append(first_instructor)
                    if course_id not in instructors[first_instructor].qualified_courses:
                        instructors[first_instructor].qualified_courses.append(
                            course_id
                        )
