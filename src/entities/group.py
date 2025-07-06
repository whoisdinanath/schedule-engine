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
        year_level: Academic year level (1, 2, 3, 4, etc.)
        program: Academic program or major
        max_daily_hours: Maximum hours of classes per day
        preferred_break_duration: Preferred break duration between classes (minutes)
        earliest_start_time: Earliest acceptable start time for classes
        latest_end_time: Latest acceptable end time for classes
        lunch_break_required: Whether a lunch break is required
        lunch_break_start: Preferred lunch break start time
        lunch_break_duration: Required lunch break duration (minutes)
    """
    
    group_id: str
    name: str
    student_count: int
    enrolled_courses: List[str]
    year_level: int = 1
    program: str = "General"
    max_daily_hours: int = 8
    preferred_break_duration: int = 15  # minutes
    earliest_start_time: str = "08:00"
    latest_end_time: str = "18:00"
    lunch_break_required: bool = True
    lunch_break_start: str = "12:00"
    lunch_break_duration: int = 60  # minutes
    
    def __post_init__(self):
        """Validate group data after initialization."""
        if self.student_count <= 0:
            raise ValueError(f"Group {self.group_id}: student_count must be positive")
        
        if not self.enrolled_courses:
            raise ValueError(f"Group {self.group_id}: must be enrolled in at least one course")
        
        if self.year_level <= 0:
            raise ValueError(f"Group {self.group_id}: year_level must be positive")
    
    def is_enrolled_in_course(self, course_id: str) -> bool:
        """
        Check if group is enrolled in a specific course.
        
        Args:
            course_id: Course identifier
        
        Returns:
            True if enrolled, False otherwise
        """
        return course_id in self.enrolled_courses
    
    def get_enrolled_courses_set(self) -> Set[str]:
        """Get set of enrolled course IDs."""
        return set(self.enrolled_courses)
    
    def get_course_count(self) -> int:
        """Get number of courses the group is enrolled in."""
        return len(self.enrolled_courses)
    
    def has_schedule_conflict(self, course1: str, course2: str, 
                            day: str, time_slot: str) -> bool:
        """
        Check if two courses would create a schedule conflict for this group.
        
        Args:
            course1: First course ID
            course2: Second course ID
            day: Day of the week
            time_slot: Time slot
        
        Returns:
            True if there's a conflict (both courses at same time)
        """
        return (self.is_enrolled_in_course(course1) and 
                self.is_enrolled_in_course(course2) and 
                course1 != course2)
    
    def calculate_workload_score(self, total_weekly_hours: float) -> float:
        """
        Calculate workload appropriateness score for the group.
        
        Args:
            total_weekly_hours: Total weekly class hours
        
        Returns:
            Score between 0 and 1 (1 = optimal workload)
        """
        # Optimal workload varies by year level
        optimal_hours = {
            1: 20,  # First year: 20 hours/week
            2: 22,  # Second year: 22 hours/week
            3: 24,  # Third year: 24 hours/week
            4: 18   # Final year: 18 hours/week (more project work)
        }
        
        target_hours = optimal_hours.get(self.year_level, 20)
        
        if total_weekly_hours <= 0:
            return 0.0
        
        ratio = total_weekly_hours / target_hours
        
        if 0.8 <= ratio <= 1.2:
            return 1.0  # Within 20% of optimal
        elif 0.6 <= ratio < 0.8 or 1.2 < ratio <= 1.4:
            return 0.7  # Moderate deviation
        elif 0.4 <= ratio < 0.6 or 1.4 < ratio <= 1.6:
            return 0.5  # Significant deviation
        else:
            return 0.2  # Poor workload distribution
    
    def requires_special_scheduling(self) -> bool:
        """
        Check if group requires special scheduling considerations.
        
        Returns:
            True if special scheduling is needed
        """
        # First year students might need more structured schedules
        # Final year students might need more flexibility
        return self.year_level == 1 or self.year_level >= 4
    
    def get_break_preferences(self) -> Dict[str, int]:
        """
        Get break preferences for the group.
        
        Returns:
            Dictionary with break preferences
        """
        return {
            'preferred_duration': self.preferred_break_duration,
            'lunch_break_required': self.lunch_break_required,
            'lunch_start': self.lunch_break_start,
            'lunch_duration': self.lunch_break_duration
        }
    
    def get_time_constraints(self) -> Dict[str, str]:
        """
        Get time constraints for the group.
        
        Returns:
            Dictionary with time constraints
        """
        return {
            'earliest_start': self.earliest_start_time,
            'latest_end': self.latest_end_time,
            'max_daily_hours': self.max_daily_hours
        }
    
    def __str__(self) -> str:
        return f"Group({self.group_id}: {self.name}, {self.student_count} students, Year {self.year_level})"
    
    def __repr__(self) -> str:
        return self.__str__()
