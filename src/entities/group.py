"""
Group entity model for the timetabling system.
Represents a student group with enrollment information.
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass


@dataclass
class Group:
    """
    Represents a student group in the university timetabling system.


    Attributes:
        group_id: Unique identifier for the group
        name: Display name of the group
        student_count: Number of students in the group
        enrolled_courses: List of course IDs the group is enrolled in
        available_quanta: Set of available quantum time slots
        available_quanta: Set of available quantum time slots
    """

    group_id: str
    name: str
    student_count: int
    enrolled_courses: List[str]
    # available_quanta: Set[int]

    def __post_init__(self):
        """Validate group data after initialization."""
        if self.student_count <= 0:
            raise ValueError(f"Group {self.group_id}: student_count must be positive")

        # Note: enrolled_courses can be empty if populated later through course-group mapping

    def is_enrolled_in_course(self, course_id: str) -> bool:
        """Check if group is enrolled in a specific course."""
        """Check if group is enrolled in a specific course."""
        return course_id in self.enrolled_courses

    def get_enrolled_courses_set(self) -> Set[str]:
        """Get set of enrolled course IDs."""
        return set(self.enrolled_courses)

    def get_course_count(self) -> int:
        """Get number of courses the group is enrolled in."""
        return len(self.enrolled_courses)
