from deap import tools, algorithms
import random
from src.ga_deap.population import register_individual_classes, setup_toolbox
from src.ga_deap.individual import generate_individual
from src.ga_deap.operators import custom_crossover, custom_mutation


def run_ga(qts, courses, instructors, groups, rooms, ngen=50, pop_size=100):
    """
    Run the genetic algorithm optimization loop.
    """
    register_individual_classes()
    toolbox = setup_toolbox(
        lambda: generate_individual(qts, courses, instructors, groups, rooms)
    )

    toolbox.register(
        "evaluate",
        lambda ind: evaluate_fitness(ind, qts, courses, instructors, groups, rooms),
    )
    toolbox.register("mate", custom_crossover)
    toolbox.register("mutate", custom_mutation, qts_max_quanta=qts.TOTAL_WEEKLY_QUANTA)
    toolbox.register("select", tools.selTournament, tournsize=3)

    population = toolbox.population(n=pop_size)

    # Evaluate the initial population
    for individual in population:
        individual.fitness.values = toolbox.evaluate(individual)

    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda x: sum(f[0] for f in x) / len(x) if x else 0)
    stats.register("min", lambda x: min(f[0] for f in x) if x else 0)
    stats.register("max", lambda x: max(f[0] for f in x) if x else 0)

    population, logbook = algorithms.eaSimple(
        population, toolbox, cxpb=0.9, mutpb=0.1, ngen=ngen, stats=stats, verbose=True
    )

    best = tools.selBest(population, 1)[0]
    return best


def evaluate_fitness(individual, qts, courses, instructors, groups, rooms):
    """
    Comprehensive fitness function that evaluates schedule quality.
    Lower penalty scores indicate better solutions.
    """
    penalty = 0

    # Check for scheduling conflicts
    time_slot_usage = {}
    for session in individual:
        time_slot, room_id, instructor_id = session[0], session[1], session[2]

        key = (time_slot, room_id)
        if key in time_slot_usage:
            penalty += 100  # Room double-booking penalty
        else:
            time_slot_usage[key] = True

        key = (time_slot, instructor_id)
        if key in time_slot_usage:
            penalty += 100  # Instructor double-booking penalty
        else:
            time_slot_usage[key] = True

    # Reward for having more sessions scheduled
    penalty -= len(individual) * 10

    # Prefer lower penalties (better solutions have negative scores)
    return (-penalty,)
