"""
Course entity model for the timetabling system.
Represents a course with its attributes and requirements.
"""

from typing import List, Set, Optional
from dataclasses import dataclass


@dataclass
class Course:
    """
    Represents a course in the university timetabling system.
    
    Attributes:
        course_id: Unique identifier for the course
        name: Display name of the course
        sessions_per_week: Number of sessions required per week
        duration: Duration of each session in minutes
        required_room_type: Type of room required (e.g., 'lecture', 'lab', 'seminar')
        group_ids: List of student group IDs enrolled in this course
        qualified_instructor_ids: List of instructor IDs qualified to teach this course
        preferred_slots: Optional list of preferred time slots
        room_consistency_required: Whether all sessions need the same room
        max_gap_hours: Maximum gap allowed between sessions (in hours)
    """
    
    course_id: str
    name: str
    sessions_per_week: int
    duration: int  # in minutes
    required_room_type: str
    group_ids: List[str]
    qualified_instructor_ids: List[str]
    preferred_slots: Optional[List[str]] = None
    room_consistency_required: bool = False
    max_gap_hours: int = 48  # Maximum 48 hours between sessions
    
    def __post_init__(self):
        """Validate course data after initialization."""
        if self.sessions_per_week <= 0:
            raise ValueError(f"Course {self.course_id}: sessions_per_week must be positive")
        
        if self.duration <= 0:
            raise ValueError(f"Course {self.course_id}: duration must be positive")
        
        if not self.group_ids:
            raise ValueError(f"Course {self.course_id}: must have at least one group")
        
        if not self.qualified_instructor_ids:
            raise ValueError(f"Course {self.course_id}: must have at least one qualified instructor")
    
    def get_total_weekly_hours(self) -> float:
        """Calculate total weekly hours for this course."""
        return (self.sessions_per_week * self.duration) / 60.0
    
    def is_instructor_qualified(self, instructor_id: str) -> bool:
        """Check if an instructor is qualified to teach this course."""
        return instructor_id in self.qualified_instructor_ids
    
    def has_group(self, group_id: str) -> bool:
        """Check if a group is enrolled in this course."""
        return group_id in self.group_ids
    
    def get_enrolled_groups(self) -> Set[str]:
        """Get set of enrolled group IDs."""
        return set(self.group_ids)
    
    def __str__(self) -> str:
        return f"Course({self.course_id}: {self.name}, {self.sessions_per_week} sessions/week)"
    
    def __repr__(self) -> str:
        return self.__str__()
