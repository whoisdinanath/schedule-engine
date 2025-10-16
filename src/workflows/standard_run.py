"""
Standard Workflow Module

Orchestrates full scheduling pipeline: load → validate → schedule → export.
Extracted from main.py for better testability and reusability.
"""

import os
import random
from datetime import datetime
from typing import Dict, Optional
from tqdm import tqdm

from src.encoder.input_encoder import (
    load_courses,
    load_groups,
    load_instructors,
    load_rooms,
    link_courses_and_groups,
    link_courses_and_instructors,
)
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.decoder.individual_decoder import decode_individual
from src.core.types import SchedulingContext
from src.core.ga_scheduler import GAScheduler, GAConfig
from src.validation import validate_input
from src.workflows.reporting import generate_reports
from src.utils.console import write_header, write_separator, write_info
from config.constraints import HARD_CONSTRAINTS_CONFIG, SOFT_CONSTRAINTS_CONFIG


def run_standard_workflow(
    pop_size: int,
    generations: int,
    crossover_prob: float = 0.7,
    mutation_prob: float = 0.2,
    data_dir: str = "data",
    output_dir: Optional[str] = None,
    seed: int = 69,
    validate: bool = True,
) -> Dict:
    """
    Execute standard GA scheduling workflow.

    Pipeline:
        1. Initialize RNG and output directory
        2. Load input data from JSON files
        3. Validate input data (optional)
        4. Setup and run GA scheduler
        5. Decode best solution
        6. Generate reports and exports

    Args:
        pop_size: Population size for GA
        generations: Number of GA generations
        crossover_prob: Crossover probability (0.0-1.0)
        mutation_prob: Mutation probability (0.0-1.0)
        data_dir: Directory containing input JSON files
        output_dir: Output directory (auto-generated if None)
        seed: Random seed for reproducibility
        validate: Whether to validate input before running GA

    Returns:
        Dict containing:
            - best_individual: Best GA solution
            - decoded_schedule: List of CourseSession objects
            - metrics: GAMetrics with evolution data
            - output_path: Path to output directory
            - qts: QuantumTimeSystem instance

    Raises:
        ValueError: If input validation fails
    """

    # ========================================
    # Step 1: Initialize
    # ========================================
    write_header("SCHEDULE ENGINE - Standard Workflow")
    tqdm.write("")

    # Set random seed
    random.seed(seed)
    write_info(f"Random seed: {seed}")

    # Create output directory
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", f"evaluation_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    write_info(f"Output directory: {output_dir}")
    tqdm.write("")

    # ========================================
    # Step 2: Load Data
    # ========================================
    with tqdm(
        total=5,
        desc="📥 Loading Input Data",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    ) as pbar:
        qts, context = load_input_data(data_dir)
        pbar.update(5)

    write_info(f"   Courses: {len(context.courses)}")
    write_info(f"   Groups: {len(context.groups)}")
    write_info(f"   Instructors: {len(context.instructors)}")
    write_info(f"   Rooms: {len(context.rooms)}")
    write_info(f"   Time quanta: {len(context.available_quanta)}")
    tqdm.write("")

    # ========================================
    # Step 3: Validate (Optional)
    # ========================================
    if validate:
        with tqdm(
            total=1, desc="✓ Validating Input", bar_format="{l_bar}{bar}| {elapsed}"
        ) as pbar:
            validation_result = validate_input(context, strict=False)
            pbar.update(1)

        if not validation_result:
            raise ValueError(
                "❌ Input validation failed with ERRORS! Fix errors and try again."
            )

        tqdm.write("   ✓ Input validation passed\n")

    # ========================================
    # Step 4: Configure GA
    # ========================================
    ga_config = GAConfig(
        pop_size=pop_size,
        generations=generations,
        crossover_prob=crossover_prob,
        mutation_prob=mutation_prob,
    )

    # Get enabled constraint names
    hard_names = [
        name for name, cfg in HARD_CONSTRAINTS_CONFIG.items() if cfg["enabled"]
    ]
    soft_names = [
        name for name, cfg in SOFT_CONSTRAINTS_CONFIG.items() if cfg["enabled"]
    ]

    tqdm.write("🧬 Genetic Algorithm Configuration:")
    tqdm.write(
        f"   Population: {ga_config.pop_size} | Generations: {ga_config.generations}"
    )
    tqdm.write(
        f"   Crossover: {ga_config.crossover_prob:.1%} | Mutation: {ga_config.mutation_prob:.1%}"
    )
    tqdm.write(f"   Constraints: {len(hard_names)} hard, {len(soft_names)} soft\n")

    # ========================================
    # Step 5: Run GA
    # ========================================
    tqdm.write("🧬 Running Genetic Algorithm...\n")

    scheduler = GAScheduler(ga_config, context, hard_names, soft_names)
    scheduler.setup_toolbox()
    scheduler.initialize_population()
    scheduler.evolve()

    # ========================================
    # Step 6: Decode Best Solution
    # ========================================
    tqdm.write("")
    tqdm.write("Processing Results...")

    best_individual = scheduler.get_best_solution()
    decoded_schedule = decode_individual(
        best_individual,
        context.courses,
        context.instructors,
        context.groups,
        context.rooms,
    )

    write_info(f"   Hard Violations: {best_individual.fitness.values[0]:.0f}")
    write_info(f"   Soft Penalty: {best_individual.fitness.values[1]:.2f}")
    write_info(f"   Schedule sessions: {len(decoded_schedule)}")
    tqdm.write("")

    # ========================================
    # Step 7: Generate Reports
    # ========================================
    with tqdm(
        total=1, desc="📊 Generating Reports", bar_format="{l_bar}{bar}| {elapsed}"
    ) as pbar:
        generate_reports(
            decoded_schedule=decoded_schedule,
            metrics=scheduler.metrics,
            population=scheduler.population,
            qts=qts,
            output_dir=output_dir,
            course_map=context.courses,
        )
        pbar.update(1)

    # ========================================
    # Done!
    # ========================================
    write_header("WORKFLOW COMPLETE")
    write_info(f"Results saved to: {output_dir}")
    write_info(f"   - schedule.json: Schedule data")
    write_info(f"   - schedule.pdf: Visual calendar")
    write_info(f"   - plots/: Evolution charts")
    write_separator()
    tqdm.write("")

    return {
        "best_individual": best_individual,
        "decoded_schedule": decoded_schedule,
        "metrics": scheduler.metrics,
        "output_path": output_dir,
        "qts": qts,
    }


def load_input_data(data_dir: str) -> tuple[QuantumTimeSystem, SchedulingContext]:
    """
    Load and link all input entities.

    Only includes courses that are enrolled by at least one group,
    filtering out the rest of the university course database.

    Args:
        data_dir: Directory containing input JSON files

    Returns:
        Tuple of (QuantumTimeSystem, SchedulingContext)
    """
    # Initialize time system
    qts = QuantumTimeSystem()

    # Step 1: Load groups first to know which course codes are enrolled
    groups = load_groups(os.path.join(data_dir, "Groups.json"), qts)

    # Step 2: Collect all enrolled course codes from groups
    enrolled_course_codes = set()
    for group in groups.values():
        enrolled_course_codes.update(group.enrolled_courses)

    print(
        f"[INFO] Found {len(enrolled_course_codes)} unique course codes enrolled by groups"
    )

    # Step 3: Load ALL courses from database
    all_courses = load_courses(os.path.join(data_dir, "Course.json"))

    # Step 4: Filter to only keep courses whose course_code is enrolled
    # Note: Dict keyed by (course_code, course_type) tuples
    # A single course_code may have both theory and practical versions
    courses = {}
    for course_key, course in all_courses.items():
        # course_key is (course_code, course_type)
        course_code = course_key[0]
        if course_code in enrolled_course_codes:
            courses[course_key] = course

    excluded_count = len(all_courses) - len(courses)
    print(
        f"[INFO] Filtered {len(courses)} course objects from {len(all_courses)} total in database"
    )
    print(f"[INFO] ({excluded_count} courses excluded - not enrolled by any group)")

    # Step 5: Load other entities
    instructors = load_instructors(os.path.join(data_dir, "Instructors.json"), qts)
    rooms = load_rooms(os.path.join(data_dir, "Rooms.json"), qts)

    # Step 6: Link relationships (only for enrolled courses)
    link_courses_and_groups(courses, groups)
    link_courses_and_instructors(courses, instructors)

    # Create context with filtered courses
    context = SchedulingContext(
        courses=courses,
        groups=groups,
        instructors=instructors,
        rooms=rooms,
        available_quanta=qts.get_all_operating_quanta(),
    )

    return qts, context
