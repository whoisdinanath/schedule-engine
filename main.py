"""
Schedule Engine Entry Point

Runs standard GA-based course scheduling workflow.
Refactored for clarity and testability - see docs/refactoring/ for details.
"""

from tqdm import tqdm
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

    # Print final summary with clean formatting
    tqdm.write("\n" + "🎯 " + "=" * 56)
    tqdm.write("FINAL RESULTS".center(60))
    tqdm.write("=" * 60)
    hard_viol = result["best_individual"].fitness.values[0]
    soft_pen = result["best_individual"].fitness.values[1]

    if hard_viol == 0:
        tqdm.write(f"✓ Perfect schedule found (no hard constraint violations)!")
    else:
        tqdm.write(f"⚠ Hard constraint violations: {hard_viol:.0f}")

    tqdm.write(f"  Soft constraint penalty: {soft_pen:.2f}")
    tqdm.write(f"\n  Schedule sessions: {len(result['decoded_schedule'])}")
    tqdm.write(f"  Output location: {result['output_path']}")
    tqdm.write("=" * 60)


if __name__ == "__main__":
    main()
