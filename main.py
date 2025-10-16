"""
Schedule Engine Entry Point

Runs standard GA-based course scheduling workflow.
Refactored for clarity and testability - see docs/refactoring/ for details.
"""

from src.workflows import run_standard_workflow
from config.ga_params import POP_SIZE, NGEN, CXPB, MUTPB


def main():
    """
    Execute standard scheduling workflow.

    Pipeline:
        1. Load input data from data/
        2. Validate input for consistency
        3. Run NSGA-II genetic algorithm
        4. Export best schedule to output/
        5. Generate evolution plots and reports

    Configuration is loaded from config/ga_params.py and config/constraints.py.
    Results are saved to output/evaluation_<timestamp>/.
    """
    result = run_standard_workflow(
        pop_size=POP_SIZE,
        generations=NGEN,
        crossover_prob=CXPB,
        mutation_prob=MUTPB,
        validate=True,  # Enable input validation
    )

    # Print final summary
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Fitness: {result['best_individual'].fitness.values}")
    print(
        f"  - Hard constraint violations: {result['best_individual'].fitness.values[0]:.0f}"
    )
    print(
        f"  - Soft constraint penalty: {result['best_individual'].fitness.values[1]:.2f}"
    )
    print(f"\nSchedule: {len(result['decoded_schedule'])} sessions")
    print(f"Output: {result['output_path']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
