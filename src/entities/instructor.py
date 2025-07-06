"""
Instructor entity model for the timetabling system.
Represents an instructor with their qualifications and availability.
"""

from typing import List, Set, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, time


@dataclass
class Instructor:
    """
    Represents an instructor in the university timetabling system.
    
    Attributes:
        instructor_id: Unique identifier for the instructor
        name: Display name of the instructor
        qualified_courses: List of course IDs the instructor is qualified to teach
        available_slots: Dictionary mapping days to available time ranges
        preferred_slots: Optional dictionary of preferred teaching times
        max_hours_per_day: Maximum teaching hours per day
        max_hours_per_week: Maximum teaching hours per week
        min_break_minutes: Minimum break time between consecutive classes
        is_full_time: Whether the instructor is full-time (affects scheduling preferences)
        department: Department the instructor belongs to
    """
    
    instructor_id: str
    name: str
    qualified_courses: List[str]
    available_slots: Dict[str, List[str]]  # day -> list of time ranges
    preferred_slots: Optional[Dict[str, List[str]]] = None
    max_hours_per_day: int = 8
    max_hours_per_week: int = 40
    min_break_minutes: int = 15
    is_full_time: bool = True
    department: str = "General"
    
    def __post_init__(self):
        """Validate instructor data after initialization."""
        if not self.qualified_courses:
            raise ValueError(f"Instructor {self.instructor_id}: must be qualified for at least one course")
        
        if not self.available_slots:
            raise ValueError(f"Instructor {self.instructor_id}: must have available time slots")
        
        # Convert preferred_slots to empty dict if None
        if self.preferred_slots is None:
            self.preferred_slots = {}
    
    def is_qualified_for_course(self, course_id: str) -> bool:
        """Check if instructor is qualified to teach a specific course."""
        return course_id in self.qualified_courses
    
    def is_available_at_slot(self, day: str, time_slot: str) -> bool:
        """
        Check if instructor is available at a specific day and time slot.
        
        Args:
            day: Day of the week (e.g., 'monday', 'tuesday')
            time_slot: Time slot in format 'HH:MM-HH:MM'
        
        Returns:
            True if available, False otherwise
        """
        if day not in self.available_slots:
            return False
        
        return time_slot in self.available_slots[day]
    
    def has_preference_for_slot(self, day: str, time_slot: str) -> bool:
        """
        Check if instructor has a preference for a specific time slot.
        
        Args:
            day: Day of the week
            time_slot: Time slot in format 'HH:MM-HH:MM'
        
        Returns:
            True if preferred, False otherwise
        """
        if not self.preferred_slots or day not in self.preferred_slots:
            return False
        
        return time_slot in self.preferred_slots[day]
    
    def get_all_available_slots(self) -> List[tuple]:
        """
        Get all available time slots as a list of (day, time_slot) tuples.
        
        Returns:
            List of (day, time_slot) tuples
        """
        slots = []
        for day, time_slots in self.available_slots.items():
            for time_slot in time_slots:
                slots.append((day, time_slot))
        return slots
    
    def get_preferred_slots(self) -> List[tuple]:
        """
        Get all preferred time slots as a list of (day, time_slot) tuples.
        
        Returns:
            List of (day, time_slot) tuples
        """
        if not self.preferred_slots:
            return []
        
        slots = []
        for day, time_slots in self.preferred_slots.items():
            for time_slot in time_slots:
                slots.append((day, time_slot))
        return slots
    
    def get_qualification_set(self) -> Set[str]:
        """Get set of qualified course IDs."""
        return set(self.qualified_courses)
    
    def calculate_preference_score(self, day: str, time_slot: str) -> float:
        """
        Calculate preference score for a given time slot.
        
        Args:
            day: Day of the week
            time_slot: Time slot
        
        Returns:
            Score between 0 and 1 (1 = highly preferred, 0 = not preferred)
        """
        if self.has_preference_for_slot(day, time_slot):
            return 1.0
        elif self.is_available_at_slot(day, time_slot):
            return 0.5
        else:
            return 0.0
    
    def __str__(self) -> str:
        return f"Instructor({self.instructor_id}: {self.name}, {len(self.qualified_courses)} courses)"
    
    def __repr__(self) -> str:
        return self.__str__()
