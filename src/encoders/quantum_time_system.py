from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional, ClassVar
from collections import defaultdict


@dataclass
class QuantumTimeSystem:
    """
    Complete quantum-based time management system with:
    - Global operating hours configuration
    - Group-specific scheduling overrides
    - Holiday management
    - Pure quantum-based internal operations
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
        """Initialize with default operating hours and build quanta map"""
        self.operating_hours = self.DEFAULT_OPERATING_HOURS.copy()
        self._build_quanta_map()

    def _build_quanta_map(self) -> None:
        """Convert all time strings to quanta indices for faster processing"""
        self.quanta_hours = {}
        for day, hours in self.operating_hours.items():
            self.quanta_hours[day] = (
                self._convert_hours_to_quanta(day, hours) if hours else None
            )

    def _convert_hours_to_quanta(
        self, day: str, hours: Tuple[str, str]
    ) -> Tuple[int, int]:
        """Convert operating hours tuple to quanta indices"""
        start = self.time_to_quanta(day, hours[0]) % self.QUANTA_PER_DAY
        end = self.time_to_quanta(day, hours[1]) % self.QUANTA_PER_DAY
        return (start, end)

    @classmethod
    def time_to_quanta(cls, day: str, time_str: str) -> int:
        """Convert (day, time) to global quantum index"""
        day_idx = cls._validate_and_get_day_index(day)
        hours, minutes = map(int, time_str.split(":"))
        return (
            day_idx * cls.QUANTA_PER_DAY
            + hours * cls.QUANTA_PER_HOUR
            + minutes // cls.QUANTUM_MINUTES
        )

    @classmethod
    def _validate_and_get_day_index(cls, day: str) -> int:
        """Validate day name and return its index"""
        try:
            return cls.DAY_NAMES.index(day.capitalize())
        except ValueError as e:
            raise ValueError(f"Invalid day name: {day}") from e

    @classmethod
    def quanta_to_time(cls, quantum: int) -> Tuple[str, str]:
        """Convert global quantum back to (day, time)"""
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
        """Update operating hours for a specific day"""
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
        """Convert JSON schedule to quantum set"""
        occupied_quanta = set()

        for day, periods in schedule_json.items():
            if not self.is_operational(day):
                continue
            for period in periods:
                occupied_quanta.update(self._get_period_quanta(day, period))

        return occupied_quanta

    def _get_period_quanta(self, day: str, period: Dict) -> range:
        """Get quantum range for a single period"""
        start = self.time_to_quanta(day, period["start"])
        end = self.time_to_quanta(day, period["end"])  # Exclusive
        return range(start, end)

    def decode_schedule(self, quanta_set: Set[int]) -> Dict[str, List[Dict]]:
        """Convert quantum set back to JSON schedule"""
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
        """Create a period dictionary from quanta values"""
        return {
            "start": self._quanta_to_time_str(start),
            "end": self._quanta_to_time_str(end),
        }

    def _quanta_to_time_str(self, quanta: int) -> str:
        """Convert within-day quanta to time string"""
        hour, minute_quanta = divmod(quanta, self.QUANTA_PER_HOUR)
        minute = minute_quanta * self.QUANTUM_MINUTES
        return f"{hour:02d}:{minute:02d}"


@dataclass
class StudentGroup:
    """Student group with customizable scheduling constraints"""

    id: str
    name: str
    size: int
    course_ids: List[str]
    custom_hours: Dict[str, Optional[Tuple[str, str]]] = field(default_factory=dict)

    def get_effective_hours(
        self, day: str, time_system: QuantumTimeSystem
    ) -> Tuple[int, int]:
        """Get operating hours in quanta for specific day"""
        day = day.capitalize()
        hours = self._get_hours_for_day(day, time_system)
        return self._convert_to_quanta(day, hours, time_system)

    def _get_hours_for_day(
        self, day: str, time_system: QuantumTimeSystem
    ) -> Tuple[str, str]:
        """Get operating hours for a specific day"""
        if day in self.custom_hours and self.custom_hours[day] is not None:
            return self.custom_hours[day]
        if time_system.is_operational(day):
            return time_system.operating_hours[day]
        raise ValueError(f"{day} is non-operational for this group")

    def _convert_to_quanta(
        self, day: str, hours: Tuple[str, str], time_system: QuantumTimeSystem
    ) -> Tuple[int, int]:
        """Convert time strings to quanta values"""
        start = time_system.time_to_quanta(day, hours[0]) % time_system.QUANTA_PER_DAY
        end = time_system.time_to_quanta(day, hours[1]) % time_system.QUANTA_PER_DAY
        return start, end


# Example usage
if __name__ == "__main__":
    qts = QuantumTimeSystem()
    print("Unit session duration (quanta):", qts.UNIT_SESSION_DURATION_QUANTA)

    # Find quanta for Sunday 00:00 to 04:35
    start_quanta = qts.time_to_quanta("Sunday", "00:00")
    end_quanta = qts.time_to_quanta("Sunday", "04:46")
    print(f"Sunday 00:00 quanta: {start_quanta}")
    print(f"Sunday 04:35 quanta: {end_quanta}")
    print(
        f"Quanta indices for Sunday 00:00-04:35: {list(range(start_quanta, end_quanta))}"
    )

    # Example: encode a time period into quanta
    day = "Monday"
    start_time = "09:00"
    end_time = "11:30"
    start_q = qts.time_to_quanta(day, start_time)
    end_q = qts.time_to_quanta(day, end_time)
    print(
        f"{day} {start_time}-{end_time} encoded as quanta: {list(range(start_q, end_q))}"
    )
