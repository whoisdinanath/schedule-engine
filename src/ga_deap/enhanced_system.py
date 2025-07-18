"""
Enhanced GA System with Visualization Integration

This module provides a streamlined interface for running genetic algorithm-based
timetabling optimization with integrated visualization capabilities. It combines
the best features of the existing system with new interactive elements.
"""

import logging
import time
from typing import Dict, List, Tuple, Any, Optional, Callable
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

from deap import base, creator, tools, algorithms
import random

from src.encoders.quantum_time_system import QuantumTimeSystem
from src.encoders.input_encoder import (
    load_courses,
    load_instructors,
    load_groups,
    load_rooms,
    link_courses_and_instructors,
)
from src.entities import Course, Instructor, Group, Room
from src.ga_deap.individual import generate_individual
from src.ga_deap.operators import custom_crossover, custom_mutation
from src.ga_deap.runner import evaluate_fitness


class EnhancedTimetablingSystem:
    """
    Enhanced timetabling system with integrated visualization and interactive capabilities.
    """

    def __init__(self, data_path: str = "data", log_level: int = logging.INFO):
        """
        Initialize the enhanced timetabling system.

        Args:
            data_path: Directory containing JSON data files
            log_level: Logging level
        """
        self.data_path = Path(data_path)
        self.qts = QuantumTimeSystem()

        # Data containers
        self.courses: Dict[str, Course] = {}
        self.instructors: Dict[str, Instructor] = {}
        self.groups: Dict[str, Group] = {}
        self.rooms: Dict[str, Room] = {}

        # Results tracking
        self.best_solution = None
        self.evolution_stats: List[Dict[str, Any]] = []
        self.generation_callback: Optional[Callable] = None

        # Setup logging
        logging.basicConfig(level=log_level)
        self.logger = logging.getLogger(__name__)

    def load_data(self) -> Tuple[bool, List[str]]:
        """
        Load all data files and perform validation.

        Returns:
            Tuple of (success_flag, list_of_issues)
        """
        issues = []

        try:
            # Load enhanced data files for better parallel scheduling
            self.courses = load_courses(str(self.data_path / "Courses_Enhanced.json"))
            self.instructors = load_instructors(
                str(self.data_path / "Instructors_Enhanced.json"), self.qts
            )
            self.groups = load_groups(
                str(self.data_path / "Groups_Enhanced.json"), self.qts
            )
            self.rooms = load_rooms(
                str(self.data_path / "Rooms_Enhanced.json"), self.qts
            )

            # Link courses and instructors
            link_courses_and_instructors(self.courses, self.instructors)

            # Validate data
            validation_issues = self._validate_data()
            issues.extend(validation_issues)

            self.logger.info(
                f"Loaded {len(self.courses)} courses, {len(self.instructors)} instructors, "
                f"{len(self.groups)} groups, {len(self.rooms)} rooms"
            )

            return True, issues

        except Exception as e:
            self.logger.error(f"Error loading data: {e}")
            return False, [str(e)]

    def _validate_data(self) -> List[str]:
        """Validate loaded data and return list of issues."""
        issues = []

        # Check courses
        for course_id, course in self.courses.items():
            if not course.qualified_instructor_ids:
                issues.append(f"Course {course_id} has no qualified instructors")
            if not course.enrolled_group_ids:
                issues.append(f"Course {course_id} has no enrolled groups")

        # Check instructors
        for instructor_id, instructor in self.instructors.items():
            if not instructor.qualified_courses:
                issues.append(f"Instructor {instructor_id} has no qualified courses")

        return issues

    def run_optimization(
        self,
        generations: int = 50,
        population_size: int = 100,
        crossover_rate: float = 0.8,
        mutation_rate: float = 0.1,
        tournament_size: int = 3,
        progress_callback: Optional[Callable] = None,
        update_interval: int = 5,
    ) -> Any:
        """
        Run genetic algorithm optimization with optional progress tracking.

        Args:
            generations: Number of generations to evolve
            population_size: Size of the population
            crossover_rate: Probability of crossover
            mutation_rate: Probability of mutation
            tournament_size: Tournament selection size
            progress_callback: Optional callback for progress updates
            update_interval: How often to call progress callback

        Returns:
            Best individual found
        """
        if not all([self.courses, self.instructors, self.groups, self.rooms]):
            raise ValueError("Data not loaded. Call load_data() first.")

        self.generation_callback = progress_callback

        # Setup DEAP
        if hasattr(creator, "FitnessMax"):
            del creator.FitnessMax
        if hasattr(creator, "Individual"):
            del creator.Individual

        creator.create("FitnessMax", base.Fitness, weights=(1.0,))
        creator.create("Individual", list, fitness=creator.FitnessMax)

        toolbox = base.Toolbox()
        toolbox.register(
            "individual",
            lambda: creator.Individual(
                generate_individual(
                    self.qts, self.courses, self.instructors, self.groups, self.rooms
                )
            ),
        )
        toolbox.register("population", tools.initRepeat, list, toolbox.individual)
        toolbox.register(
            "evaluate",
            lambda ind: evaluate_fitness(
                ind, self.qts, self.courses, self.instructors, self.groups, self.rooms
            ),
        )
        toolbox.register("mate", custom_crossover)
        toolbox.register(
            "mutate",
            lambda ind: custom_mutation(
                ind,
                self.qts,
                self.courses,
                self.instructors,
                self.groups,
                self.rooms,
                mutation_rate,
            ),
        )
        toolbox.register("select", tools.selTournament, tournsize=tournament_size)

        # Initialize population
        self.logger.info(f"Initializing population of {population_size} individuals...")
        population = toolbox.population(n=population_size)

        # Evaluate initial population
        self.logger.info("Evaluating initial population...")
        for individual in population:
            individual.fitness.values = toolbox.evaluate(individual)

        # Statistics tracking
        stats = tools.Statistics(lambda ind: ind.fitness.values)
        stats.register("avg", lambda x: sum(f[0] for f in x) / len(x) if x else 0)
        stats.register("min", lambda x: min(f[0] for f in x) if x else 0)
        stats.register("max", lambda x: max(f[0] for f in x) if x else 0)
        stats.register("std", lambda x: np.std([f[0] for f in x]) if x else 0)

        # Reset evolution stats
        self.evolution_stats = []

        self.logger.info(f"Starting evolution for {generations} generations...")
        start_time = time.time()

        # Custom evolution loop for progress tracking
        for gen in range(generations):
            # Select and breed next generation
            offspring = toolbox.select(population, len(population))
            offspring = list(map(toolbox.clone, offspring))

            # Apply crossover
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < crossover_rate:
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            # Apply mutation
            for mutant in offspring:
                if random.random() < mutation_rate:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate invalid individuals
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            # Replace population
            population[:] = offspring

            # Record statistics
            record = stats.compile(population)
            self.evolution_stats.append(
                {
                    "generation": gen,
                    "best": record["max"],
                    "average": record["avg"],
                    "worst": record["min"],
                    "std": record["std"],
                    "time": time.time() - start_time,
                }
            )

            # Progress callback
            if progress_callback and gen % update_interval == 0:
                progress_callback(gen, record, self.evolution_stats)

            # Log progress
            if gen % 10 == 0:
                self.logger.info(
                    f"Generation {gen}: Best={record['max']:.4f}, Avg={record['avg']:.4f}"
                )

        # Final results
        best_individual = tools.selBest(population, 1)[0]
        self.best_solution = best_individual

        elapsed_time = time.time() - start_time
        self.logger.info(f"Evolution completed in {elapsed_time:.2f} seconds")
        self.logger.info(f"Best fitness: {best_individual.fitness.values[0]:.4f}")

        return best_individual

    def get_solution_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of the current solution."""
        if not self.best_solution:
            return {"error": "No solution available"}

        solution = self.best_solution

        # Basic statistics
        total_sessions = len(solution)
        unique_slots = set()
        room_usage = {}
        instructor_usage = {}
        course_coverage = set()

        for session in solution:
            course_coverage.add(session.course_id)
            for q in session.quanta:
                unique_slots.add(q)
                room_usage[session.room_id] = room_usage.get(session.room_id, 0) + 1
                instructor_usage[session.instructor_id] = (
                    instructor_usage.get(session.instructor_id, 0) + 1
                )

        # Evolution statistics
        if self.evolution_stats:
            final_stats = self.evolution_stats[-1]
            initial_best = self.evolution_stats[0]["best"]
            improvement = final_stats["best"] - initial_best
        else:
            final_stats = {}
            improvement = 0

        summary = {
            "total_sessions": total_sessions,
            "unique_time_slots": len(unique_slots),
            "rooms_used": len(room_usage),
            "instructors_used": len(instructor_usage),
            "courses_covered": len(course_coverage),
            "fitness_score": (
                solution.fitness.values[0] if hasattr(solution, "fitness") else 0
            ),
            "total_improvement": improvement,
            "generations_run": len(self.evolution_stats),
            "room_usage": room_usage,
            "instructor_usage": instructor_usage,
            "evolution_time": final_stats.get("time", 0),
        }

        return summary

    def export_schedule(
        self, filename: Optional[str] = None, format_type: str = "excel"
    ) -> str:
        """
        Export the current schedule to file.

        Args:
            filename: Output filename (auto-generated if None)
            format_type: Export format ('excel', 'csv', 'json')

        Returns:
            Path to exported file
        """
        if not self.best_solution:
            raise ValueError("No solution available to export")

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"timetable_{timestamp}.{format_type}"

        # Convert solution to structured data
        schedule_data = []

        for i, session in enumerate(self.best_solution):
            course = self.courses[session.course_id]
            instructor = self.instructors[session.instructor_id]
            group = self.groups[session.group_id]
            room = self.rooms[session.room_id]

            for q in session.quanta:
                day, time = self.qts.quanta_to_time(q)

                schedule_data.append(
                    {
                        "Session_ID": f"S{i+1:03d}",
                        "Day": day,
                        "Time": time,
                        "Course_ID": course.course_id,
                        "Course_Name": course.name,
                        "Instructor_ID": instructor.instructor_id,
                        "Instructor_Name": instructor.name,
                        "Group_ID": group.group_id,
                        "Group_Name": group.name,
                        "Room_ID": room.room_id,
                        "Room_Name": room.name,
                        "Room_Capacity": room.capacity,
                    }
                )

        # Export based on format
        if format_type == "excel":
            import pandas as pd

            df = pd.DataFrame(schedule_data)
            df.to_excel(filename, index=False)
        elif format_type == "csv":
            import pandas as pd

            df = pd.DataFrame(schedule_data)
            df.to_csv(filename, index=False)
        elif format_type == "readable":
            return self._format_readable_schedule()
        elif format_type == "json":
            import json

            with open(filename, "w") as f:
                json.dump(schedule_data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format_type}")

        self.logger.info(f"Schedule exported to: {filename}")
        return filename

    def _format_readable_schedule(self) -> str:
        """Format the schedule in a human-readable text format."""
        if not self.best_solution:
            return "No solution available"

        schedule_text = "=== COMPREHENSIVE TIMETABLE SCHEDULE ===\n\n"

        for i, session in enumerate(self.best_solution):
            course = self.courses[session.course_id]
            instructor = self.instructors[session.instructor_id]
            group = self.groups[session.group_id]
            room = self.rooms[session.room_id]

            schedule_text += f"Session {i+1:03d}:\n"
            schedule_text += f"  Course: {course.name} ({course.course_id})\n"
            schedule_text += (
                f"  Instructor: {instructor.name} ({instructor.instructor_id})\n"
            )
            schedule_text += f"  Group: {group.name} ({group.group_id})\n"
            schedule_text += f"  Room: {room.name} ({room.room_id})\n"
            schedule_text += f"  Time Slots:\n"

            for q in session.quanta:
                day, time = self.qts.quanta_to_time(q)
                schedule_text += f"    - {day} at {time}\n"

            schedule_text += "\n"

        return schedule_text

    def create_visualization_data(self) -> Dict[str, Any]:
        """
        Create a data structure compatible with visualization functions.

        Returns:
            Dictionary containing formatted data for visualization
        """
        if not self.best_solution:
            return {}

        # Convert evolution stats to visualization format
        viz_evolution_stats = []
        for i, stats in enumerate(self.evolution_stats):
            viz_evolution_stats.append(
                {
                    "generation": i,
                    "best": stats.get("best", 0),
                    "average": stats.get("avg", 0),
                    "worst": stats.get("min", 0),  # min fitness is worst
                }
            )

        return {
            "fitness_history": viz_evolution_stats,
            "solution": self.best_solution,
            "courses": self.courses,
            "instructors": self.instructors,
            "rooms": self.rooms,
            "groups": self.groups,
        }

    def show_fitness_evolution(self) -> None:
        """Display fitness evolution chart using the visualizer."""
        try:
            from src.visualization.charts import EvolutionVisualizer

            visualizer = EvolutionVisualizer()

            viz_data = self.create_visualization_data()
            if viz_data.get("fitness_history"):
                visualizer.plot_fitness_evolution(
                    viz_data["fitness_history"], show_plot=True
                )
            else:
                print("No evolution data available for visualization.")
        except ImportError:
            print("Visualization module not available.")

    def show_schedule_heatmap(self, view_type: str = "room") -> None:
        """Display schedule heatmap using the visualizer."""
        try:
            from src.visualization.charts import EvolutionVisualizer

            visualizer = EvolutionVisualizer()

            if self.best_solution:
                visualizer.plot_schedule_heatmap(
                    self.best_solution,
                    self.courses,
                    self.instructors,
                    self.rooms,
                    self.groups,
                    view_type=view_type,
                    show_plot=True,
                )
            else:
                print("No solution available for heatmap.")
        except ImportError:
            print("Visualization module not available.")

    def show_workload_distribution(self) -> None:
        """Display workload distribution using the visualizer."""
        try:
            from src.visualization.charts import EvolutionVisualizer

            visualizer = EvolutionVisualizer()

            if self.best_solution:
                visualizer.plot_workload_distribution(
                    self.best_solution, self.instructors, self.courses, show_plot=True
                )
            else:
                print("No solution available for workload analysis.")
        except ImportError:
            print("Visualization module not available.")
