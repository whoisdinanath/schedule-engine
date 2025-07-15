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
    toolbox.register(
        "mutate",
        lambda ind: custom_mutation(
            ind, qts, courses, instructors, groups, rooms, mutation_rate=0.1
        ),
    )
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
    Evaluate the fitness of an individual schedule based on conflicts and qualiy constraints.

    Args:
        individual: List of SessionGene objects
        qts: an instance of QuantumTimeSystem
        courses, instructors, groups, rooms: All relevant entities

    Returns:
        Tuple[float]: Fitness score (negative penalty score)

    Comprehensive fitness function that evaluates schedule quality.
    Lower penalty scores indicate better solutions.
    """
    penalty = 0  # Initialize penalty score
    used_slots = set()
    # (quanta, room/instructor/group) tuples to track used slot and detect the conflicts

    for session in individual:
        course = courses[session.course_id]
        instructor = instructors[session.instructor_id]
        group = groups[session.group_id]
        room = rooms[session.room_id]

        for q in session.quanta:
            # Conflict: Room double-booked
            if (q, session.room_id) in used_slots:
                penalty += 100
            else:
                used_slots.add((q, session.room_id))

            # Conflict: Instructor double-booked
            if (q, session.instructor_id) in used_slots:
                penalty += 100
            else:
                used_slots.add((q, session.instructor_id))

            # Conflict: Group double-booked
            if (q, session.group_id) in used_slots:
                penalty += 100
            else:
                used_slots.add((q, session.group_id))

            # Instructor availability
            if not instructor.is_full_time and q not in instructor.available_quanta:
                penalty += 50

            # Group availability
            if q not in group.available_quanta:
                penalty += 50

            # Room availability
            if q not in room.available_quanta:
                penalty += 50

        # Instructor qualification
        if session.course_id not in instructor.qualified_courses:
            penalty += 100

        # Room suitability
        if not room.is_suitable_for_course_type(course.required_room_features):
            penalty += 50

    # Reward number of sessions correctly scheduled (optional)
    penalty -= len(individual) * 10

    return (-penalty,)
