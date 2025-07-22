import random
import os
from datetime import datetime
from deap import base, tools, algorithms
from nbconvert import export

# Entities Import
from src.entities.course import Course
from src.entities.group import Group
from src.entities.instructor import Instructor
from src.entities.room import Room

# Import GA Components and Modules
from src.ga.sessiongene import SessionGene
from src.ga.individual import create_individual
from src.ga.population import generate_population
from src.ga.operators.crossover import crossover_uniform
from src.ga.operators.mutation import mutate_individual
from src.ga.evaluator.fitness import evaluate  # Fitness Function

# Import GA Parameters from config/ga_params.py
from config.ga_params import *

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

# Import Exporter
from src.exporter.exporter import export_everything

# Import Decoder
from src.decoder.individual_decoder import decode_individual

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

link_courses_and_groups(courses, groups)
link_courses_and_instructors(courses, instructors)

# 4. Prepare Context for GA Populaiton Generation and evaluation
context = {
    "courses": courses,
    "instructors": instructors,
    "groups": groups,
    "rooms": rooms,
    "available_quanta": qts.get_all_operating_quanta(),
}

SESSION_COUNT = len(courses)  # Assuming one session per course

# 5. DEAP Setup
toolbox = base.Toolbox()
toolbox.register(
    "individual", generate_population, n=1, session_count=SESSION_COUNT, context=context
)
toolbox.register(
    "population", generate_population, session_count=SESSION_COUNT, context=context
)

# Fitness Function
toolbox.register(
    "evaluate", evaluate, courses=courses, instructors=instructors, groups=groups
)

# Genetic Operators
toolbox.register("mate", crossover_uniform, cx_prob=0.5)
toolbox.register("mutate", mutate_individual, context=context, mut_prob=0.2)
toolbox.register("select", tools.selTournament, tournsize=3)

# 6. Create Population
# These parameters are defined in config/ga_params.py
# POP_SIZE = 500
# NGEN = 30
# CXPB, MUTPB = 0.7, 0.2

population = toolbox.population(n=POP_SIZE)

# 7.  Evaluate the Initial Population
fitness = list(map(toolbox.evaluate, population))
for ind, fit in zip(population, fitness):
    ind.fitness.values = fit

# 8. Run GenAlgo
for gin in range(NGEN):
    print(f"Generation {gin + 1}/{NGEN}")
    # Select next generation
    offspring = toolbox.select(population, len(population))
    offspring = list(map(toolbox.clone, offspring))

    # Apply Crossover and Mutaiton
    for i in range(1, len(offspring), 2):
        if random.random() < CXPB:
            toolbox.mate(offspring[i - 1], offspring[i])
            del offspring[i - 1].fitness.values
            del offspring[i].fitness.values

    for mutant in offspring:
        if random.random() < MUTPB:
            toolbox.mutate(mutant)
            del mutant.fitness.values

    # ReEval the invalidated individuals
    invalid = [ind for ind in offspring if not ind.fitness.valid]
    fitness = list(map(toolbox.evaluate, invalid))
    for ind, fit in zip(invalid, fitness):
        ind.fitness.values = fit

    # Replace the population
    population[:] = offspring

    # Log best Fitness
    best = tools.selBest(population, 1)[0]  # Get the best individual : 0 means first
    print(f"Best Fitness : {best.fitness.values[0]}")

# 9 . Final best solution
final_best = tools.selBest(population, 1)[0]
print("Final Best Individual:")

# Decode the individual before saving
decoded_schedule = decode_individual(final_best, courses, instructors, groups)
export_everything(decoded_schedule, output_dir, qts)
print("Fitness: ", final_best.fitness.values[0])
