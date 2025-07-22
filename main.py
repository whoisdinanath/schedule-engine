"""
Unified Timetabling System - Best of all versions with working visualizations
This combines features from clean_main.py, improved_main.py, and enhanced_main.py
"""

import sys
import logging
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.config.clean_config import CleanConfig
from src.ga_deap.enhanced_system import StreamlinedTimetablingSystem
from src.visualization.charts import EvolutionVisualizer


def main():
    """Unified main function with working visualizations"""
    print("🧬 Unified Genetic Algorithm Timetabling System")
    print("=" * 60)
    print("✨ Best features from all versions with working visualizations")
    print("=" * 60)

    # Create configuration
    config = CleanConfig()

    # Ask user for quick or full optimization
    print("\nChoose optimization mode:")
    print("1. Quick Test (50 population, 30 generations) - ~2 minutes")
    print("2. Standard (100 population, 50 generations) - ~5 minutes")
    print("3. Full (200 population, 200 generations) - ~15 minutes")

    choice = input("Enter choice (1/2/3) [default: 1]: ").strip() or "1"

    if choice == "1":
        config.ga_config.population_size = 50
        config.ga_config.generations = 30
        mode = "Quick Test"
    elif choice == "2":
        config.ga_config.population_size = 100
        config.ga_config.generations = 50
        mode = "Standard"
    else:
        config.ga_config.population_size = 200
        config.ga_config.generations = 200
        mode = "Full"

    # Display configuration
    print(f"\n📋 {mode} Configuration:")
    print(f"   Population Size: {config.ga_config.population_size}")
    print(f"   Generations: {config.ga_config.generations}")
    print(f"   Crossover Rate: {config.ga_config.crossover_rate}")
    print(f"   Mutation Rate: {config.ga_config.mutation_rate}")

    try:
        # Initialize system
        system = StreamlinedTimetablingSystem(config=config)
        print("\n✅ System initialized successfully")

        # Load data
        print("\n📊 Loading data...")
        success, issues = system.load_data()

        if not success:
            print("❌ Data loading failed!")
            for issue in issues:
                print(f"   - {issue}")
            return 1

        print(f"✅ Data loaded successfully:")
        print(f"   📚 Courses: {len(system.courses)}")
        print(f"   👥 Instructors: {len(system.instructors)}")
        print(f"   🎓 Groups: {len(system.groups)}")
        print(f"   🏢 Rooms: {len(system.rooms)}")

        # Run optimization
        print(f"\n🚀 Starting {mode} optimization...")
        print("⏱️  Please wait...")

        start_time = datetime.now()
        result = system.run_optimization()
        end_time = datetime.now()

        duration = end_time - start_time

        if result and "best_individual" in result:
            best_solution = result["best_individual"]
            best_fitness = result["best_fitness"]
            generations = result["generations"]

            print(
                f"\n✅ Optimization completed in {duration.total_seconds():.2f} seconds"
            )
            print(f"🏆 Best Fitness: {best_fitness:.4f}")
            print(f"📈 Generations: {generations}")

            # Analyze solution
            print("\n📊 Analyzing solution...")
            analysis = system.analyze_solution(best_solution)

            print(f"   ❌ Hard Violations: {analysis.get('hard_violations', 0)}")
            print(f"   ⚠️  Soft Violations: {analysis.get('soft_violations', 0)}")
            print(f"   📊 Total Violations: {analysis.get('total_violations', 0)}")
            print(f"   🎯 Fitness Score: {analysis.get('fitness_score', 0):.4f}")

            # Resource utilization
            if "resource_utilization" in analysis:
                util = analysis["resource_utilization"]
                print(f"\n🏭 Resource Utilization:")
                print(
                    f"   👥 Instructors: {util.get('instructor_utilization', 0):.1f}%"
                )
                print(f"   🏢 Rooms: {util.get('room_utilization', 0):.1f}%")
                print(f"   ⏰ Time Slots: {util.get('time_utilization', 0):.1f}%")

            # Create visualizations
            print("\n🎨 Creating visualizations...")
            visualizer = EvolutionVisualizer()

            # Create output directory
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = Path("output") / f"unified_{timestamp}"
            output_dir.mkdir(parents=True, exist_ok=True)

            try:
                # 1. Fitness evolution
                if system.evolution_stats:
                    fitness_history = []
                    for i, stats in enumerate(system.evolution_stats):
                        fitness_history.append(
                            {
                                "generation": i,
                                "best": stats.get("best_fitness", stats.get("best", 0)),
                                "average": stats.get(
                                    "avg_fitness", stats.get("average", 0)
                                ),
                                "worst": stats.get(
                                    "min_fitness", stats.get("worst", 0)
                                ),
                            }
                        )

                    fitness_file = output_dir / "fitness_evolution.pdf"
                    visualizer.plot_fitness_evolution(
                        fitness_history, save_path=str(fitness_file), show_plot=True
                    )
                    print(f"   📈 Fitness evolution: {fitness_file}")

                # 2. Schedule heatmap
                heatmap_file = output_dir / "schedule_heatmap.pdf"
                visualizer.plot_schedule_heatmap(
                    best_solution,
                    system.courses,
                    system.instructors,
                    system.rooms,
                    system.groups,
                    view_type="room",
                    save_path=str(heatmap_file),
                    show_plot=False,
                )
                print(f"   🗓️  Schedule heatmap: {heatmap_file}")

                # 3. Workload distribution
                workload_file = output_dir / "workload_distribution.pdf"
                visualizer.plot_workload_distribution(
                    best_solution,
                    system.instructors,
                    system.courses,
                    save_path=str(workload_file),
                    show_plot=False,
                )
                print(f"   👥 Workload distribution: {workload_file}")

            except Exception as e:
                print(f"   ⚠️  Visualization error: {e}")
                print("   📊 Continuing with export...")

            # Export results
            print("\n💾 Exporting results...")
            try:
                full_output_dir = system.export_all_results(str(output_dir))
                print(f"   📁 All results saved to: {full_output_dir}")
            except Exception as e:
                print(f"   ⚠️  Export error: {e}")

            # Final summary
            print(f"\n🎯 {mode.upper()} OPTIMIZATION COMPLETE!")
            print(f"   📊 Best Fitness: {best_fitness:.2f}")
            print(f"   ⏱️  Duration: {duration.total_seconds():.2f} seconds")
            print(f"   ❌ Hard Violations: {analysis.get('hard_violations', 0)}")
            print(f"   ⚠️  Soft Violations: {analysis.get('soft_violations', 0)}")
            print(f"   📁 Results: {output_dir}")

        else:
            print("❌ No solution found")
            return 1

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logging.exception("Detailed error:")
        return 1

    print("\n🎉 Process completed successfully!")
    print("\n📝 Why do you have 3 main files?")
    print("   • clean_main.py - Basic version (streamlined)")
    print("   • improved_main.py - Enhanced version (more features)")
    print("   • enhanced_main.py - Advanced version (full optimization)")
    print("   • unified_main.py - This file (best of all with working viz)")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n⚠️  Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
