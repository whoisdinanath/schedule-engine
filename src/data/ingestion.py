"""
Data ingestion module for loading course, instructor, room, and group data.
Supports CSV and JSON formats with comprehensive error handling.
"""

import pandas as pd
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger


class DataIngestion:
    """
    Handles data ingestion from various file formats.
    Converts raw data into entity objects with validation.
    Also Encodes the time based input data to quanta based representation for our system
    """

    def __init__(self):
        """Initialize the data ingestion system."""
        self.logger = get_logger(self.__class__.__name__)
        self.courses: Dict[str, Course] = {}
        self.instructors: Dict[str, Instructor] = {}
        self.rooms: Dict[str, Room] = {}
        self.groups: Dict[str, Group] = {}

    def load_data(
        self,
        courses_file: str,
        instructors_file: str,
        rooms_file: str,
        groups_file: str,
    ) -> bool:
        """
        Load all data files and create entity objects.

        Args:
            courses_file: Path to courses data file
            instructors_file: Path to instructors data file
            rooms_file: Path to rooms data file
            groups_file: Path to groups data file

        Returns:
            True if all data loaded successfully, False otherwise
        """
        try:
            self.logger.info("Starting data loading process...")

            # Load courses
            if not self._load_courses(courses_file):
                return False

            # Load instructors
            if not self._load_instructors(instructors_file):
                return False

            # Load rooms
            if not self._load_rooms(rooms_file):
                return False

            # Load groups
            if not self._load_groups(groups_file):
                return False

            # Cross-validate data integrity
            if not self._validate_data_integrity():
                return False

            self.logger.info(
                f"Data loading completed successfully: "
                f"{len(self.courses)} courses, "
                f"{len(self.instructors)} instructors, "
                f"{len(self.rooms)} rooms, "
                f"{len(self.groups)} groups"
            )

            return True

        except Exception as e:
            self.logger.error(f"Error during data loading: {str(e)}")
            return False

    def _load_courses(self, file_path: str) -> bool:
        """Load courses from file."""
        try:
            self.logger.info(f"Loading courses from {file_path}")

            if file_path.endswith(".json"):
                data = self._load_json(file_path)
                courses_data = (
                    data if isinstance(data, list) else data.get("courses", [])
                )
            else:
                df = pd.read_csv(file_path)
                courses_data = df.to_dict("records")

            for row in courses_data:
                course = self._create_course_from_data(row)
                if course:
                    self.courses[course.course_id] = course

            self.logger.info(f"Loaded {len(self.courses)} courses")
            return True

        except Exception as e:
            self.logger.error(f"Error loading courses: {str(e)}")
            return False

    def _load_instructors(self, file_path: str) -> bool:
        """Load instructors from file."""
        try:
            self.logger.info(f"Loading instructors from {file_path}")

            if file_path.endswith(".json"):
                data = self._load_json(file_path)
                instructors_data = (
                    data if isinstance(data, list) else data.get("instructors", [])
                )
            else:
                df = pd.read_csv(file_path)
                instructors_data = df.to_dict("records")

            for row in instructors_data:
                instructor = self._create_instructor_from_data(row)
                if instructor:
                    self.instructors[instructor.instructor_id] = instructor

            self.logger.info(f"Loaded {len(self.instructors)} instructors")
            return True

        except Exception as e:
            self.logger.error(f"Error loading instructors: {str(e)}")
            return False

    def _load_rooms(self, file_path: str) -> bool:
        """Load rooms from file."""
        try:
            self.logger.info(f"Loading rooms from {file_path}")

            if file_path.endswith(".json"):
                data = self._load_json(file_path)
                rooms_data = data if isinstance(data, list) else data.get("rooms", [])
            else:
                df = pd.read_csv(file_path)
                rooms_data = df.to_dict("records")

            for row in rooms_data:
                room = self._create_room_from_data(row)
                if room:
                    self.rooms[room.room_id] = room

            self.logger.info(f"Loaded {len(self.rooms)} rooms")
            return True

        except Exception as e:
            self.logger.error(f"Error loading rooms: {str(e)}")
            return False

    def _load_groups(self, file_path: str) -> bool:
        """Load groups from file."""
        try:
            self.logger.info(f"Loading groups from {file_path}")

            if file_path.endswith(".json"):
                data = self._load_json(file_path)
                groups_data = data if isinstance(data, list) else data.get("groups", [])
            else:
                df = pd.read_csv(file_path)
                groups_data = df.to_dict("records")

            for row in groups_data:
                group = self._create_group_from_data(row)
                if group:
                    self.groups[group.group_id] = group

            self.logger.info(f"Loaded {len(self.groups)} groups")
            return True

        except Exception as e:
            self.logger.error(f"Error loading groups: {str(e)}")
            return False

    def _load_json(self, file_path: str) -> Any:
        """Load JSON data from file."""
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _create_course_from_data(self, data: Dict[str, Any]) -> Optional[Course]:
        """Create Course object from data dictionary."""
        try:
            # Parse list fields that might be strings
            group_ids = self._parse_list_field(data.get("group_ids", ""))
            qualified_instructors = self._parse_list_field(
                data.get("qualified_instructor_ids", "")
            )
            preferred_slots = None
            if "preferred_slots" in data and data["preferred_slots"]:
                preferred_slots = self._parse_list_field(data["preferred_slots"])

            # Skip courses with no qualified instructors
            if not qualified_instructors:
                self.logger.warning(
                    f"Skipping course {data.get('course_id', 'unknown')}: no qualified instructors specified"
                )
                return None

            # Skip courses with no groups
            if not group_ids:
                self.logger.warning(
                    f"Skipping course {data.get('course_id', 'unknown')}: no groups specified"
                )
                return None

            course = Course(
                course_id=str(data["course_id"]),
                name=str(data["name"]),
                sessions_per_week=int(data["sessions_per_week"]),
                duration=int(data["duration"]),
                required_room_type=str(data["required_room_type"]),
                group_ids=group_ids,
                qualified_instructor_ids=qualified_instructors,
                preferred_slots=preferred_slots,
                room_consistency_required=bool(
                    data.get("room_consistency_required", False)
                ),
            )

            return course

        except Exception as e:
            self.logger.error(f"Error creating course from data {data}: {str(e)}")
            return None

    def _create_instructor_from_data(
        self, data: Dict[str, Any]
    ) -> Optional[Instructor]:
        """Create Instructor object from data dictionary."""
        try:
            # Parse qualified courses
            qualified_courses = self._parse_list_field(
                data.get("qualified_courses", "")
            )

            # Parse available slots
            available_slots = self._parse_time_slots(data.get("available_slots", ""))

            # Parse preferred slots (optional)
            preferred_slots = None
            if "preferred_slots" in data and data["preferred_slots"]:
                preferred_slots = self._parse_time_slots(data["preferred_slots"])

            instructor = Instructor(
                instructor_id=str(data["instructor_id"]),
                name=str(data["name"]),
                qualified_courses=qualified_courses,
                available_slots=available_slots,
                preferred_slots=preferred_slots,
                max_hours_per_day=int(data.get("max_hours_per_day", 8)),
                max_hours_per_week=int(data.get("max_hours_per_week", 40)),
                is_full_time=bool(data.get("is_full_time", True)),
                department=str(data.get("department", "General")),
            )

            return instructor

        except Exception as e:
            self.logger.error(f"Error creating instructor from data {data}: {str(e)}")
            return None

    def _create_room_from_data(self, data: Dict[str, Any]) -> Optional[Room]:
        """Create Room object from data dictionary."""
        try:
            # Parse available slots
            available_slots = self._parse_time_slots(data.get("available_slots", ""))

            # Parse equipment list
            equipment = []
            if "equipment" in data and data["equipment"]:
                equipment = self._parse_list_field(data["equipment"])

            room = Room(
                room_id=str(data["room_id"]),
                name=str(data["name"]),
                capacity=int(data["capacity"]),
                room_type=str(
                    data["type"]
                ),  # Map 'type' from CSV to 'room_type' parameter
                available_slots=available_slots,
                equipment=equipment,
                building=str(data.get("building", "Main Building")),
                floor=int(data.get("floor", 1)),
                is_accessible=bool(data.get("is_accessible", True)),
            )

            return room

        except Exception as e:
            self.logger.error(f"Error creating room from data {data}: {str(e)}")
            return None

    def _create_group_from_data(self, data: Dict[str, Any]) -> Optional[Group]:
        """Create Group object from data dictionary."""
        try:
            # Parse enrolled courses
            enrolled_courses = self._parse_list_field(data.get("enrolled_courses", ""))

            group = Group(
                group_id=str(data["group_id"]),
                name=str(data["name"]),
                student_count=int(data["student_count"]),
                enrolled_courses=enrolled_courses,
                year_level=int(data.get("year_level", 1)),
                program=str(data.get("program", "General")),
                max_daily_hours=int(data.get("max_daily_hours", 8)),
            )

            return group

        except Exception as e:
            self.logger.error(f"Error creating group from data {data}: {str(e)}")
            return None

    def _parse_list_field(self, field_value: Any) -> List[str]:
        """Parse a field that should be a list."""
        import pandas as pd

        # Handle pandas NaN values
        if pd.isna(field_value):
            return []

        if isinstance(field_value, list):
            return [str(item) for item in field_value if not pd.isna(item)]
        elif isinstance(field_value, str):
            if field_value.strip():
                # Handle comma-separated values
                return [item.strip() for item in field_value.split(",") if item.strip()]
            else:
                return []
        else:
            return []

    def _parse_time_slots(self, slots_data: Any) -> Dict[str, List[str]]:
        """Parse time slots data into dictionary format."""
        if isinstance(slots_data, dict):
            return slots_data
        elif isinstance(slots_data, str):
            # Parse format like "mon_09:00-17:00,tue_09:00-17:00"
            slots = {}
            if slots_data.strip():
                for slot_range in slots_data.split(","):
                    slot_range = slot_range.strip()
                    if "_" in slot_range:
                        day, time_range = slot_range.split("_", 1)
                        day = day.strip().lower()
                        if day not in slots:
                            slots[day] = []
                        slots[day].append(time_range.strip())
            return slots
        else:
            return {}

    def _validate_data_integrity(self) -> bool:
        """Validate cross-references between entities."""
        try:
            self.logger.info("Validating data integrity...")

            courses_to_remove = []

            # Check course-instructor qualifications
            for course_id, course in self.courses.items():
                valid_instructors = []
                for instructor_id in course.qualified_instructor_ids:
                    if instructor_id not in self.instructors:
                        self.logger.warning(
                            f"Course {course_id} references unknown instructor {instructor_id}, removing reference"
                        )
                    else:
                        valid_instructors.append(instructor_id)
                        if (
                            course_id
                            not in self.instructors[instructor_id].qualified_courses
                        ):
                            self.logger.warning(
                                f"Instructor {instructor_id} not qualified for course {course_id} "
                                f"according to instructor data"
                            )

                # Update the course with valid instructors only
                course.qualified_instructor_ids = valid_instructors

                # Mark course for removal if no valid instructors remain
                if not valid_instructors:
                    self.logger.warning(
                        f"Course {course_id} has no valid instructors, removing course"
                    )
                    courses_to_remove.append(course_id)

            # Check course-group enrollments
            for course_id, course in self.courses.items():
                if course_id in courses_to_remove:
                    continue

                valid_groups = []
                for group_id in course.group_ids:
                    if group_id not in self.groups:
                        self.logger.warning(
                            f"Course {course_id} references unknown group {group_id}, removing reference"
                        )
                    else:
                        valid_groups.append(group_id)
                        if course_id not in self.groups[group_id].enrolled_courses:
                            self.logger.warning(
                                f"Group {group_id} not enrolled in course {course_id} "
                                f"according to group data"
                            )

                # Update the course with valid groups only
                course.group_ids = valid_groups

                # Mark course for removal if no valid groups remain
                if not valid_groups:
                    self.logger.warning(
                        f"Course {course_id} has no valid groups, removing course"
                    )
                    courses_to_remove.append(course_id)

            # Remove invalid courses
            for course_id in courses_to_remove:
                if course_id in self.courses:
                    del self.courses[course_id]
                    self.logger.info(f"Removed invalid course: {course_id}")

            if courses_to_remove:
                self.logger.info(
                    f"Data integrity validation completed with {len(courses_to_remove)} courses removed"
                )
            else:
                self.logger.info("Data integrity validation completed successfully")

            return True

        except Exception as e:
            self.logger.error(f"Error during data integrity validation: {str(e)}")
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of loaded data."""
        return {
            "courses_count": len(self.courses),
            "instructors_count": len(self.instructors),
            "rooms_count": len(self.rooms),
            "groups_count": len(self.groups),
            "total_sessions_per_week": sum(
                course.sessions_per_week for course in self.courses.values()
            ),
            "total_students": sum(
                group.student_count for group in self.groups.values()
            ),
        }
