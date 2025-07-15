"""
Main Timetabling System using DEAP-based Genetic Algorithm
"""

from typing import Dict, List, Tuple, Any
from encoders.quantum_time_system import QuantumTimeSystem
from encoders.input_encoder import (
    load_courses,
    load_instructors,
    load_groups,
    load_rooms,
    link_courses_and_instructors,
)
from entities import Course, Instructor, Group, Room
from .runner import run_ga
from .population import register_individual_classes
import logging


class TimetablingSystem:
    """
    Main system that coordinates entities, input encoding, and GA optimization
    """

    def __init__(self, data_path: str = "data"):
        """Initialize the timetabling system with data loading"""
        self.data_path = data_path
        self.qts = QuantumTimeSystem()
        self.courses = {}
        self.instructors = {}
        self.groups = {}
        self.rooms = {}
        self.best_solution = None

        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def load_data(self):
        """Load all data from JSON files"""
        try:
            self.logger.info("Loading data files...")
            self.courses = load_courses(f"{self.data_path}/Courses.json")
            self.instructors = load_instructors(
                f"{self.data_path}/Instructors.json", self.qts
            )
            self.groups = load_groups(f"{self.data_path}/Groups.json", self.qts)
            self.rooms = load_rooms(f"{self.data_path}/Rooms.json", self.qts)

            # Link courses and instructors
            link_courses_and_instructors(self.courses, self.instructors)

            self.logger.info(
                f"Loaded {len(self.courses)} courses, {len(self.instructors)} instructors, "
                f"{len(self.groups)} groups, {len(self.rooms)} rooms"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return False

    def validate_data(self):
        """Validate that all data is consistent and complete"""
        issues = []

        # Check if courses have qualified instructors
        for course_id, course in self.courses.items():
            if not course.qualified_instructor_ids:
                issues.append(f"Course {course_id} has no qualified instructors")

        # Check if instructors have valid courses
        for instructor_id, instructor in self.instructors.items():
            if not instructor.qualified_courses:
                issues.append(f"Instructor {instructor_id} has no qualified courses")

        if issues:
            self.logger.warning(f"Data validation issues: {issues}")
        else:
            self.logger.info("Data validation passed")

        return len(issues) == 0, issues

    def run_optimization(self, generations: int = 50, population_size: int = 100):
        """Run the genetic algorithm optimization"""
        if not all([self.courses, self.instructors, self.groups, self.rooms]):
            raise ValueError("Data not loaded. Call load_data() first.")

        self.logger.info(
            f"Starting GA optimization with {generations} generations, population size {population_size}"
        )

        # Run the GA
        self.best_solution = run_ga(
            qts=self.qts,
            courses=self.courses,
            instructors=self.instructors,
            groups=self.groups,
            rooms=self.rooms,
            ngen=generations,
            pop_size=population_size,
        )

        self.logger.info("GA optimization completed")
        return self.best_solution

    def get_solution_summary(self):
        """Get a summary of the best solution found"""
        if not self.best_solution:
            return "No solution available. Run optimization first."

        summary = {
            "total_sessions": len(self.best_solution),
            "unique_time_slots": len(set(session[0] for session in self.best_solution)),
            "rooms_used": len(set(session[1] for session in self.best_solution)),
            "instructors_used": len(set(session[2] for session in self.best_solution)),
            "fitness_score": (
                self.best_solution.fitness.values[0]
                if hasattr(self.best_solution, "fitness")
                else "N/A"
            ),
        }

        return summary

    def export_schedule(self, format: str = "readable"):
        """Export the schedule in different formats"""
        if not self.best_solution:
            return "No solution to export. Run optimization first."

        if format == "readable":
            return self._format_readable_schedule()
        elif format == "json":
            return self._format_json_schedule()
        else:
            return "Unsupported format"

    def _format_readable_schedule(self):
        """Format schedule in human-readable format"""
        if not self.best_solution:
            return "No schedule available"

        schedule_text = "=== TIMETABLE SCHEDULE ===\n"

        for i, (time_slot, room_id, instructor_id) in enumerate(self.best_solution):
            day, time = self.qts.quanta_to_time(time_slot)
            schedule_text += f"Session {i+1}: {day} {time}, Room {room_id}, Instructor {instructor_id}\n"

        return schedule_text

    def _format_json_schedule(self):
        """Format schedule as JSON-serializable dict"""
        if not self.best_solution:
            return {}

        schedule = []
        for i, (time_slot, room_id, instructor_id) in enumerate(self.best_solution):
            day, time = self.qts.quanta_to_time(time_slot)
            schedule.append(
                {
                    "session_id": i,
                    "time_slot": time_slot,
                    "day": day,
                    "time": time,
                    "room_id": room_id,
                    "instructor_id": instructor_id,
                }
            )

        return schedule
