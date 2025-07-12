"""
Main entry point for the PURE Genetic Algorithm-based University Course Timetabling System.
Provides a high-level interface for running the timetabling optimization.
It is currently Command Line based

This system uses a pure GA approach without any local search components.
Rooms are always available (no room availability constraints).
"""

from typing import Dict, List, Optional, Any, Callable
import argparse
import sys
import time
import os
from pathlib import Path
from datetime import datetime

from src.entities import Course, Instructor, Room, Group
from src.data.ingestion import DataIngestion
from src.data.validation import DataValidator
from src.ga.engine import GAEngine
from src.output.generator import OutputGenerator
from src.constraints.checker import ConstraintChecker
from src.utils.logger import setup_logging, get_logger
from src.utils.config import GA_CONFIG
from src.visualization.charts import EvolutionVisualizer


class TimetablingSystem:
    """
    Main timetabling system that orchestrates the entire optimization process.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the timetabling system.

        Args:
            config: Configuration dictionary
        """
        # Setup logging
        setup_logging()
        self.logger = get_logger(self.__class__.__name__)

        # Configuration
        self.config = config or GA_CONFIG

        # Components
        self.data_ingestion = DataIngestion()
        self.data_validator = DataValidator()
        self.ga_engine = GAEngine(config)
        self.output_generator = OutputGenerator()
        self.constraint_checker = ConstraintChecker()
        self.visualizer = EvolutionVisualizer()

        # Data storage
        self.courses = {}
        self.instructors = {}
        self.rooms = {}
        self.groups = {}

        # Results
        self.best_solution = None
        self.evolution_stats = None

        # Output directory with timestamp
        self.output_dir = self._create_timestamped_output_dir()

    def _create_timestamped_output_dir(self) -> str:
        """
        Create a timestamped output directory.

        Returns:
            Path to the created directory
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = f"output/run_{timestamp}"
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(f"{output_dir}/visualizations", exist_ok=True)
        self.logger.info(f"Created output directory: {output_dir}")
        return output_dir

    def load_data(
        self,
        courses_file: str,
        instructors_file: str,
        rooms_file: str,
        groups_file: str,
        skip_validation: bool = False,
    ) -> bool:
        """
        Load data from input files.

        Args:
            courses_file: Path to courses CSV file
            instructors_file: Path to instructors CSV file
            rooms_file: Path to rooms CSV file
            groups_file: Path to groups CSV file
            skip_validation: Skip validation errors and continue

        Returns:
            True if all data loaded successfully, False otherwise
        """
        try:
            self.logger.info("Loading input data...")

            # Load all data using the actual interface
            if not self.data_ingestion.load_data(
                courses_file, instructors_file, rooms_file, groups_file
            ):
                return False

            # Access the loaded data from the ingestion object
            self.courses = self.data_ingestion.courses
            self.instructors = self.data_ingestion.instructors
            self.rooms = self.data_ingestion.rooms
            self.groups = self.data_ingestion.groups

            # Log loading results
            self.logger.info(f"Loaded {len(self.courses)} courses")
            self.logger.info(f"Loaded {len(self.instructors)} instructors")
            self.logger.info(f"Loaded {len(self.rooms)} rooms")
            self.logger.info(f"Loaded {len(self.groups)} groups")

            # Validate data
            if not self._validate_data(skip_validation):
                return False

            self.logger.info("Data loading completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error loading data: {str(e)}")
            return False

    def _validate_data(self, skip_validation: bool = False) -> bool:
        """
        Validate loaded data for consistency and completeness.

        Args:
            skip_validation: Skip validation errors and continue

        Returns:
            True if validation passes, False otherwise
        """
        try:
            self.logger.info("Validating input data...")

            # Validate data using the actual interface
            is_valid, errors, warnings = self.data_validator.validate_all(
                self.courses, self.instructors, self.rooms, self.groups
            )

            # Log warnings
            for warning in warnings:
                self.logger.warning(f"Validation warning: {warning}")

            if not is_valid:
                if skip_validation:
                    self.logger.warning(
                        "Data validation failed but continuing due to --skip-validation:"
                    )
                    for error in errors:
                        self.logger.warning(f"  - {error}")
                else:
                    self.logger.error("Data validation failed:")
                    for error in errors:
                        self.logger.error(f"  - {error}")
                    return False

            self.logger.info("Data validation passed")
            return True

        except Exception as e:
            self.logger.error(f"Error during data validation: {str(e)}")
            return False

    def optimize(
        self, callback: Optional[Callable[[int, float, Dict[str, Any]], bool]] = None
    ) -> Optional[Any]:
        """
        Run the genetic algorithm optimization.

        Args:
            callback: Optional callback function for monitoring progress

        Returns:
            Best chromosome found, or None if optimization failed
        """
        try:
            if not all([self.courses, self.instructors, self.rooms, self.groups]):
                self.logger.error("Data not loaded. Call load_data() first.")
                return None

            self.logger.info("Starting timetable optimization...")

            # Initialize and run GA
            self.ga_engine.initialize(
                self.courses, self.instructors, self.rooms, self.groups
            )
            self.best_solution = self.ga_engine.evolve(
                self.courses, self.instructors, self.rooms, self.groups, callback
            )

            # Store evolution statistics
            self.evolution_stats = self.ga_engine.get_statistics()

            if self.best_solution:
                # Analyze final solution
                self._analyze_solution()
                self.logger.info("Optimization completed successfully")
                return self.best_solution
            else:
                self.logger.error("Optimization failed to find a solution")
                return None

        except Exception as e:
            self.logger.error(f"Error during optimization: {str(e)}")
            return None

    def _analyze_solution(self) -> None:
        """
        Analyze and log information about the final solution.
        """
        if not self.best_solution:
            return

        # Check constraints
        hard_violations, soft_violations = (
            self.constraint_checker.check_all_constraints(
                self.best_solution,
                self.courses,
                self.instructors,
                self.rooms,
                self.groups,
            )
        )

        total_hard = sum(hard_violations.values())
        total_soft = sum(soft_violations.values())

        self.logger.info("=== SOLUTION ANALYSIS ===")
        self.logger.info(f"Total genes (sessions): {len(self.best_solution.genes)}")
        self.logger.info(f"Hard constraint violations: {total_hard}")
        self.logger.info(f"Soft constraint violations: {total_soft}")

        if total_hard == 0:
            self.logger.info("✓ Solution is FEASIBLE (no hard constraint violations)")
        else:
            self.logger.warning("✗ Solution has hard constraint violations:")
            for constraint, count in hard_violations.items():
                if count > 0:
                    self.logger.warning(f"  {constraint}: {count}")

        if total_soft > 0:
            self.logger.info("Soft constraint violations (quality issues):")
            for constraint, count in soft_violations.items():
                if count > 0:
                    self.logger.info(f"  {constraint}: {count}")

    def export_schedule(
        self,
        output_path: str = None,
        format_type: str = "csv",
        detail_level: str = "detailed",
    ) -> bool:
        """
        Export the best schedule to a file.

        Args:
            output_path: Path to save the schedule (defaults to timestamped directory)
            format_type: Export format ('csv', 'excel', 'json')
            detail_level: Detail level ('basic', 'detailed', 'summary')

        Returns:
            True if export successful, False otherwise
        """
        if not self.best_solution:
            self.logger.error("No solution available to export. Run optimize() first.")
            return False

        # Use timestamped directory if no path specified
        if output_path is None:
            extension = "xlsx" if format_type == "excel" else format_type
            output_path = f"{self.output_dir}/schedule.{extension}"

        return self.output_generator.export_schedule(
            self.best_solution,
            self.courses,
            self.instructors,
            self.rooms,
            self.groups,
            output_path,
            format_type,
            detail_level,
        )

    def generate_visualizations(
        self,
        create_individual: bool = True,
        create_comprehensive: bool = True,
        show_plots: bool = False,
    ) -> bool:
        """
        Generate visualization plots for the optimization results.

        Args:
            create_individual: Create individual plots
            create_comprehensive: Create comprehensive report
            show_plots: Display plots interactively

        Returns:
            True if successful, False otherwise
        """
        if not self.best_solution or not self.evolution_stats:
            self.logger.error(
                "No solution available for visualization. Run optimize() first."
            )
            return False

        try:
            viz_dir = f"{self.output_dir}/visualizations"
            self.logger.info(f"Generating visualizations in: {viz_dir}")

            if create_comprehensive:
                # Create comprehensive report only (includes all plots)
                self.logger.info("Creating comprehensive visualization report...")
                self.visualizer.create_comprehensive_report(
                    self.evolution_stats,
                    self.best_solution,
                    self.courses,
                    self.instructors,
                    self.rooms,
                    self.groups,
                    output_dir=viz_dir,  # Save directly to visualizations folder
                )
            elif create_individual:
                # Individual plots only if comprehensive is disabled
                self.logger.info("Creating individual visualization plots...")

                # Fitness evolution
                self.visualizer.plot_fitness_evolution(
                    self.ga_engine.fitness_history,
                    save_path=f"{viz_dir}/fitness_evolution.pdf",
                    show_plot=show_plots,
                )

                # Constraint violations
                self.visualizer.plot_constraint_violations(
                    self.ga_engine.violation_history,
                    save_path=f"{viz_dir}/constraint_violations.pdf",
                    show_plot=show_plots,
                )

                # Diversity evolution
                self.visualizer.plot_diversity_evolution(
                    self.ga_engine.diversity_history,
                    save_path=f"{viz_dir}/diversity_evolution.pdf",
                    show_plot=show_plots,
                )

                # Schedule heatmaps
                for view_type in ["room", "instructor", "course"]:
                    self.visualizer.plot_schedule_heatmap(
                        self.best_solution,
                        self.courses,
                        self.instructors,
                        self.rooms,
                        self.groups,
                        view_type=view_type,
                        save_path=f"{viz_dir}/schedule_heatmap_{view_type}.pdf",
                        show_plot=show_plots,
                    )

                # Workload distribution
                self.visualizer.plot_workload_distribution(
                    self.best_solution,
                    self.instructors,
                    self.courses,
                    save_path=f"{viz_dir}/workload_distribution.pdf",
                    show_plot=show_plots,
                )

            self.logger.info("Visualization generation completed successfully")
            return True

        except Exception as e:
            self.logger.error(f"Error generating visualizations: {str(e)}")
            return False

    def get_output_directory(self) -> str:
        """
        Get the timestamped output directory path.

        Returns:
            Output directory path
        """
        return self.output_dir

    def print_schedule(self) -> None:
        """
        Print the schedule summary to console.
        """
        if not self.best_solution:
            self.logger.error("No solution available to print. Run optimize() first.")
            return

        self.output_generator.print_schedule_summary(
            self.best_solution, self.courses, self.instructors, self.rooms, self.groups
        )

    def get_statistics(self) -> Optional[Dict[str, Any]]:
        """
        Get evolution and solution statistics.

        Returns:
            Statistics dictionary or None if no solution
        """
        return self.evolution_stats

    def is_solution_feasible(self) -> bool:
        """
        Check if the current solution is feasible (no hard constraint violations).

        Returns:
            True if solution is feasible, False otherwise
        """
        if not self.best_solution:
            return False

        try:
            # Check constraints
            hard_violations, soft_violations = (
                self.constraint_checker.check_all_constraints(
                    self.best_solution,
                    self.courses,
                    self.instructors,
                    self.rooms,
                    self.groups,
                )
            )

            total_hard = sum(hard_violations.values())
            return total_hard == 0

        except Exception as e:
            self.logger.error(f"Error checking solution feasibility: {str(e)}")
            return False


def create_sample_callback():
    """
    Create a sample callback function for monitoring GA progress.

    Returns:
        Callback function
    """

    def callback(generation: int, best_fitness: float, stats: Dict[str, Any]) -> bool:
        """
        Sample callback that prints progress and can stop evolution.

        Args:
            generation: Current generation number
            best_fitness: Best fitness achieved so far
            stats: Additional statistics

        Returns:
            True to continue evolution, False to stop
        """
        if generation % 10 == 0:  # Print every 10 generations
            violations = stats.get("violations", {})
            hard_violations = violations.get("total_hard", 0)

            print(
                f"Generation {generation:3d}: "
                f"Fitness = {best_fitness:8.4f}, "
                f"Hard violations = {hard_violations:3d}"
            )

            # Stop if we find a feasible solution
            if hard_violations == 0:
                print("✓ Found feasible solution! Stopping evolution.")
                return False

        return True  # Continue evolution

    return callback


def main():
    """
    Main function for command-line interface.
    """
    parser = argparse.ArgumentParser(
        description="GA-based University Course Timetabling System"
    )

    # Input files
    parser.add_argument(
        "--courses",
        default="data/sample_courses.csv",
        help="Path to courses CSV file (default: data/sample_courses.csv)",
    )
    parser.add_argument(
        "--instructors",
        default="data/sample_instructors.csv",
        help="Path to instructors CSV file (default: data/sample_instructors.csv)",
    )
    parser.add_argument(
        "--rooms",
        default="data/sample_rooms.csv",
        help="Path to rooms CSV file (default: data/sample_rooms.csv)",
    )
    parser.add_argument(
        "--groups",
        default="data/sample_groups.csv",
        help="Path to groups CSV file (default: data/sample_groups.csv)",
    )

    # Output options
    parser.add_argument(
        "--output",
        help="Output file path for schedule (default: timestamped directory)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "excel", "json"],
        default="csv",
        help="Output format (default: csv)",
    )
    parser.add_argument(
        "--detail",
        choices=["basic", "detailed", "summary"],
        default="detailed",
        help="Detail level for output (default: detailed)",
    )

    # Visualization options
    parser.add_argument(
        "--no-visualizations",
        action="store_true",
        help="Skip visualization generation (default: generate visualizations)",
    )
    parser.add_argument(
        "--show-plots",
        action="store_true",
        help="Display plots interactively (default: save only)",
    )
    parser.add_argument(
        "--no-viz-individual",
        action="store_true",
        help="Skip individual visualization plots (default: create them)",
    )
    parser.add_argument(
        "--no-viz-comprehensive",
        action="store_true",
        help="Skip comprehensive visualization report (default: create it)",
    )

    # GA parameters dynamically fetched from GA_CONFIG
    parser.add_argument(
        "--population",
        type=int,
        default=GA_CONFIG["population_size"],
        help=f'Population size (default: {GA_CONFIG["population_size"]})',
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=GA_CONFIG["max_generations"],
        help=f'Maximum generations (default: {GA_CONFIG["max_generations"]})',
    )
    parser.add_argument(
        "--mutation-rate",
        type=float,
        default=GA_CONFIG["mutation_rate"],
        help=f'Mutation rate (default: {GA_CONFIG["mutation_rate"]})',
    )
    parser.add_argument(
        "--crossover-rate",
        type=float,
        default=GA_CONFIG["crossover_rate"],
        help=f'Crossover rate (default: {GA_CONFIG["crossover_rate"]})',
    )
    parser.add_argument(
        "--elite-size",
        type=int,
        default=GA_CONFIG["elite_size"],
        help=f'Elite size (default: {GA_CONFIG["elite_size"]})',
    )
    parser.add_argument(
        "--tournament-size",
        type=int,
        default=GA_CONFIG["tournament_size"],
        help=f'Tournament size (default: {GA_CONFIG["tournament_size"]})',
    )

    # Other options with defaults
    parser.add_argument(
        "--print-schedule",
        action="store_true",
        default=True,
        help="Print schedule to console (default: True)",
    )
    parser.add_argument(
        "--skip-validation",
        action="store_true",
        default=False,
        help="Skip validation errors and continue with optimization (default: False)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        default=True,
        help="Verbose output (default: True)",
    )

    args = parser.parse_args()

    try:
        # Create custom configuration with all provided parameters
        config = GA_CONFIG.copy()
        config["population_size"] = args.population
        config["max_generations"] = args.generations
        config["mutation_rate"] = args.mutation_rate
        config["crossover_rate"] = args.crossover_rate
        config["elite_size"] = args.elite_size
        config["tournament_size"] = args.tournament_size

        # Initialize system
        system = TimetablingSystem(config)
        print(f"🎯 Output directory: {system.get_output_directory()}")

        # Load data
        if not system.load_data(
            args.courses,
            args.instructors,
            args.rooms,
            args.groups,
            args.skip_validation,
        ):
            print("Failed to load data. Exiting.")
            sys.exit(1)

        # Create callback for progress monitoring
        callback = create_sample_callback() if args.verbose else None

        # Run optimization
        print("Starting optimization...")
        start_time = time.time()

        solution = system.optimize(callback)

        end_time = time.time()
        duration = end_time - start_time

        if solution:
            print(f"\nOptimization completed in {duration:.2f} seconds")

            # Print feasibility status
            if system.is_solution_feasible():
                print("✓ Found a FEASIBLE solution!")
            else:
                print("✗ Solution has constraint violations")

            # Print schedule if requested
            if args.print_schedule:
                system.print_schedule()

            # Export schedule
            if system.export_schedule(args.output, args.format, args.detail):
                print(f"📄 Schedule exported to: {system.get_output_directory()}")
            else:
                print("Failed to export schedule")

            # Generate visualizations
            if not args.no_visualizations:
                print("\n🎨 Generating visualizations...")
                if system.generate_visualizations(
                    create_individual=not args.no_viz_individual,
                    create_comprehensive=not args.no_viz_comprehensive,
                    show_plots=args.show_plots,
                ):
                    print(
                        f"📊 Visualizations saved to: {system.get_output_directory()}/visualizations/"
                    )
                else:
                    print("⚠️ Failed to generate some visualizations")

            # Print statistics
            stats = system.get_statistics()
            if stats:
                evolution_stats = stats.get("evolution", {})
                print(f"\nEvolution Statistics:")
                print(f"  Generations: {evolution_stats.get('generations', 0)}")
                print(
                    f"  Total evaluations: {evolution_stats.get('total_evaluations', 0)}"
                )
                print(
                    f"  Best fitness: {stats.get('fitness', {}).get('best_achieved', 0):.6f}"
                )

            print(f"\n✅ All outputs saved to: {system.get_output_directory()}")

        else:
            print("Optimization failed to find a solution")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nOptimization interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
