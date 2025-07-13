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

    toolbox.register("evaluate", dummy_fitness)  # Replace this!
    toolbox.register("mate", custom_crossover)
    toolbox.register("mutate", custom_mutation, qts_max_quanta=qts.TOTAL_WEEKLY_QUANTA)
    toolbox.register("select", tools.selTournament, tournsize=3)

    population = toolbox.population(n=pop_size)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", lambda x: sum(f[0] for f in x) / len(x))
    stats.register("min", lambda x: min(f[0] for f in x))
    stats.register("max", lambda x: max(f[0] for f in x))

    population, logbook = algorithms.eaSimple(
        population, toolbox, cxpb=0.9, mutpb=0.1, ngen=ngen, stats=stats, verbose=True
    )

    best = tools.selBest(population, 1)[0]
    return best


def dummy_fitness(individual):
    """
    Dummy fitness function for testing.
    Replace with actual constraint penalty system.
    """
    return (len(set(ind[0] for ind in individual)),)  # just number of unique time slots
