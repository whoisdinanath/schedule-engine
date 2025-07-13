import json
from src.entities.instructor import Instructor
from src.entities.course import Course
from src.entities.group import Group
from src.entities.room import Room
from typing import Dict, List
from src.encoders.quantum_time_system import QuantumTimeSystem


def encode_availability(availability_dict: Dict, qts: QuantumTimeSystem) -> set:
    quanta = set()
    for day, periods in availability_dict.items():
        for period in periods:
            start_q = qts.time_to_quanta(day, period["start"])
            end_q = qts.time_to_quanta(day, period["end"])
            quanta.update(range(start_q, end_q))
    return quanta


def load_instructors(path: str, qts: QuantumTimeSystem) -> Dict[str, Instructor]:
    data = json.load(open(path))
    instructors = {}
    for item in data:
        instructors[item["id"]] = Instructor(
            instructor_id=item["id"],
            name=item["name"],
            qualified_courses=[],  # To be backfilled
            is_full_time=False,
            available_quanta=encode_availability(item["availability"], qts),
        )
    return instructors


def load_courses(path: str) -> Dict[str, Course]:
    data = json.load(open(path))
    courses = {}
    for item in data:
        courses[item["cid"]] = Course(
            course_id=item["cid"],
            name=item["name"],
            quanta_per_week=item["weekly_sessions"],
            required_room_features=item["type"].lower(),
            enrolled_group_ids=[item["group_id"]],
            qualified_instructor_ids=[item["instructor_id"]],
        )
    return courses


def load_groups(path: str, qts: QuantumTimeSystem) -> Dict[str, Group]:
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
            else set()
        )
        if subgroups:
            per_subgroup = student_count // len(subgroups)
            for sub_id in subgroups:
                groups[sub_id] = Group(
                    group_id=sub_id,
                    name=f"{item['name']} Sub {sub_id[-1]}",
                    student_count=per_subgroup,
                    enrolled_courses=item["courses"],
                    available_quanta=available_quanta,
                )
        groups[parent_id] = Group(
            group_id=parent_id,
            name=item["name"],
            student_count=student_count,
            enrolled_courses=item["courses"],
            available_quanta=available_quanta,
        )
    return groups


def load_rooms(path: str, qts: QuantumTimeSystem) -> Dict[str, Room]:
    data = json.load(open(path))
    rooms = {}
    for item in data:
        room_availability = item.get("availability", {})
        available_quanta = (
            encode_availability(room_availability, qts) if room_availability else set()
        )
        rooms[item["room_id"]] = Room(
            room_id=item["room_id"],
            name=item.get("name", item["room_id"]),
            capacity=item["capacity"],
            room_features=item["type"].lower(),
            available_quanta=available_quanta,
        )
    return rooms
