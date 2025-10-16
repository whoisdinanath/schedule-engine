"""
Schedule Engine Entry Point

Runs standard GA-based course scheduling workflow.
Refactored for clarity and testability - see docs/refactoring/ for details.
"""

from tqdm import tqdm
from src.workflows import run_standard_workflow
from src.utils.console import write_header, write_separator, write_info
from config.ga_params import (
    POP_SIZE,
    NGEN,
    CXPB,
    MUTPB,
    USE_MULTIPROCESSING,
    NUM_WORKERS,
)


def main():
    """
    Execute standard scheduling workflow.

    Pipeline:
        1. Load input data from data/
        2. Validate input for consistency
        3. Run NSGA-II genetic algorithm (with optional parallelization)
        4. Export best schedule to output/
        5. Generate evolution plots and reports

    Configuration is loaded from config/ga_params.py and config/constraints.py.
    Results are saved to output/evaluation_<timestamp>/.

    Parallelization:
        - If USE_MULTIPROCESSING=True, uses multiprocessing.Pool for parallel fitness evaluation
        - Provides 3-6× speedup on multi-core systems
        - Set USE_MULTIPROCESSING=False for debugging or single-threaded execution
    """
    pool = None

    # Create multiprocessing pool if enabled
    if USE_MULTIPROCESSING:
        import multiprocessing

        pool = multiprocessing.Pool(processes=NUM_WORKERS)
        write_info(f"Multiprocessing enabled: {pool._processes} workers")
    else:
        write_info("Running in single-threaded mode (USE_MULTIPROCESSING=False)")

    try:
        result = run_standard_workflow(
            pop_size=POP_SIZE,
            generations=NGEN,
            crossover_prob=CXPB,
            mutation_prob=MUTPB,
            validate=True,  # Enable input validation
            pool=pool,  # Pass pool for parallel evaluation
        )

        # Print final summary with clean formatting
        write_header("FINAL RESULTS")
        hard_viol = result["best_individual"].fitness.values[0]
        soft_pen = result["best_individual"].fitness.values[1]

        if hard_viol == 0:
            write_info("Perfect schedule found (no hard constraint violations)!")
        else:
            write_info(f"Hard constraint violations: {hard_viol:.0f}")

        write_info(f"Soft constraint penalty: {soft_pen:.2f}")
        write_info(f"Schedule sessions: {len(result['decoded_schedule'])}")
        write_info(f"Output location: {result['output_path']}")
        write_separator()

    finally:
        # Clean up multiprocessing pool
        if pool is not None:
            pool.close()
            pool.join()


if __name__ == "__main__":
    main()
