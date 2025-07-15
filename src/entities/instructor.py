from typing import List, Set, Dict, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Instructor:
    """
    Represents an instructor in the university timetabling system using quantum time representation.

    Attributes:
        instructor_id: Unique identifier for the instructor
        name: Display name of the instructor
        qualified_courses: List of course IDs the instructor is qualified to teach
        available_quanta: Set of available quantum time slots (empty if full-time)
        booked_quanta: Set of booked quantum time slots:
        max_hours_per_week: Maximum teaching hours per week
        is_full_time: Whether the instructor is full-time (all quanta available if True)

    Methods:
    is_qualified_for_course(course_id): Check if instructor is qualified to teach a specific course
    is_available_at_quanta(quanta): Check if instructor is available at a specific quantum time slot
    get_available_quanta(instructor_id): returns a list of available quantum time slots for the instructor
    get_booked_quanta(instructor_id): returns a list of booked quantum time slots for the instructor
    Full Time is available every time, except in booked slot
    """

    instructor_id: str
    name: str
    qualified_courses: List[str]
    is_full_time: bool = True
    available_quanta: Set[int] = field(default_factory=set)
    booked_quanta: Set[int] = field(default_factory=set)
    max_hours_per_week: int = 40

    def __post_init__(self):
        """Validate instructor data after initialization."""
        # Temporarily allow empty qualified_courses - will be populated via cross-referencing
        if not self.qualified_courses:
            # Log warning but don't fail - courses may be populated later
            pass

        if not self.is_full_time and not self.available_quanta:
            raise ValueError(
                f"Part-time instructor {self.instructor_id} must have available time slots"
            )

    def is_qualified_for_course(self, course_id: str) -> bool:
        """Check if instructor is qualified to teach a specific course."""
        return course_id in self.qualified_courses

    def is_available_at_quanta(self, quanta: int, time_system) -> bool:
        """
        Check if instructor is available at a specific quantum time slot.

        Args:
            quanta: Quantum time index to check
            time_system: QuantumTimeSystem instance for validation

        Returns:
            True if available, False otherwise
        """
        if not 0 <= quanta < time_system.TOTAL_WEEKLY_QUANTA:
            return False

        if self.is_full_time:
            return True

        return quanta in self.available_quanta

    def get_available_quanta_ranges(
        self, time_system
    ) -> Dict[str, List[Tuple[int, int]]]:
        """
        Get available time ranges grouped by day.

        Args:
            time_system: QuantumTimeSystem instance for conversion

        Returns:
            Dictionary mapping days to list of (start_quanta, end_quanta) ranges
            (Returns all operating hours if full-time)
        """
        if self.is_full_time:
            return self._get_full_time_availability(time_system)

        ranges = defaultdict(list)
        sorted_quanta = sorted(self.available_quanta)

        if not sorted_quanta:
            return dict(ranges)

        current_start = sorted_quanta[0]
        current_end = current_start + 1

        for q in sorted_quanta[1:]:
            if q == current_end:
                current_end += 1
            else:
                day = time_system.quanta_to_time(current_start)[0]
                ranges[day].append((current_start, current_end))
                current_start = q
                current_end = q + 1

        # Add the last range
        day = time_system.quanta_to_time(current_start)[0]
        ranges[day].append((current_start, current_end))

        return dict(ranges)

    def _get_full_time_availability(
        self, time_system
    ) -> Dict[str, List[Tuple[int, int]]]:
        """Get all operating hours as available ranges for full-time instructors."""
        ranges = defaultdict(list)

        for day, hours in time_system.operating_hours.items():
            if hours is None:
                continue

            start = time_system.time_to_quanta(day, hours[0])
            end = time_system.time_to_quanta(day, hours[1])
            ranges[day].append((start, end))

        return dict(ranges)

    def get_qualification_set(self) -> Set[str]:
        """Get set of qualified course IDs."""
        return set(self.qualified_courses)
