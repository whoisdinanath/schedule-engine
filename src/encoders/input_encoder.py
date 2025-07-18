import json
from src.entities import Course, Instructor, Room, Group
from typing import Dict, List
from .quantum_time_system import QuantumTimeSystem


def generate_instructors_from_courses(
    courses: Dict[str, Course], qts: QuantumTimeSystem
) -> Dict[str, Instructor]:
    """
    Generate instructors based on course requirements.
    Used when loading FullSyllabusAll format.
    """
    instructors = {}

    # Get unique departments/instructors needed
    instructor_depts = set()
    for course in courses.values():
        if hasattr(course, "department"):
            instructor_depts.add(course.department)

    # Create instructors for each department
    for dept in instructor_depts:
        instructor_id = f"I_{dept}"

        # Get courses for this instructor
        dept_courses = [
            c.course_id
            for c in courses.values()
            if hasattr(c, "department") and c.department == dept
        ]

        instructor = Instructor(
            instructor_id=instructor_id,
            name=f"Prof. {dept}",
            qualified_courses=dept_courses,
            is_full_time=True,
            available_quanta=qts.get_all_operating_quanta(),
        )
        instructors[instructor_id] = instructor

    return instructors


def generate_groups_from_courses(
    courses: Dict[str, Course], qts: QuantumTimeSystem
) -> Dict[str, Group]:
    """
    Generate groups based on course requirements.
    Used when loading FullSyllabusAll format.
    """
    groups = {}

    # Get unique departments/groups needed
    group_depts = set()
    for course in courses.values():
        if hasattr(course, "department"):
            group_depts.add(course.department)

    # Create groups for each department
    for dept in group_depts:
        group_id = f"G_{dept}"

        # Get courses for this group
        dept_courses = [
            c.course_id
            for c in courses.values()
            if hasattr(c, "department") and c.department == dept
        ]

        group = Group(
            group_id=group_id,
            name=f"{dept} Students",
            student_count=40,
            enrolled_courses=dept_courses,
            available_quanta=qts.get_all_operating_quanta(),
        )
        groups[group_id] = group

    return groups


def generate_rooms_from_courses(
    courses: Dict[str, Course], qts: QuantumTimeSystem
) -> Dict[str, Room]:
    """
    Generate rooms based on course requirements.
    Used when loading FullSyllabusAll format.
    """
    rooms = {}

    # Get unique room features needed
    room_features = set()
    for course in courses.values():
        room_features.add(course.required_room_features)

    room_id = 1

    # Create general lecture halls
    for i in range(5):
        room = Room(
            room_id=f"R{room_id}",
            name=f"Lecture Hall {i+1}",
            capacity=50,
            room_features="lecture",
            available_quanta=qts.get_all_operating_quanta(),
        )
        rooms[f"R{room_id}"] = room
        room_id += 1

    # Create specialized rooms
    for feature in room_features:
        if feature and feature != "lecture":
            room = Room(
                room_id=f"R{room_id}",
                name=f"{feature.title()} Room",
                capacity=30,
                room_features=feature,
                available_quanta=qts.get_all_operating_quanta(),
            )
            rooms[f"R{room_id}"] = room
            room_id += 1

    return rooms


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
            # FullSyllabusAll format
            course_id = f"C{i+1}"  # Generate course ID

            # Calculate weekly sessions based on L + T + P
            lecture_hours = item.get("L", 0)
            tutorial_hours = item.get("T", 0)
            practical_hours = item.get("P", 0)

            # Convert total hours to sessions (assuming 15-minute quanta)
            total_hours = lecture_hours + tutorial_hours + practical_hours
            weekly_sessions = max(
                1, int(total_hours)
            )  # At least 1 session, ensure integer

            # Determine room features from practical requirements
            room_features = "lab" if practical_hours > 0 else "lecture"
            if item.get("PracticalRoomFeatures"):
                room_features = item["PracticalRoomFeatures"].lower()

            # Generate group and instructor IDs based on department
            dept = item.get("Dept", "GENERAL")
            dept_list = [d.strip() for d in dept.split(",")]
            group_id = f"G_{dept_list[0]}"  # Use first department
            instructor_id = f"I_{dept_list[0]}"  # Use first department

            course = Course(
                course_id=course_id,
                name=item["CourseTitle"],
                quanta_per_week=weekly_sessions,
                required_room_features=room_features,
                enrolled_group_ids=[group_id],
                qualified_instructor_ids=[instructor_id],
            )

            # Store additional metadata
            course.instructor_id = instructor_id
            course.course_code = item["CourseCode"]
            course.department = dept_list[0]
            course.semester = item.get("Semester", 1)
            course.credits = item.get("Credits", 3)
            course.lecture_hours = lecture_hours
            course.tutorial_hours = tutorial_hours
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
