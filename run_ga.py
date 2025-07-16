#!/usr/bin/env python3
"""
Simple launcher for the Timetabling GA System

This script provides a command-line interface to run the genetic algorithm
timetabling optimization with basic parameters.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.ga_deap.enhanced_system import EnhancedTimetablingSystem


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description="University Timetabling Genetic Algorithm"
    )
    parser.add_argument("--data", default="data", help="Data directory path")
    parser.add_argument(
        "--generations", type=int, default=50, help="Number of generations"
    )
    parser.add_argument("--population", type=int, default=100, help="Population size")
    parser.add_argument("--crossover", type=float, default=0.8, help="Crossover rate")
    parser.add_argument("--mutation", type=float, default=0.1, help="Mutation rate")
    parser.add_argument("--output", default=None, help="Output filename")
    parser.add_argument(
        "--format",
        choices=["excel", "csv", "json"],
        default="excel",
        help="Output format",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    # Initialize system
    system = EnhancedTimetablingSystem(
        data_path=args.data,
        log_level=10 if args.verbose else 20,  # DEBUG if verbose else INFO
    )

    print("🏫 University Timetabling System")
    print("=" * 40)

    # Load data
    print("📂 Loading data...")
    success, issues = system.load_data()

    if not success:
        print(f"❌ Failed to load data: {issues}")
        return 1

    if issues:
        print(f"⚠️  Found {len(issues)} data issues (proceeding anyway)")
        if args.verbose:
            for issue in issues:
                print(f"   • {issue}")

    # Progress callback
    def progress_callback(gen, record, stats):
        print(f"Generation {gen}: Best={record['max']:.4f}, Avg={record['avg']:.4f}")

    # Run optimization
    print(f"\n🚀 Starting optimization...")
    print(f"   Generations: {args.generations}")
    print(f"   Population: {args.population}")
    print(f"   Crossover: {args.crossover}")
    print(f"   Mutation: {args.mutation}")

    try:
        best_solution = system.run_optimization(
            generations=args.generations,
            population_size=args.population,
            crossover_rate=args.crossover,
            mutation_rate=args.mutation,
            progress_callback=progress_callback if args.verbose else None,
            update_interval=5,
        )

        # Show results
        summary = system.get_solution_summary()
        print(f"\n✅ Optimization completed!")
        print(f"   Best fitness: {summary['fitness_score']:.4f}")
        print(f"   Sessions scheduled: {summary['total_sessions']}")
        print(f"   Time slots used: {summary['unique_time_slots']}")
        print(f"   Rooms utilized: {summary['rooms_used']}")
        print(f"   Instructors assigned: {summary['instructors_used']}")

        # Export results
        output_file = system.export_schedule(args.output, args.format)
        print(f"💾 Schedule exported to: {output_file}")

        return 0

    except Exception as e:
        print(f"❌ Optimization failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
