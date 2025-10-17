"""Debug find_suitable_rooms."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.encoder.input_encoder import load_courses, load_groups, load_rooms
from src.encoder.quantum_time_system import QuantumTimeSystem

qts = QuantumTimeSystem()
courses = load_courses("data/Course.json")
groups = load_groups("data/Groups.json", qts)
rooms = load_rooms("data/Rooms.json", qts)

# Get practical course
practical_course = [
    c
    for c in courses.values()
    if c.course_id == "ENAR 101" and c.course_type == "practical"
][0]

print(f"Course: {practical_course.course_id} ({practical_course.course_type})")
print(f"Required: {repr(practical_course.required_room_features)}")
print()

# Manually check room matching
required_str = practical_course.required_room_features.lower().strip()
print(f'Required (normalized): "{required_str}"')
print()

# Check a few rooms
test_rooms = list(rooms.values())[:5]
for room in test_rooms:
    room_str = room.room_features.lower().strip()
    exact_match = room_str == required_str
    print(f'Room {room.room_id}: "{room_str}" == "{required_str}" ? {exact_match}')
