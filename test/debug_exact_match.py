"""Debug why exact_matches is empty."""

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
course = [
    c
    for c in courses.values()
    if c.course_id == "ENAR 101" and c.course_type == "practical"
][0]

print(f"Course: {course.course_id}")
print(f"Required: {repr(course.required_room_features)}")
print(f"Enrolled groups: {course.enrolled_group_ids}")
print()

# Simulate find_suitable_rooms logic
required_features = getattr(course, "required_room_features", "classroom")
course_id = getattr(course, "course_id", "")

# Find group size
max_group_size = 30  # default
for group in groups.values():
    if course_id in getattr(group, "enrolled_courses", []):
        group_size = getattr(group, "student_count", 30)
        max_group_size = max(max_group_size, group_size)
        print(f"Found enrolled group {group.group_id}: {group_size} students")

print(f"Max group size: {max_group_size}")
print()

# Check rooms
exact_matches = []
for room in rooms.values():
    room_capacity = getattr(room, "capacity", 50)

    # Capacity check
    if room_capacity < max_group_size:
        continue

    room_features = getattr(room, "room_features", "classroom")
    required_str = (
        (
            required_features
            if isinstance(required_features, str)
            else str(required_features)
        )
        .lower()
        .strip()
    )
    room_str = (
        (room_features if isinstance(room_features, str) else str(room_features))
        .lower()
        .strip()
    )

    # Exact match check
    if room_str == required_str:
        exact_matches.append(room)

print(f"Exact matches found: {len(exact_matches)}")
if exact_matches:
    for i, r in enumerate(exact_matches[:5]):
        print(f"  {i+1}. {r.room_id}: {r.room_features}, capacity={r.capacity}")
else:
    # Check why
    practical_rooms = [r for r in rooms.values() if r.room_features == "practical"]
    print(f"Total practical rooms in dataset: {len(practical_rooms)}")
    print("Sample practical rooms:")
    for r in practical_rooms[:5]:
        print(f"  {r.room_id}: capacity={r.capacity}")
