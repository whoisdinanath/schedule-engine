from dataclasses import dataclass
from typing import List


@dataclass
class SessionGene:
    """
    Each SessionGene Represents a single session in the timetable.
    This is for the purpose of DEAP Encoding and Genetic Algorithm Engine (GAE)
    It contains the course, instructor, group(s), room, and quanta information.

    A single session can be scheduled for multiple groups simultaneously
    (e.g., a lecture for BAE2 and BAE4 at the same time in the same room).

    Clean architecture: course_id is plain code (e.g., "ENME 103"),
    course_type distinguishes "theory" vs "practical".
    """

    course_id: str
    course_type: str  # "theory" or "practical"
    instructor_id: str
    group_ids: List[str]  # Changed from group_id to support multiple groups
    room_id: str
    quanta: List[int]
