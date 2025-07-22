"""
Streamlined GA System with Enhanced Genetic Operators

This module provides a clean, efficient genetic algorithm system with enhanced
operators, population management, and fitness evaluation for timetabling optimization.
"""

import logging
import time
import os
import json
import csv
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
    generate_instructors_from_courses,
    generate_groups_from_courses,
    generate_rooms_from_courses,
)
from src.entities import Course, Instructor, Group, Room
from src.config.clean_config import CleanConfig, get_config
from .enhanced_operators import AdaptiveGeneticOperators, OperatorConfig
from .enhanced_fitness_evaluator import EnhancedFitnessEvaluator
from .enhanced_population import EnhancedPopulationManager, PopulationConfig


class StreamlinedTimetablingSystem:
    """
    Streamlined timetabling system with enhanced genetic operators and clean architecture.
    """

    def __init__(self, data_path: str = "data", config: CleanConfig = None):
        """
        Initialize the streamlined timetabling system.

        Args:
            data_path: Directory containing JSON data files
            config: Configuration object (uses default if None)
        """
        self.data_path = Path(data_path)
        self.config = config or get_config()
        self.qts = QuantumTimeSystem()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(getattr(logging, self.config.logging_config.level.upper()))

        # Data containers
        self.courses: Dict[str, Course] = {}
        self.instructors: Dict[str, Instructor] = {}
        self.groups: Dict[str, Group] = {}
        self.rooms: Dict[str, Room] = {}

        # Results tracking
        self.best_solution = None
        self.evolution_stats: List[Dict[str, Any]] = []
        self.optimization_history = []

    def load_data(self) -> Tuple[bool, List[str]]:
        """
        Load all data files and perform validation.
        Supports both Enhanced format and FullSyllabusAll format.

        Returns:
            Tuple of (success_flag, list_of_issues)
        """
        issues = []

        try:
            # Check if FullSyllabusAll.json exists
            fullsyllabus_path = self.data_path / "FullSyllabusAll.json"

            if fullsyllabus_path.exists():
                # Load FullSyllabusAll format
                self.logger.info("Loading FullSyllabusAll format...")

                # Load courses from FullSyllabusAll
                self.courses = load_courses(str(fullsyllabus_path))

                # Generate other entities automatically
                self.instructors = generate_instructors_from_courses(
                    self.courses, self.qts
                )
                self.groups = generate_groups_from_courses(self.courses, self.qts)
                self.rooms = generate_rooms_from_courses(self.courses, self.qts)

                self.logger.info(
                    "Auto-generated instructors, groups, and rooms from FullSyllabusAll"
                )

            else:
                # Load enhanced data files for better parallel scheduling
                self.courses = load_courses(
                    str(self.data_path / "Courses_Enhanced.json")
                )
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
        Run enhanced genetic algorithm optimization with advanced operators.

        Args:
            generations: Number of generations to evolve
            population_size: Size of the population
            crossover_rate: Probability of crossover
            mutation_rate: Probability of mutation
            tournament_size: Tournament selection size
            progress_callback: Optional callback for progress updates
            update_interval: How often to call progress callback

        Returns:
            Best individual found with detailed statistics
        """
        if not all([self.courses, self.instructors, self.groups, self.rooms]):
            raise ValueError("Data not loaded. Call load_data() first.")

        self.logger.info("Starting Enhanced Genetic Algorithm Optimization...")
        start_time = time.time()

        # Configure components
        operator_config = OperatorConfig(
            crossover_rate=crossover_rate,
            mutation_rate=mutation_rate,
            tournament_size=tournament_size,
            elite_size=max(1, population_size // 20),  # 5% elites
            adaptive_parameters=True,
        )

        population_config = PopulationConfig(
            population_size=population_size,
            elitism_rate=max(0.05, 1.0 / max(1, population_size // 20)),
            diversity_threshold=0.1,
            stagnation_limit=20,
            injection_rate=0.1,
        )

        # Initialize components
        self.genetic_operators = AdaptiveGeneticOperators(operator_config)
        self.fitness_evaluator = EnhancedFitnessEvaluator(enable_caching=True)
        self.population_manager = EnhancedPopulationManager(
            config=self.config,
            fitness_evaluator=self.fitness_evaluator,
            genetic_operators=self.genetic_operators,
        )

        # Initialize population
        self.logger.info(
            f"Initializing diverse population of {population_size} individuals..."
        )
        self.population_manager.initialize_population(
            self.qts,
            list(self.courses.values()),
            list(self.instructors.values()),
            list(self.groups.values()),
            list(self.rooms.values()),
        )

        # Population has already been evaluated during initialization
        initial_fitness = self.population_manager.fitness_scores
        self.logger.info(
            f"Initial population - Best: {max(initial_fitness):.2f}, "
            f"Average: {np.mean(initial_fitness):.2f}, "
            f"Worst: {min(initial_fitness):.2f}"
        )

        # Evolution loop
        self.logger.info(f"Starting evolution for {generations} generations...")

        for generation in range(generations):
            generation_start = time.time()

            # Evolve one generation
            generation_stats = self.population_manager.evolve_generation(
                self.qts,
                list(self.courses.values()),
                list(self.instructors.values()),
                list(self.groups.values()),
                list(self.rooms.values()),
            )

            # Track evolution statistics
            self.evolution_stats.append(generation_stats)

            # Log progress
            if generation % update_interval == 0 or generation == generations - 1:
                generation_time = time.time() - generation_start
                self.logger.info(
                    f"Generation {generation + 1}/{generations} - "
                    f"Best: {generation_stats['best_fitness']:.2f}, "
                    f"Avg: {generation_stats['avg_fitness']:.2f}, "
                    f"Diversity: {generation_stats['diversity']:.3f}, "
                    f"Stagnation: {generation_stats['stagnation_count']}, "
                    f"Time: {generation_time:.2f}s"
                )

            # Call progress callback if provided
            if progress_callback and generation % update_interval == 0:
                try:
                    progress_callback(
                        generation, generation_stats, self.evolution_stats
                    )
                except Exception as e:
                    self.logger.warning(f"Progress callback error: {e}")

            # Check for convergence
            if self.population_manager.check_convergence():
                self.logger.info(f"Convergence reached at generation {generation + 1}")
                break

            # Early stopping for perfect solution
            if generation_stats["best_fitness"] >= -1:  # Near-perfect solution
                self.logger.info(
                    f"Near-perfect solution found at generation {generation + 1}"
                )
                break

        # Get final results
        best_individual, best_fitness = self.population_manager.get_best_individual()
        self.best_solution = best_individual

        # Calculate total time
        total_time = time.time() - start_time

        # Log final statistics
        self.logger.info("=" * 60)
        self.logger.info("OPTIMIZATION COMPLETED")
        self.logger.info(f"Total generations: {len(self.evolution_stats)}")
        self.logger.info(f"Best fitness: {best_fitness:.2f}")
        self.logger.info(f"Total time: {total_time:.2f}s")
        self.logger.info(
            f"Average time per generation: {total_time/len(self.evolution_stats):.2f}s"
        )

        # Get component statistics
        cache_stats = self.fitness_evaluator.get_cache_statistics()
        operator_stats = self.genetic_operators.get_statistics()
        population_stats = self.population_manager.get_statistics()

        self.logger.info(f"Fitness evaluations: {cache_stats['evaluations']}")
        self.logger.info(f"Cache hit rate: {cache_stats['hit_rate']:.3f}")
        self.logger.info(
            f"Final mutation rate: {operator_stats['current_mutation_rate']:.3f}"
        )
        self.logger.info(
            f"Final tournament size: {operator_stats['current_tournament_size']}"
        )
        self.logger.info("=" * 60)

        # Store detailed results
        self.optimization_history.append(
            {
                "timestamp": datetime.now(),
                "generations": len(self.evolution_stats),
                "best_fitness": best_fitness,
                "total_time": total_time,
                "cache_stats": cache_stats,
                "operator_stats": operator_stats,
                "population_stats": population_stats,
                "evolution_stats": self.evolution_stats,
            }
        )

        return {
            "best_individual": best_individual,
            "best_fitness": best_fitness,
            "evolution_stats": self.evolution_stats,
            "total_time": total_time,
            "generations": len(self.evolution_stats),
            "cache_stats": cache_stats,
            "operator_stats": operator_stats,
            "population_stats": population_stats,
        }

    def analyze_solution(self, individual: List = None) -> Dict[str, Any]:
        """
        Analyze the best solution or provided individual.

        Args:
            individual: Individual to analyze (uses best if None)

        Returns:
            Detailed analysis of the solution
        """
        if individual is None:
            individual = self.best_solution

        if not individual:
            return {"error": "No solution available"}

        # Get detailed fitness breakdown
        fitness, breakdown = self.fitness_evaluator.evaluate_individual(
            individual,
            self.qts,
            self.courses,
            self.instructors,
            self.groups,
            self.rooms,
        )

        # Analyze resource utilization
        resource_analysis = self._analyze_resource_utilization(individual)

        # Analyze schedule patterns
        schedule_analysis = self._analyze_schedule_patterns(individual)

        # Analyze constraints
        constraint_analysis = self._analyze_constraints(individual)

        return {
            "fitness_score": fitness,
            "fitness_breakdown": breakdown,
            "resource_analysis": resource_analysis,
            "schedule_analysis": schedule_analysis,
            "constraint_analysis": constraint_analysis,
            "total_sessions": len(individual),
            "courses_scheduled": len(set(s.course_id for s in individual)),
            "instructors_used": len(set(s.instructor_id for s in individual)),
            "rooms_used": len(set(s.room_id for s in individual)),
            "groups_scheduled": len(set(s.group_id for s in individual)),
        }

    def _analyze_resource_utilization(self, individual) -> Dict[str, Any]:
        """Analyze resource utilization patterns"""
        instructor_usage = {}
        room_usage = {}
        time_usage = {}

        for session in individual:
            instructor_usage[session.instructor_id] = (
                instructor_usage.get(session.instructor_id, 0) + 1
            )
            room_usage[session.room_id] = room_usage.get(session.room_id, 0) + 1
            for quantum in session.quanta:
                time_usage[quantum] = time_usage.get(quantum, 0) + 1

        return {
            "instructor_utilization": {
                "total_instructors": len(self.instructors),
                "used_instructors": len(instructor_usage),
                "utilization_rate": (
                    len(instructor_usage) / len(self.instructors)
                    if self.instructors
                    else 0
                ),
                "load_distribution": dict(instructor_usage),
            },
            "room_utilization": {
                "total_rooms": len(self.rooms),
                "used_rooms": len(room_usage),
                "utilization_rate": (
                    len(room_usage) / len(self.rooms) if self.rooms else 0
                ),
                "usage_distribution": dict(room_usage),
            },
            "time_utilization": {
                "total_time_slots": len(time_usage),
                "max_concurrent_sessions": (
                    max(time_usage.values()) if time_usage else 0
                ),
                "avg_concurrent_sessions": (
                    np.mean(list(time_usage.values())) if time_usage else 0
                ),
                "time_distribution": dict(time_usage),
            },
        }

    def _analyze_schedule_patterns(self, individual) -> Dict[str, Any]:
        """Analyze scheduling patterns"""
        # Group by various dimensions
        course_patterns = {}
        instructor_patterns = {}
        room_patterns = {}

        for session in individual:
            # Course patterns
            if session.course_id not in course_patterns:
                course_patterns[session.course_id] = []
            course_patterns[session.course_id].append(
                session.quanta[0] if session.quanta else 0
            )

            # Instructor patterns
            if session.instructor_id not in instructor_patterns:
                instructor_patterns[session.instructor_id] = []
            instructor_patterns[session.instructor_id].extend(session.quanta)

            # Room patterns
            if session.room_id not in room_patterns:
                room_patterns[session.room_id] = []
            room_patterns[session.room_id].extend(session.quanta)

        # Calculate pattern statistics
        course_spread = {}
        for course_id, times in course_patterns.items():
            if len(times) > 1:
                course_spread[course_id] = max(times) - min(times)

        return {
            "course_patterns": course_patterns,
            "course_time_spread": course_spread,
            "instructor_schedules": instructor_patterns,
            "room_schedules": room_patterns,
            "avg_course_spread": (
                np.mean(list(course_spread.values())) if course_spread else 0
            ),
        }

    def _analyze_constraints(self, individual) -> Dict[str, Any]:
        """Analyze constraint violations"""
        # Use the enhanced fitness evaluator for detailed constraint analysis
        _, breakdown = self.fitness_evaluator.evaluate_individual(
            individual,
            self.qts,
            self.courses,
            self.instructors,
            self.groups,
            self.rooms,
        )

        return {
            "hard_violations": breakdown.hard_constraint_violations,
            "soft_violations": breakdown.soft_constraint_violations,
            "constraint_details": breakdown.constraint_details,
            "satisfaction_rate": 1.0
            - (breakdown.hard_constraint_violations / max(1, len(individual))),
            "quality_score": breakdown.schedule_quality_score,
        }

    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get comprehensive optimization summary"""
        if not self.evolution_stats:
            return {"error": "No optimization has been run"}

        # Calculate improvement metrics
        initial_fitness = self.evolution_stats[0]["best_fitness"]
        final_fitness = self.evolution_stats[-1]["best_fitness"]
        improvement = final_fitness - initial_fitness

        # Calculate convergence metrics
        fitness_history = [stat["best_fitness"] for stat in self.evolution_stats]
        diversity_history = [stat["diversity"] for stat in self.evolution_stats]

        return {
            "total_generations": len(self.evolution_stats),
            "initial_fitness": initial_fitness,
            "final_fitness": final_fitness,
            "improvement": improvement,
            "improvement_percent": (
                (improvement / abs(initial_fitness)) * 100
                if initial_fitness != 0
                else 0
            ),
            "final_stagnation_count": self.evolution_stats[-1]["stagnation_count"],
            "convergence_generation": self._find_convergence_generation(),
            "fitness_history": fitness_history,
            "diversity_history": diversity_history,
            "avg_fitness_improvement_per_generation": improvement
            / len(self.evolution_stats),
            "best_generation": fitness_history.index(max(fitness_history)),
            "optimization_efficiency": improvement / len(self.evolution_stats),
        }

    def _find_convergence_generation(self) -> int:
        """Find the generation where convergence was reached"""
        if len(self.evolution_stats) < 10:
            return len(self.evolution_stats)

        fitness_history = [stat["best_fitness"] for stat in self.evolution_stats]

        # Look for sustained improvement plateau
        for i in range(10, len(fitness_history)):
            window = fitness_history[i - 10 : i]
            if max(window) - min(window) < 0.001:  # Converged
                return i - 5  # Return middle of convergence window

        return len(self.evolution_stats)

    def export_results(self, filename: str = None) -> str:
        """Export optimization results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"enhanced_optimization_results_{timestamp}.json"

        results = {
            "optimization_summary": self.get_optimization_summary(),
            "solution_analysis": self.analyze_solution(),
            "evolution_history": self.evolution_stats,
            "optimization_history": self.optimization_history,
            "system_configuration": {
                "genetic_operators": self.genetic_operators.get_statistics(),
                "fitness_evaluator": self.fitness_evaluator.get_cache_statistics(),
                "population_manager": self.population_manager.get_statistics(),
            },
        }

        # Save to file
        import json

        with open(filename, "w") as f:
            json.dump(results, f, indent=2, default=str)

        self.logger.info(f"Results exported to {filename}")
        return filename

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
        self, filename: Optional[str] = None, format_type: Optional[str] = None
    ) -> str:
        """
        Export the current schedule to file.

        Args:
            filename: Output filename (auto-generated if None)
            format_type: Export format ('excel', 'csv', 'json', 'readable').
                        If None, will be inferred from filename extension.

        Returns:
            Path to exported file
        """
        if not self.best_solution:
            raise ValueError("No solution available to export")

        # Create output directory if it doesn't exist
        if filename and "/" in filename:
            output_dir = Path(filename).parent
            output_dir.mkdir(parents=True, exist_ok=True)

        # Infer format from filename if not provided
        if format_type is None and filename is not None:
            ext = Path(filename).suffix.lower()
            if ext == ".json":
                format_type = "json"
            elif ext == ".csv":
                format_type = "csv"
            elif ext == ".xlsx" or ext == ".xls":
                format_type = "excel"
            elif ext == ".txt":
                format_type = "readable"
            else:
                format_type = "json"  # default to json instead of excel
        elif format_type is None:
            format_type = "json"  # default

        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            ext_map = {"excel": "xlsx", "csv": "csv", "json": "json", "readable": "txt"}
            ext = ext_map.get(format_type, "json")
            filename = f"output/{timestamp}/timetable_{timestamp}.{ext}"

            # Create output directory
            output_dir = Path(filename).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            # Create output directory
            output_dir = Path(filename).parent
            output_dir.mkdir(parents=True, exist_ok=True)

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
            try:
                import pandas as pd

                df = pd.DataFrame(schedule_data)
                df.to_excel(filename, index=False)
            except ImportError:
                # Fallback to CSV if pandas/openpyxl not available
                format_type = "csv"
                filename = filename.replace(".xlsx", ".csv").replace(".xls", ".csv")
                import csv

                with open(filename, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=schedule_data[0].keys())
                    writer.writeheader()
                    writer.writerows(schedule_data)
        elif format_type == "csv":
            try:
                import pandas as pd

                df = pd.DataFrame(schedule_data)
                df.to_csv(filename, index=False)
            except ImportError:
                # Fallback to basic CSV
                import csv

                with open(filename, "w", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=schedule_data[0].keys())
                    writer.writeheader()
                    writer.writerows(schedule_data)
        elif format_type == "readable":
            readable_content = self._format_readable_schedule()
            with open(filename, "w") as f:
                f.write(readable_content)
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
                    "best": stats.get("best_fitness", 0),
                    "average": stats.get("avg_fitness", 0),
                    "worst": stats.get("min_fitness", 0),  # min fitness is worst
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

    def export_all_results(self, base_output_dir: str = "output") -> str:
        """
        Export all results to a timestamped folder including schedules, analysis, and visualizations.

        Args:
            base_output_dir: Base directory for output (default: "output")

        Returns:
            Path to the created output directory
        """
        if not self.best_solution:
            raise ValueError("No solution available to export")

        # Create timestamped directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path(base_output_dir) / timestamp
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Creating output directory: {output_dir}")

        try:
            # 1. Export schedules in multiple formats
            print("📊 Exporting schedules...")
            schedule_files = []

            # JSON format
            json_file = output_dir / "timetable.json"
            self.export_schedule(str(json_file), "json")
            schedule_files.append(json_file)

            # Readable format
            readable_file = output_dir / "timetable_readable.txt"
            self.export_schedule(str(readable_file), "readable")
            schedule_files.append(readable_file)

            # CSV format
            csv_file = output_dir / "timetable.csv"
            self.export_schedule(str(csv_file), "csv")
            schedule_files.append(csv_file)

            # 2. Export analysis results
            print("📈 Exporting analysis...")
            analysis = self.analyze_solution(self.best_solution)
            analysis_file = output_dir / "solution_analysis.json"

            with open(analysis_file, "w") as f:
                # Convert non-serializable objects to strings
                analysis_serializable = self._make_serializable(analysis)
                json.dump(analysis_serializable, f, indent=2)

            # 3. Export optimization summary
            print("📋 Exporting optimization summary...")
            summary = self.get_optimization_summary()
            summary_file = output_dir / "optimization_summary.json"

            with open(summary_file, "w") as f:
                summary_serializable = self._make_serializable(summary)
                json.dump(summary_serializable, f, indent=2)

            # 4. Export evolution statistics
            print("📊 Exporting evolution statistics...")
            stats_file = output_dir / "evolution_stats.json"

            with open(stats_file, "w") as f:
                stats_serializable = self._make_serializable(self.evolution_stats)
                json.dump(stats_serializable, f, indent=2)

            # 5. Generate visualizations
            print("🎨 Generating visualizations...")
            self._generate_all_visualizations(output_dir)

            # 6. Create summary report
            print("📄 Creating summary report...")
            self._create_summary_report(
                output_dir / "summary_report.txt", analysis, summary
            )

            print(f"✅ All results exported successfully to: {output_dir}")
            return str(output_dir)

        except Exception as e:
            print(f"❌ Error during export: {str(e)}")
            self.logger.error(f"Export failed: {str(e)}")
            raise

    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (int, float, str, bool)) or obj is None:
            return obj
        elif hasattr(obj, "__dict__"):
            return str(obj)
        else:
            return str(obj)

    def _generate_all_visualizations(self, output_dir: Path):
        """Generate all visualizations for the solution."""
        try:
            # Try to import and use the visualization module
            from src.visualization.charts import EvolutionVisualizer

            visualizer = EvolutionVisualizer()

            # Generate evolution plots
            if self.evolution_stats:
                # Convert evolution stats to visualization format
                fitness_history = []
                for i, stats in enumerate(self.evolution_stats):
                    fitness_history.append(
                        {
                            "generation": i,
                            "best": stats.get("best_fitness", stats.get("best", 0)),
                            "average": stats.get(
                                "avg_fitness", stats.get("average", 0)
                            ),
                            "worst": stats.get("min_fitness", stats.get("worst", 0)),
                        }
                    )

                # Fitness evolution chart
                fitness_chart_file = output_dir / "fitness_evolution.png"
                visualizer.plot_fitness_evolution(
                    fitness_history, save_path=str(fitness_chart_file)
                )
                print(f"   💹 Fitness evolution chart saved to: {fitness_chart_file}")

                # Schedule heatmap if we have a solution
                if self.best_solution:
                    heatmap_file = output_dir / "schedule_heatmap.png"
                    visualizer.plot_schedule_heatmap(
                        self.best_solution, self.rooms, save_path=str(heatmap_file)
                    )
                    print(f"   🔥 Schedule heatmap saved to: {heatmap_file}")

                    # Workload distribution
                    workload_file = output_dir / "workload_distribution.png"
                    visualizer.plot_workload_distribution(
                        self.best_solution,
                        self.instructors,
                        self.courses,
                        save_path=str(workload_file),
                    )
                    print(f"   📊 Workload distribution saved to: {workload_file}")

        except ImportError:
            print("   ⚠️  Visualization module not available - skipping charts")
        except Exception as e:
            print(f"   ⚠️  Error generating visualizations: {str(e)}")
            self.logger.warning(f"Visualization generation failed: {str(e)}")

    def _create_summary_report(self, report_path: Path, analysis: dict, summary: dict):
        """Create a human-readable summary report."""
        with open(report_path, "w") as f:
            f.write("GENETIC ALGORITHM TIMETABLING SYSTEM - OPTIMIZATION REPORT\n")
            f.write("=" * 65 + "\n\n")

            # Timestamp
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

            # Optimization Summary
            f.write("OPTIMIZATION SUMMARY\n")
            f.write("-" * 20 + "\n")
            f.write(f"Total Generations: {summary.get('total_generations', 'N/A')}\n")

            total_time = summary.get("total_time", "N/A")
            if isinstance(total_time, (int, float)):
                f.write(f"Total Time: {total_time:.2f} seconds\n")
            else:
                f.write(f"Total Time: {total_time}\n")

            f.write(f"Best Fitness: {summary.get('best_fitness', 'N/A')}\n")
            f.write(f"Final Population Size: {summary.get('population_size', 'N/A')}\n")

            evolution_rate = summary.get("evolution_rate", "N/A")
            if isinstance(evolution_rate, (int, float)):
                f.write(f"Evolution Rate: {evolution_rate:.4f}\n\n")
            else:
                f.write(f"Evolution Rate: {evolution_rate}\n\n")

            # Solution Analysis
            f.write("SOLUTION ANALYSIS\n")
            f.write("-" * 17 + "\n")
            f.write(
                f"Total Courses Scheduled: {analysis.get('total_courses', 'N/A')}\n"
            )
            f.write(
                f"Total Constraint Violations: {analysis.get('total_violations', 'N/A')}\n"
            )

            feasibility_score = analysis.get("feasibility_score", "N/A")
            if isinstance(feasibility_score, (int, float)):
                f.write(f"Feasibility Score: {feasibility_score:.2f}%\n")
            else:
                f.write(f"Feasibility Score: {feasibility_score}\n")

            room_utilization = analysis.get("room_utilization", "N/A")
            if isinstance(room_utilization, (int, float)):
                f.write(f"Room Utilization: {room_utilization:.2f}%\n")
            else:
                f.write(f"Room Utilization: {room_utilization}\n")

            instructor_efficiency = analysis.get("instructor_efficiency", "N/A")
            if isinstance(instructor_efficiency, (int, float)):
                f.write(f"Instructor Efficiency: {instructor_efficiency:.2f}%\n\n")
            else:
                f.write(f"Instructor Efficiency: {instructor_efficiency}\n\n")

            # Constraint Breakdown
            if "constraint_breakdown" in analysis:
                f.write("CONSTRAINT VIOLATIONS\n")
                f.write("-" * 20 + "\n")
                for constraint, count in analysis["constraint_breakdown"].items():
                    f.write(f"{constraint}: {count} violations\n")
                f.write("\n")

            # Recommendations
            f.write("RECOMMENDATIONS\n")
            f.write("-" * 15 + "\n")
            if analysis.get("total_violations", 0) > 0:
                f.write(
                    "• Consider increasing population size or generations for better solutions\n"
                )
                f.write("• Review constraint weights in configuration\n")
                f.write("• Check resource availability (rooms, instructors)\n")
            else:
                f.write("• Excellent! No constraint violations found\n")
                f.write("• Consider optimizing for secondary objectives\n")
            f.write("\n")

            f.write(
                "Report generated successfully by Enhanced Genetic Algorithm System\n"
            )
