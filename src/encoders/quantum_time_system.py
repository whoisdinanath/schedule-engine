"""
CONSTANTS:
QUANTUM_MINUTES: Duration of a Single Quantum in Minutes
UNIT_COURSE_DURATION: Standard Course Duration in Minutes
QUANTA_PER_HOUR: Number of Quanta in One Hour
QUANTA_PER_DAY: Number of Quanta in One Day
TOTAL_WEEKLY_QUANTA: Total Quanta in a Week
UNIT_SESSION_DURATION_QUANTA: Duration of a Single Session in Quanta
DAY_NAMES: List of Days in a Week
DEFAULT_OPERATING_HOURS: Default Operating Hours for Each Day


"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, ClassVar
from collections import defaultdict


@dataclass
class QuantumTimeSystem:
    """
    A quantum-based time system for scheduling.
    - Time is represented in 15-minute units (quanta).
    - Operating hours are configured per day.
    - Supports schedule encoding/decoding into quantum sets.
    - Enables efficient time range calculation, day-wise quanta grouping and merging

    Methods:
    For use from outside the class:



    Example:
        qts = QuantumTimeSystem()
        q = qts.time_to_quanta("Monday", "10:30")
        day, time = qts.quanta_to_time(q)
    """

    # Constants
    QUANTUM_MINUTES: ClassVar[int] = 15
    UNIT_COURSE_DURATION: ClassVar[int] = 60  # Duration in minutes

    # Derived constants
    QUANTA_PER_HOUR: ClassVar[int] = 60 // QUANTUM_MINUTES
    QUANTA_PER_DAY: ClassVar[int] = 24 * QUANTA_PER_HOUR
    TOTAL_WEEKLY_QUANTA: ClassVar[int] = 7 * QUANTA_PER_DAY
    UNIT_SESSION_DURATION_QUANTA: ClassVar[int] = (
        UNIT_COURSE_DURATION // QUANTUM_MINUTES
    )

    # Day configuration
    DAY_NAMES: ClassVar[List[str]] = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]

    DEFAULT_OPERATING_HOURS: ClassVar[Dict[str, Optional[Tuple[str, str]]]] = {
        "Monday": ("08:00", "20:00"),
        "Tuesday": ("08:00", "20:00"),
        "Wednesday": ("08:00", "20:00"),
        "Thursday": ("08:00", "20:00"),
        "Friday": ("08:00", "20:00"),
        "Saturday": ("09:00", "14:00"),  # Shorter Saturday
        "Sunday": None,  # Closed by default
    }

    def __init__(self):
        """
        Initializes the QuantumTimeSystem with default operating hours.
        Precomputes quantum bounds for each day

        Example:
            qts = QuantumTimeSystem()
        """
        self.operating_hours = self.DEFAULT_OPERATING_HOURS.copy()
        self._build_quanta_map()

    def _build_quanta_map(self) -> None:
        """
        Builds a mapping of days to their quantum operating ranges.

        Example:
            self.quanta_hours['Monday'] = (32,80)
        """
        self.quanta_hours = {}
        for day, hours in self.operating_hours.items():
            self.quanta_hours[day] = (
                self._convert_hours_to_quanta(day, hours) if hours else None
            )

    def _convert_hours_to_quanta(
        self, day: str, hours: Tuple[str, str]
    ) -> Tuple[int, int]:
        """
        Converts start and end times for a day into a tuple of quantum indices.

        Args:
            day: Day of the week
            hours: Tuple of (start_time, end_time) in "HH:MM" format

        Returns:
            Tuple[int, int]: Start and end quantum indices

        Example:
            (32, 80) for ("08:00", "20:00") on Monday


        """
        start = self.time_to_quanta(day, hours[0]) % self.QUANTA_PER_DAY
        end = self.time_to_quanta(day, hours[1]) % self.QUANTA_PER_DAY
        return (start, end)

    @classmethod
    def time_to_quanta(cls, day: str, time_str: str) -> int:
        """
        Convert (day, time) to global quantum index (GQI)

        Args:
            day: Day of the week
            time_str: Time string in HH:MM format

        Returns:
            int: Global Quantum Index (GQI)

        Example:
            Monday 09:15 -> 129
        """
        day_idx = cls._validate_and_get_day_index(day)
        hours, minutes = map(int, time_str.split(":"))
        return (
            day_idx * cls.QUANTA_PER_DAY
            + hours * cls.QUANTA_PER_HOUR
            + minutes // cls.QUANTUM_MINUTES
        )

    @classmethod
    def _validate_and_get_day_index(cls, day: str) -> int:
        """
        Validates and returns the index of the day name.

        Args:
            day: Day name

        Returns:
            Index: (0-6)

        Raises:
            ValueError: If the day name is invalid
        """
        try:
            return cls.DAY_NAMES.index(day.capitalize())
        except ValueError as e:
            raise ValueError(f"Invalid day name: {day}") from e

    @classmethod
    def quanta_to_time(cls, quantum: int) -> Tuple[str, str]:
        """
        Convert global quantum back to (day, HH:MM) format

        Args:
            quantum: Global Quantum Index in the range (0, TOTAL_WEEKLY_QUANTA)

        Returns:
            Tuple of the day name and time string in HH:MM format

        """
        cls._validate_quantum(quantum)

        day_idx, quanta_in_day = divmod(quantum, cls.QUANTA_PER_DAY)
        hour, minute_quanta = divmod(quanta_in_day, cls.QUANTA_PER_HOUR)
        minute = minute_quanta * cls.QUANTUM_MINUTES

        return cls.DAY_NAMES[day_idx], f"{hour:02d}:{minute:02d}"

    @classmethod
    def _validate_quantum(cls, quantum: int) -> None:
        """Validate quantum value is within bounds"""
        if not 0 <= quantum < cls.TOTAL_WEEKLY_QUANTA:
            raise ValueError(
                f"Quantum must be between 0 and {cls.TOTAL_WEEKLY_QUANTA-1}"
            )

    def set_operating_hours(
        self, day: str, start_time: Optional[str], end_time: Optional[str]
    ) -> None:
        """

        Set or Override the operating hours for a specific day.

        Args:
            day: Day name
            start_time: Start time string (HH:MM) format
            end_time: End time string (HH:MM) format

        Example:
            qts.set_operating_hours("Monday", "08:00", "20:00")

        """
        day = day.capitalize()
        self._validate_day(day)

        self.operating_hours[day] = (
            (start_time, end_time) if start_time and end_time else None
        )
        self._build_quanta_map()

    def _validate_day(self, day: str) -> None:
        """Validate that day exists in system"""
        if day not in self.DAY_NAMES:
            raise ValueError(f"Invalid day: {day}")

    def is_operational(self, day: str) -> bool:
        """Check if a day has operating hours"""
        return self.operating_hours.get(day.capitalize()) is not None

    def encode_schedule(self, schedule_json: Dict) -> Set[int]:
        """
        Convert JSON schedule to quantum set

        Args:
            schedule_json: { day: [{"start": "HH:MM", "end": "HH:MM"}] }

        Returns:
            Set of quantum indices
        """
        occupied_quanta = set()

        for day, periods in schedule_json.items():
            if not self.is_operational(day):
                continue
            for period in periods:
                occupied_quanta.update(self._get_period_quanta(day, period))

        return occupied_quanta

    def _get_period_quanta(self, day: str, period: Dict) -> range:
        """
        Get quantum index range for a single period

        Args:
            day: Day of the week
            period: {"start": "HH:MM", "end": "HH:MM"}

        Returns:
            range(start, end) of quantum indices
        """
        start = self.time_to_quanta(day, period["start"])
        end = self.time_to_quanta(day, period["end"])  # Exclusive
        return range(start, end)

    def decode_schedule(self, quanta_set: Set[int]) -> Dict[str, List[Dict]]:
        """
        Converts a set of quantum indices back to readable JSON schedule.

        Args:
            quanta_set: Set of quantum indices

        Returns:
            { day: [ {"start": "HH:MM", "end": "HH:MM"}, ... ] }
        """
        schedule = {day: [] for day in self.DAY_NAMES}
        day_groups = self._group_quanta_by_day(quanta_set)

        for day_idx, quanta_list in day_groups.items():
            if quanta_list:
                schedule[self.DAY_NAMES[day_idx]] = self._merge_consecutive_quanta(
                    quanta_list
                )

        return {day: periods for day, periods in schedule.items() if periods}

    def _group_quanta_by_day(self, quanta_set: Set[int]) -> Dict[int, List[int]]:
        """Group quanta by day index"""
        day_groups = defaultdict(list)
        for q in sorted(quanta_set):
            day_idx = q // self.QUANTA_PER_DAY
            day_groups[day_idx].append(q % self.QUANTA_PER_DAY)
        return day_groups

    def _merge_consecutive_quanta(self, quanta_list: List[int]) -> List[Dict]:
        """Merge consecutive quanta into time periods"""
        periods = []
        if not quanta_list:
            return periods

        current_start = quanta_list[0]
        current_end = current_start + 1

        for q in quanta_list[1:]:
            if q == current_end:
                current_end += 1
            else:
                periods.append(self._create_period(current_start, current_end))
                current_start = q
                current_end = q + 1

        periods.append(self._create_period(current_start, current_end))
        return periods

    def _create_period(self, start: int, end: int) -> Dict:
        """
        Converts start and end quanta into a period dictionary
        """
        return {
            "start": self._quanta_to_time_str(start),
            "end": self._quanta_to_time_str(end),
        }

    def _quanta_to_time_str(self, quanta: int) -> str:
        """
        Converts a within-day quantum index to HH:MM string.
        """
        hour, minute_quanta = divmod(quanta, self.QUANTA_PER_HOUR)
        minute = minute_quanta * self.QUANTUM_MINUTES
        return f"{hour:02d}:{minute:02d}"
