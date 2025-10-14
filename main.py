import random
import os
from datetime import datetime
from deap import base, tools, algorithms
from tqdm import tqdm

# Entities Import
from src.entities.course import Course
from src.entities.group import Group
from src.entities.instructor import Instructor
from src.entities.room import Room

# Import GA Components and Modules
from src.ga.sessiongene import SessionGene
from src.ga.individual import create_individual
from src.ga.population import generate_course_group_aware_population
from src.ga.operators.crossover import crossover_course_group_aware
from src.ga.operators.mutation import mutate_individual
from src.ga.evaluator.fitness import evaluate  # Fitness Function
from src.ga.evaluator.detailed_fitness import (
    evaluate_detailed,
    evaluate_from_detailed,
)  # Enhanced evaluation


from src.metrics.diversity import average_pairwise_diversity

# Import GA Parameters from config/ga_params.py
from config.ga_params import POP_SIZE, NGEN, CXPB, MUTPB

# Import Decoder and Encoder
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.encoder.input_encoder import (
    load_courses,
    load_groups,
    load_instructors,
    load_rooms,
    link_courses_and_groups,
    link_courses_and_instructors,
)
import json

# Import Exporter : this module containts func to export to json and pdf of generated Schedule
from src.exporter.exporter import export_everything

# Plotting modules
from src.exporter.plotdiversity import plot_diversity_trend
from src.exporter.plothard import plot_hard_constraint_violation_over_generation
from src.exporter.plotpareto import plot_pareto_front
from src.exporter.plotsoft import plot_soft_constraint_violation_over_generation
from src.exporter.plot_detailed_constraints import (
    plot_individual_hard_constraints,
    plot_individual_soft_constraints,
    plot_constraint_summary,
)

# Import Decoder
from src.decoder.individual_decoder import decode_individual
import matplotlib.pyplot as plt

#########################################################1
# Step 0: Create unique output folder per evaluation run
tstamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = os.path.join("output", f"evaluation_{tstamp}")
os.makedirs(output_dir, exist_ok=True)

# 1. Initialite RNG  # Set a seed for reproducibility
random.seed(69)

# 2. init the quantum Time system
qts = QuantumTimeSystem()

# 3. Load Input Data
courses = load_courses("data/Course.json")
groups = load_groups("data/Groups.json", qts)
instructors = load_instructors("data/Instructors.json", qts)
rooms = load_rooms("data/Rooms.json", qts)

link_courses_and_groups(
    courses, groups
)  # Yo muz function alik primitive xa: sudhar garnaparne xa
link_courses_and_instructors(courses, instructors)

# 4. Prepare Context for GA Population Generation and evaluation
context = {
    "courses": courses,
    "instructors": instructors,
    "groups": groups,
    "rooms": rooms,
    "available_quanta": qts.get_all_operating_quanta(),
}

# 5. DEAP Setup
toolbox = base.Toolbox()
toolbox.register(
    "select", tools.selNSGA2
)  # Selector for NSGA-II Multi-objective optimization

toolbox.register(
    "individual", generate_course_group_aware_population, n=1, context=context
)
toolbox.register("population", generate_course_group_aware_population, context=context)

# Fitness Function
toolbox.register(
    "evaluate",
    evaluate,
    courses=courses,
    instructors=instructors,
    groups=groups,
    rooms=rooms,
)

# Genetic Operators
toolbox.register("mate", crossover_course_group_aware, cx_prob=CXPB)
toolbox.register("mutate", mutate_individual, context=context, mut_prob=MUTPB)
# toolbox.register("select", tools.selTournament, tournsize=3) # Not needed for NSGA-II, dont konw why not needed? coz it uses binary tournament selection internally


# 5.5 Add Validation Function for Gene Alignment
def validate_gene_alignment(population):
    """
    Verify all individuals have matching (course, group) at each gene position.

    This validation ensures the position-independent crossover assumption holds:
    all individuals must represent the same set of (course, group) pairs.

    Args:
        population: List of individuals to validate

    Raises:
        ValueError: If any individual has mismatched (course, group) pairs
    """
    if not population:
        return

    # Use first individual as reference
    reference = [
        (gene.course_id, tuple(sorted(gene.group_ids))) for gene in population[0]
    ]
    reference_set = set(reference)

    for idx, individual in enumerate(population[1:], start=1):
        current = [
            (gene.course_id, tuple(sorted(gene.group_ids))) for gene in individual
        ]
        current_set = set(current)

        if current_set != reference_set:
            # Find differences
            missing_in_current = reference_set - current_set
            extra_in_current = current_set - reference_set

            raise ValueError(
                f"❌ Gene alignment validation FAILED!\n"
                f"   Individual {idx} has different (course, group) pairs than Individual 0.\n"
                f"   Individual 0 has {len(reference_set)} unique pairs.\n"
                f"   Individual {idx} has {len(current_set)} unique pairs.\n"
                f"   Missing in Individual {idx}: {missing_in_current}\n"
                f"   Extra in Individual {idx}: {extra_in_current}\n"
                f"   This indicates a bug in population generation or mutation."
            )

        # Also check for duplicates within individual
        if len(current) != len(current_set):
            duplicates = [x for x in current if current.count(x) > 1]
            raise ValueError(
                f"❌ Individual {idx} contains DUPLICATE (course, group) pairs!\n"
                f"   Duplicates: {set(duplicates)}\n"
                f"   This violates the fundamental chromosome structure."
            )


# 6. Create Population

population = toolbox.population(n=POP_SIZE)

# 6.5 Validate Initial Population Structure
print("Validating initial population gene alignment...")
try:
    validate_gene_alignment(population)
    print(
        "Gene alignment verified: All individuals have consistent (course, group) structure"
    )
except ValueError as e:
    print(f"WARNING: Population validation failed!\n{e}")
    print("   Continuing anyway, but crossover may fail...")

# 7.  Evaluate the Initial Population
print("Evaluating initial population...")
fitness = list(
    map(toolbox.evaluate, tqdm(population, desc="Initial Eval", leave=False))
)
for ind, fit in zip(population, fitness):
    ind.fitness.values = fit

# 7.1 Before the GA Loop
hard_trend = []
soft_trend = []
diversity_trend = []

# Enhanced constraint tracking - individual constraint trends
hard_constraint_names = [
    "no_group_overlap",
    "no_instructor_conflict",
    "instructor_not_qualified",
    "room_type_mismatch",
    "availability_violations",
    "incomplete_or_extra_sessions",
]
soft_constraint_names = [
    "group_gaps_penalty",
    "instructor_gaps_penalty",
    "group_midday_break_violation",
    "course_split_penalty",
    "early_or_late_session_penalty",
]

# Initialize detailed tracking dictionaries
hard_trends = {name: [] for name in hard_constraint_names}
soft_trends = {name: [] for name in soft_constraint_names}

# 8. Run GenAlgo
for gin in tqdm(range(NGEN), desc="GA Progress", unit="gen"):
    # print(f"Generation {gin + 1}/{NGEN}")  # tqdm provides this now

    # Generate offspring using NSGA-II selection
    offspring = toolbox.select(population, len(population))
    offspring = list(map(toolbox.clone, offspring))

    # Apply Crossover and Mutation
    for i in range(1, len(offspring), 2):
        if random.random() < CXPB:
            toolbox.mate(offspring[i - 1], offspring[i])
            del offspring[i - 1].fitness.values
            del offspring[i].fitness.values

    for mutant in offspring:
        if random.random() < MUTPB:
            toolbox.mutate(mutant)
            del mutant.fitness.values

    # Evaluate only invalidated individuals
    invalid = [ind for ind in offspring if not ind.fitness.valid]
    fitness = list(
        map(
            toolbox.evaluate,
            tqdm(
                invalid,
                desc=f"Gen {gin+1} Eval",
                leave=False,
                disable=len(invalid) == 0,
            ),
        )
    )
    for ind, fit in zip(invalid, fitness):
        ind.fitness.values = fit

    # Combine parents and offspring, then select next generation
    combined_population = population + offspring
    population[:] = toolbox.select(combined_population, len(population))

    # Periodic validation to catch any gene alignment corruption
    # (Uncomment if you suspect issues with mutation or other operators)
    # if gin % 20 == 0:
    #     try:
    #         validate_gene_alignment(population)
    #     except ValueError as e:
    #         print(f"⚠️  Generation {gin + 1}: Gene alignment corrupted!\n{e}")
    #         break

    # Track Metrics per generation
    hard_trend.append(min(ind.fitness.values[0] for ind in population))
    soft_trend.append(min(ind.fitness.values[1] for ind in population))
    diversity_trend.append(average_pairwise_diversity(population))

    # Track detailed constraints from the best individual
    best = tools.selBest(population, 1)[0]  # Get the best individual
    best_hard_details, best_soft_details = evaluate_detailed(
        best, courses, instructors, groups, rooms
    )

    # Update detailed constraint trends
    for constraint_name in hard_constraint_names:
        hard_trends[constraint_name].append(best_hard_details[constraint_name])

    for constraint_name in soft_constraint_names:
        soft_trends[constraint_name].append(best_soft_details[constraint_name])

    # Log best Fitness (write to tqdm postfix instead of printing)
    tqdm.write(
        f"Gen {gin+1}: Hard={best.fitness.values[0]:.0f}, Soft={best.fitness.values[1]:.2f}"
    )

    # Log detailed constraint breakdown for the best individual
    if gin % 10 == 0 or gin == NGEN - 1:  # Print details every 10 generations
        tqdm.write(f"  [HARD] Total Violations: {best.fitness.values[0]:.0f}")
        for name, value in best_hard_details.items():
            if value > 0:  # Only show violated constraints
                tqdm.write(f"    - {name}: {value}")

        tqdm.write(f"  [SOFT] Total Penalty: {best.fitness.values[1]:.2f}")
        for name, value in best_soft_details.items():
            if value > 0:  # Only show penalties
                tqdm.write(f"    - {name}: {value}")

    # Early stopping if we find a perfect solution
    if best.fitness.values[0] == 0:
        tqdm.write(f"✓ Perfect solution found at generation {gin + 1}!")
        break


# 8.5 Plotting Hard and Soft Constraint Trends Separately

# Plot Hard Constraint violations
plot_hard_constraint_violation_over_generation(hard_trend, output_dir)
# Plot Soft Constraint penalties
plot_soft_constraint_violation_over_generation(soft_trend, output_dir)
# Plot diversity evolution
plot_diversity_trend(diversity_trend, output_dir)
# Plot final Pareto front (enhanced version)
plot_pareto_front(population, output_dir)

# NEW: Plot detailed individual constraints
plot_individual_hard_constraints(hard_trends, output_dir)
plot_individual_soft_constraints(soft_trends, output_dir)
plot_constraint_summary(hard_trends, soft_trends, output_dir)

print(f"Detailed constraint plots saved in {output_dir}/hard/ and {output_dir}/soft/")


# 9 (Aliter): For MOO Multi Objective Optimization: We implement code slot #9 . below
pareto_front = tools.sortNondominated(
    population, len(population), first_front_only=True
)[0]
feasible = [ind for ind in pareto_front if ind.fitness.values[0] == 0]
final_best = (
    min(feasible, key=lambda ind: ind.fitness.values[1])
    if feasible
    else pareto_front[0]
)


# Decode the individual before saving
decoded_schedule = decode_individual(final_best, courses, instructors, groups, rooms)
export_everything(decoded_schedule, output_dir, qts)
print("Fitness: ", final_best.fitness.values[0])
