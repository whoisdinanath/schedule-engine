from dataclasses import dataclass
from typing import List


@dataclass
class SessionGene:
    """
    Each SessionGene Represents a single session in the timtetable.
    This is for the purpose of DEAP Encoding and Genetic Algorithm Engine (GAE)
    It contains the course, instructor, group, room, and quanta information.
    """

    course_id: str
    instructor_id: str
    group_id: str
    room_id: str
    quanta: List[int]
    
