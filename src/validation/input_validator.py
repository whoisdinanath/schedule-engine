"""
Input Validation Module

Validates loaded data for consistency before GA execution.
Fails fast with clear error messages to prevent cryptic runtime failures.
"""

from typing import List, Dict
from src.entities.course import Course
from src.entities.group import Group
from src.entities.instructor import Instructor
from src.entities.room import Room
from src.core.types import SchedulingContext


class ValidationError:
    """Represents a single validation error."""

    def __init__(self, category: str, message: str, severity: str = "ERROR"):
        """
        Args:
            category: Error category (e.g., "COURSE", "GROUP", "INSTRUCTOR")
            message: Detailed error message
            severity: "ERROR", "WARNING", or "INFO"
        """
        self.category = category
        self.message = message
        self.severity = severity

    def __str__(self):
        return f"[{self.severity}] {self.category}: {self.message}"

    def __repr__(self):
        return self.__str__()


class InputValidator:
    """
    Validates scheduling input data for consistency and completeness.

    Checks:
    - Required relationships exist
    - No orphaned entities
    - Data types are correct
    - Reasonable constraints (e.g., room capacity > 0)
    """

    def __init__(self, context: SchedulingContext):
        """
        Initialize validator with scheduling context.

        Args:
            context: SchedulingContext to validate
        """
        self.context = context
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []

    def validate(self) -> List[ValidationError]:
        """
        Run all validation checks.

        Returns:
            List of validation errors (empty if valid)
        """
        self.errors = []
        self.warnings = []

        # Run all validation checks
        self._validate_courses()
        self._validate_groups()
        self._validate_instructors()
        self._validate_rooms()
        self._validate_relationships()
        self._validate_availability()

        return self.errors + self.warnings

    def _validate_courses(self):
        """Validate course data."""
        if not self.context.courses:
            self.errors.append(
                ValidationError(
                    "COURSE", "No courses loaded! Cannot generate schedule."
                )
            )
            return

        for course_id, course in self.context.courses.items():
            # Check required fields
            if not course.name:
                self.warnings.append(
                    ValidationError(
                        "COURSE", f"Course {course_id} has no name", "WARNING"
                    )
                )

            if course.quanta_per_week <= 0:
                self.errors.append(
                    ValidationError(
                        "COURSE",
                        f"Course {course_id} has invalid quanta_per_week: {course.quanta_per_week}",
                    )
                )

            # Check for qualified instructors
            if not course.qualified_instructor_ids:
                self.warnings.append(
                    ValidationError(
                        "COURSE",
                        f"Course {course_id} has no qualified instructors",
                        "WARNING",
                    )
                )

            # Check for practical courses
            if course.course_type == "practical" and not course.required_room_features:
                self.warnings.append(
                    ValidationError(
                        "COURSE",
                        f"Practical course {course_id} has no required room features",
                        "WARNING",
                    )
                )

    def _validate_groups(self):
        """Validate group data."""
        if not self.context.groups:
            self.errors.append(
                ValidationError("GROUP", "No groups loaded! Cannot generate schedule.")
            )
            return

        for group_id, group in self.context.groups.items():
            # Check enrolled courses
            if not group.enrolled_courses:
                self.warnings.append(
                    ValidationError(
                        "GROUP", f"Group {group_id} has no enrolled courses", "WARNING"
                    )
                )

            # Check size
            if group.student_count <= 0:
                self.warnings.append(
                    ValidationError(
                        "GROUP",
                        f"Group {group_id} has invalid student_count: {group.student_count}",
                        "WARNING",
                    )
                )

    def _validate_instructors(self):
        """Validate instructor data."""
        if not self.context.instructors:
            self.errors.append(
                ValidationError(
                    "INSTRUCTOR", "No instructors loaded! Cannot generate schedule."
                )
            )
            return

        for instructor_id, instructor in self.context.instructors.items():
            # Check qualified courses from ORIGINAL JSON data
            # Use original_qualified_courses if available to avoid false warnings
            # when courses are filtered out during enrollment filtering
            original_courses = getattr(instructor, "original_qualified_courses", None)

            if original_courses is None:
                # Fallback to current qualified_courses if original not stored
                original_courses = instructor.qualified_courses

            # Only warn if instructor has NO qualifications in the original JSON
            if not original_courses:
                self.warnings.append(
                    ValidationError(
                        "INSTRUCTOR",
                        f"Instructor {instructor_id} has no qualified courses in JSON data",
                        "WARNING",
                    )
                )
            # Informational: instructor has qualifications but none match enrolled courses
            elif not instructor.qualified_courses:
                # Silently skip - this is expected when instructor qualifications
                # don't match any enrolled courses. Not a data error.
                pass

            # Check availability for part-time instructors
            if not instructor.is_full_time and not instructor.available_quanta:
                self.warnings.append(
                    ValidationError(
                        "INSTRUCTOR",
                        f"Part-time instructor {instructor_id} has no availability defined",
                        "WARNING",
                    )
                )

    def _validate_rooms(self):
        """Validate room data."""
        if not self.context.rooms:
            self.errors.append(
                ValidationError("ROOM", "No rooms loaded! Cannot generate schedule.")
            )
            return

        for room_id, room in self.context.rooms.items():
            # Check capacity
            if room.capacity <= 0:
                self.errors.append(
                    ValidationError(
                        "ROOM", f"Room {room_id} has invalid capacity: {room.capacity}"
                    )
                )

    def _validate_relationships(self):
        """Validate relationships between entities."""
        # Check course-instructor relationships
        for course_id, course in self.context.courses.items():
            for instructor_id in course.qualified_instructor_ids:
                if instructor_id not in self.context.instructors:
                    self.errors.append(
                        ValidationError(
                            "RELATIONSHIP",
                            f"Course {course_id} references non-existent instructor {instructor_id}",
                        )
                    )
                else:
                    # Check reverse relationship
                    instructor = self.context.instructors[instructor_id]
                    if course_id not in instructor.qualified_courses:
                        self.warnings.append(
                            ValidationError(
                                "RELATIONSHIP",
                                f"Asymmetric relationship: Course {course_id} lists instructor {instructor_id}, "
                                f"but instructor doesn't list course",
                                "WARNING",
                            )
                        )

        # Check group-course relationships
        # Note: Groups reference course CODES, but context.courses uses course IDs
        # For pure practical courses, the ID becomes "CODE-PR"
        for group_id, group in self.context.groups.items():
            for course_code in group.enrolled_courses:
                # Try to find course by course_code attribute
                matching_courses = [
                    c
                    for c in self.context.courses.values()
                    if hasattr(c, "course_code") and c.course_code == course_code
                ]

                # Also check if course_code matches course_id directly
                if course_code in self.context.courses:
                    matching_courses.append(self.context.courses[course_code])

                if not matching_courses:
                    # This is a WARNING, not an ERROR - courses with L=T=P=0 don't need scheduling
                    self.warnings.append(
                        ValidationError(
                            "RELATIONSHIP",
                            f"Group {group_id} enrolled in course {course_code} which doesn't exist "
                            f"(likely has L=T=P=0 in Course.json and doesn't need scheduling)",
                            "WARNING",
                        )
                    )

        # Check for orphaned courses (no groups enrolled)
        enrolled_courses = set()
        for group in self.context.groups.values():
            enrolled_courses.update(group.enrolled_courses)

        for course_id in self.context.courses.keys():
            if course_id not in enrolled_courses:
                self.warnings.append(
                    ValidationError(
                        "RELATIONSHIP",
                        f"Course {course_id} has no groups enrolled",
                        "WARNING",
                    )
                )

    def _validate_availability(self):
        """Validate availability constraints."""
        if not self.context.available_quanta:
            self.errors.append(
                ValidationError("AVAILABILITY", "No available time quanta defined!")
            )
            return

        # Check for sufficient time slots
        total_quanta_needed = 0
        for course_id, course in self.context.courses.items():
            # Count how many groups are enrolled
            groups_enrolled = sum(
                1
                for group in self.context.groups.values()
                if course_id in group.enrolled_courses
            )
            total_quanta_needed += course.quanta_per_week * groups_enrolled

        available_slots = len(self.context.available_quanta)

        if total_quanta_needed > available_slots:
            self.warnings.append(
                ValidationError(
                    "AVAILABILITY",
                    f"Tight schedule: Need {total_quanta_needed} quanta but only {available_slots} available. "
                    f"May result in conflicts.",
                    "WARNING",
                )
            )
        elif total_quanta_needed > available_slots * 0.8:
            self.warnings.append(
                ValidationError(
                    "AVAILABILITY",
                    f"Schedule is 80%+ full ({total_quanta_needed}/{available_slots} quanta). "
                    f"Limited flexibility for optimization.",
                    "INFO",
                )
            )

    def has_errors(self) -> bool:
        """Check if validation found any errors."""
        return len(self.errors) > 0

    def has_warnings(self) -> bool:
        """Check if validation found any warnings."""
        return len(self.warnings) > 0

    def print_report(self):
        """Print validation report to console."""
        all_issues = self.errors + self.warnings

        if not all_issues:
            print("[OK] Validation passed! No issues found.")
            return

        print("\n" + "=" * 60)
        print("VALIDATION REPORT")
        print("=" * 60)

        if self.errors:
            print(f"\n[ERROR] Found {len(self.errors)} ERRORS:")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n[WARNING] Found {len(self.warnings)} WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")

        print("\n" + "=" * 60)

        if self.errors:
            print("[X] Validation FAILED! Fix errors before running GA.")
        else:
            print("[OK] Validation passed with warnings. Review before running GA.")


def validate_input(context: SchedulingContext, strict: bool = False) -> bool:
    """
    Validate input data and print report.

    Args:
        context: SchedulingContext to validate
        strict: If True, treat warnings as errors

    Returns:
        True if validation passed (or only warnings in non-strict mode)

    Raises:
        ValueError: If validation fails in strict mode
    """
    validator = InputValidator(context)
    issues = validator.validate()

    validator.print_report()

    if validator.has_errors():
        if strict:
            raise ValueError("Input validation failed! See errors above.")
        return False

    if strict and validator.has_warnings():
        raise ValueError("Strict validation failed! Warnings present.")

    return True
