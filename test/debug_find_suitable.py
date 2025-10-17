"""Debug find_suitable_rooms with actual function call."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.encoder.input_encoder import (
    load_courses,
    load_groups,
    load_rooms,
    link_courses_and_groups,
)
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.ga.population import find_suitable_rooms

qts = QuantumTimeSystem()
courses = load_courses("data/Course.json")
groups = load_groups("data/Groups.json", qts)
rooms = load_rooms("data/Rooms.json", qts)
link_courses_and_groups(courses, groups)


class SimpleContext(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"No attribute '{key}'")


context = SimpleContext(
    {
        "courses": courses,
        "groups": groups,
        "rooms": rooms,
        "available_quanta": qts.get_all_operating_quanta(),
    }
)

# Get practical course
practical_course = [
    c
    for c in courses.values()
    if c.course_id == "ENAR 101" and c.course_type == "practical"
][0]

print(f"Course: {practical_course.course_id} ({practical_course.course_type})")
print(f"Required: {repr(practical_course.required_room_features)}")
print(f"Enrolled groups: {practical_course.enrolled_group_ids}")
print()

# Check group sizes
if practical_course.enrolled_group_ids:
    for gid in practical_course.enrolled_group_ids:
        if gid in groups:
            print(f"Group {gid}: {groups[gid].student_count} students")
print()

# Call function
suitable_rooms = find_suitable_rooms(practical_course, "practical", context)
print(f"Found {len(suitable_rooms)} suitable rooms")
if suitable_rooms:
    # Check room types
    for i, room in enumerate(suitable_rooms[:5]):
        print(
            f"  {i+1}. {room.room_id}: {room.room_features}, capacity={room.capacity}"
        )
