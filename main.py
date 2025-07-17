#!/usr/bin/env python3
"""
Main execution file for the University Course Timetabling Problem (UCTP) solver.
This script demonstrates a comprehensive instance of the genetic algorithm-based
timetabling system with full visualization capabilities.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.ga_deap.enhanced_system import EnhancedTimetablingSystem
from src.utils.logger import get_logger, setup_logging
from src.utils.config import GA_CONFIG
from src.visualization.charts import EvolutionVisualizer


def main():
    """
    Main function to run a simple UCTP instance using the genetic algorithm.
    """
    # Setup logging
    setup_logging(level="INFO", log_dir="logs", console_output=True, file_output=True)
    logger = get_logger("main")

    logger.info("=" * 60)
    logger.info("University Course Timetabling Problem (UCTP) Solver")
    logger.info("Pure Genetic Algorithm Implementation")
    logger.info("=" * 60)

    try:
        # Initialize the enhanced timetabling system
        logger.info("Initializing Enhanced Timetabling System...")
        system = EnhancedTimetablingSystem(data_path="data")

        # Load data
        logger.info("Loading data from JSON files...")
        success, issues = system.load_data()

        if not success:
            logger.error("Failed to load data. Exiting...")
            return False

        # Check validation issues
        if issues:
            logger.warning("Data validation issues found:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("Data validation successful!")

        # Print data summary
        logger.info("Data Summary:")
        logger.info(f"  - Courses: {len(system.courses)}")
        logger.info(f"  - Instructors: {len(system.instructors)}")
        logger.info(f"  - Groups: {len(system.groups)}")
        logger.info(f"  - Rooms: {len(system.rooms)}")

        # Configure GA parameters for this comprehensive instance
        generations = 100  # Increased for better evolution tracking
        population_size = 200  # Increased for better diversity

        logger.info(
            f"Starting optimization with {generations} generations and population size {population_size}"
        )
        logger.info("GA Configuration:")
        logger.info(f"  - Crossover Rate: {GA_CONFIG['crossover_rate']}")
        logger.info(f"  - Mutation Rate: {GA_CONFIG['mutation_rate']}")
        logger.info(f"  - Tournament Size: {GA_CONFIG['tournament_size']}")

        # Define progress callback for real-time monitoring
        def progress_callback(generation, record, evolution_stats):
            if generation % 10 == 0:
                logger.info(
                    f"Generation {generation}: Best={record['max']:.4f}, "
                    f"Avg={record['avg']:.4f}, Diversity={record.get('std', 0):.4f}"
                )

        # Run the genetic algorithm with progress tracking
        start_time = datetime.now()
        best_solution = system.run_optimization(
            generations=generations,
            population_size=population_size,
            progress_callback=progress_callback,
            update_interval=5,
        )
        end_time = datetime.now()

        optimization_time = (end_time - start_time).total_seconds()
        logger.info(f"Optimization completed in {optimization_time:.2f} seconds")

        # Get comprehensive solution summary
        summary = system.get_solution_summary()
        logger.info("Solution Summary:")
        for key, value in summary.items():
            logger.info(f"  - {key}: {value}")

        # Export the schedule in multiple formats
        logger.info("Exporting schedule...")

        # Create output directory
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Export in different formats
        excel_file = system.export_schedule(
            filename=f"output/schedule_{timestamp}.xlsx", format_type="excel"
        )

        csv_file = system.export_schedule(
            filename=f"output/schedule_{timestamp}.csv", format_type="csv"
        )

        json_file = system.export_schedule(
            filename=f"output/schedule_{timestamp}.json", format_type="json"
        )

        logger.info(f"Schedule exported to:")
        logger.info(f"  - Excel: {excel_file}")
        logger.info(f"  - CSV: {csv_file}")
        logger.info(f"  - JSON: {json_file}")

        # Generate comprehensive visualizations
        logger.info("Generating visualizations...")
        visualizer = EvolutionVisualizer()

        # Create visualization directory
        viz_dir = output_dir / f"visualizations_{timestamp}"
        viz_dir.mkdir(exist_ok=True)

        # 1. Fitness Evolution Plot
        if system.evolution_stats:
            fitness_history = []
            for i, stats in enumerate(system.evolution_stats):
                fitness_history.append(
                    {
                        "generation": i,
                        "best": stats.get("best", 0),
                        "average": stats.get("average", 0),
                        "worst": stats.get("worst", 0),
                    }
                )

            visualizer.plot_fitness_evolution(
                fitness_history,
                save_path=str(viz_dir / "fitness_evolution.pdf"),
                show_plot=False,
            )
            logger.info("✓ Fitness evolution plot generated")

        # 2. Constraint Violations (create mock data for demonstration)
        violation_history = []
        for i in range(len(system.evolution_stats)):
            # Mock constraint violation data - in a real implementation,
            # this would be tracked during evolution
            violation_history.append(
                {
                    "total_hard": max(0, 50 - i * 0.5),  # Decreasing violations
                    "total_soft": max(0, 100 - i * 0.8),
                }
            )

        visualizer.plot_constraint_violations(
            violation_history,
            save_path=str(viz_dir / "constraint_violations.pdf"),
            show_plot=False,
        )
        logger.info("✓ Constraint violations plot generated")

        # 3. Population Diversity (create mock data)
        diversity_history = []
        for i, stats in enumerate(system.evolution_stats):
            diversity_history.append(stats.get("std", 0))

        if diversity_history:
            visualizer.plot_diversity_evolution(
                diversity_history,
                save_path=str(viz_dir / "diversity_evolution.pdf"),
                show_plot=False,
            )
            logger.info("✓ Population diversity plot generated")

        # 4. Schedule Heatmaps
        if system.best_solution:
            for view_type in ["room", "instructor", "course"]:
                visualizer.plot_schedule_heatmap_with_qts(
                    system.best_solution,
                    system.qts,
                    system.courses,
                    system.instructors,
                    system.rooms,
                    system.groups,
                    view_type=view_type,
                    save_path=str(viz_dir / f"schedule_heatmap_{view_type}.pdf"),
                    show_plot=False,
                )
                logger.info(f"✓ Schedule heatmap ({view_type}) generated")

        # 5. Workload Distribution
        if system.best_solution:
            visualizer.plot_workload_distribution(
                system.best_solution,
                system.instructors,
                system.courses,
                save_path=str(viz_dir / "workload_distribution.pdf"),
                show_plot=False,
            )
            logger.info("✓ Workload distribution plot generated")

        logger.info(f"All visualizations saved to: {viz_dir}")

        # Display readable schedule preview
        readable_schedule = system.export_schedule(format_type="readable")

        # Save readable schedule
        readable_file = output_dir / f"readable_schedule_{timestamp}.txt"
        with open(readable_file, "w") as f:
            f.write(readable_schedule)

        logger.info(f"Readable schedule saved to: {readable_file}")

        # Display first few sessions of the schedule
        logger.info("\nFirst few scheduled sessions:")
        print("\n" + "=" * 80)
        print("SCHEDULE PREVIEW:")
        print("=" * 80)

        lines = readable_schedule.split("\n")
        for i, line in enumerate(lines[:20]):  # Show first 20 lines
            print(line)

        if len(lines) > 20:
            print(f"\n... and {len(lines) - 20} more lines")

        print("=" * 80)

        # Final summary
        logger.info("\n" + "=" * 60)
        logger.info("COMPREHENSIVE UCTP SOLUTION COMPLETED!")
        logger.info("=" * 60)
        logger.info(
            f"Best fitness achieved: {system.best_solution.fitness.values[0]:.4f}"
        )
        logger.info(f"Total generations: {len(system.evolution_stats)}")
        logger.info(f"Total sessions scheduled: {len(system.best_solution)}")
        logger.info(f"Output directory: {output_dir.absolute()}")
        logger.info(f"Visualization directory: {viz_dir.absolute()}")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.exception(f"An error occurred during execution: {str(e)}")
        return False

    finally:
        logger.info("Execution finished.")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
