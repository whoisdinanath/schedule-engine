"""
Main Timetabling System using DEAP-based Genetic Algorithm.

This module provides a class-based interface for loading university scheduling data,
validating it, running a genetic algorithm to generate a conflict-free timetable,
and exporting the result in various formats.

It integrates time encoding (QuantumTimeSystem), input preprocessing,
and DEAP-based optimization for the University Course Timetabling Problem (UCTP).
"""

import logging
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


class TimetablingSystem:
    """
    Main coordinator for the DEAP-based university timetabling optimization system.

    This class encapsulates data loading, preprocessing, validation, 
    and optimization via genetic algorithms. It also provides output formatting utilities.
    """

    def __init__(self, data_path: str = "data"):
        """
        Initialize the TimetablingSystem with a default or user-defined data directory.

        Args:
            data_path (str): Directory path where JSON input files are stored.
        """
        self.data_path = data_path
        self.qts = QuantumTimeSystem()
        self.courses: Dict[str, Course] = {}
        self.instructors: Dict[str, Instructor] = {}
        self.groups: Dict[str, Group] = {}
        self.rooms: Dict[str, Room] = {}
        self.best_solution = None

        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def load_data(self) -> bool:
        """
        Load all required input files and initialize internal entity dictionaries.

        Loads courses, instructors, student groups, and rooms from JSON files and 
        encodes availability into quantum time slots.

        Returns:
            bool: True if loading succeeds, False otherwise.
        """
        try:
            self.logger.info("Loading data files...")
            self.courses = load_courses(f"{self.data_path}/Courses.json")
            self.instructors = load_instructors(f"{self.data_path}/Instructors.json", self.qts)
            self.groups = load_groups(f"{self.data_path}/Groups.json", self.qts)
            self.rooms = load_rooms(f"{self.data_path}/Rooms.json", self.qts)

            link_courses_and_instructors(self.courses, self.instructors)

            self.logger.info(
                f"Loaded {len(self.courses)} courses, {len(self.instructors)} instructors, "
                f"{len(self.groups)} groups, {len(self.rooms)} rooms"
            )
            return True
        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return False

    def validate_data(self) -> Tuple[bool, List[str]]:
        """
        Perform sanity checks on the loaded data to catch incomplete or inconsistent entities.

        Returns:
            Tuple[bool, List[str]]: (True if valid, False otherwise, list of issues)
        """
        issues = []

        for course_id, course in self.courses.items():
            if not course.qualified_instructor_ids:
                issues.append(f"Course {course_id} has no qualified instructors")

        for instructor_id, instructor in self.instructors.items():
            if not instructor.qualified_courses:
                issues.append(f"Instructor {instructor_id} has no qualified courses")

        if issues:
            self.logger.warning(f"Data validation issues: {issues}")
        else:
            self.logger.info("Data validation passed")

        return len(issues) == 0, issues

    def run_optimization(self, generations: int = 50, population_size: int = 100) -> Any:
        """
        Run the DEAP-based genetic algorithm to generate a valid schedule.

        Args:
            generations (int): Number of generations for evolution.
            population_size (int): Size of the population for the GA.

        Returns:
            Any: The best individual (schedule) found by the GA.
        
        Raises:
            ValueError: If data has not been loaded before calling this method.
        """
        if not all([self.courses, self.instructors, self.groups, self.rooms]):
            raise ValueError("Data not loaded. Call load_data() first.")

        self.logger.info(
            f"Starting GA optimization with {generations} generations, population size {population_size}"
        )

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

    def get_solution_summary(self) -> Dict[str, Any]:
        """
        Generate a summary report of the best solution's statistics.

        Returns:
            Dict[str, Any]: Dictionary summarizing key statistics of the best solution.
        """
        if not self.best_solution:
            return {"error": "No solution available. Run optimization first."}

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

    def export_schedule(self, format: str = "readable") -> Any:
        """
        Export the current schedule in a specified format.

        Args:
            format (str): Output format ("readable" or "json").

        Returns:
            Any: A formatted string or dict representing the schedule.

        Raises:
            ValueError: If an unsupported format is requested.
        """
        if not self.best_solution:
            return "No solution to export. Run optimization first."

        if format == "readable":
            return self._format_readable_schedule()
        elif format == "json":
            return self._format_json_schedule()
        else:
            raise ValueError("Unsupported format: choose 'readable' or 'json'.")

    def _format_readable_schedule(self) -> str:
        """
        Return a human-readable formatted string of the schedule.

        Returns:
            str: Schedule in plain text format.
        """
        schedule_text = "=== TIMETABLE SCHEDULE ===\n"

        for i, (time_slot, room_id, instructor_id) in enumerate(self.best_solution):
            day, time = self.qts.quanta_to_time(time_slot)
            schedule_text += f"Session {i+1}: {day} {time}, Room {room_id}, Instructor {instructor_id}\n"

        return schedule_text

    def _format_json_schedule(self) -> List[Dict[str, Any]]:
        """
        Return a JSON-serializable version of the schedule.

        Returns:
            List[Dict[str, Any]]: List of session dictionaries.
        """
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
