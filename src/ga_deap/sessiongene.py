from dataclasses import dataclass
from typing import List


@dataclass
class SessionGene:
    """
    Each Gene represents 1 course session in the schedule.
    """

    course_id: str
    instructor_id: str
    group_id: str
    room_id: str
    quanta: List[int]
