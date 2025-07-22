"""
Enhanced Population Management with Diversity Control and Adaptive Strategies
Provides advanced population initialization, diversity management, and adaptive evolution strategies.
"""

import random
import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Set
from collections import defaultdict
from dataclasses import dataclass

from .sessiongene import SessionGene
from .enhanced_operators import AdaptiveGeneticOperators
from .enhanced_fitness_evaluator import EnhancedFitnessEvaluator
from src.encoders import QuantumTimeSystem


@dataclass
class PopulationConfig:
    """Configuration for population management"""

    population_size: int = 100
    elitism_rate: float = 0.1
    diversity_threshold: float = 0.3
    stagnation_limit: int = 10
    injection_rate: float = 0.1


@dataclass
class PopulationStats:
    """Statistics about population state"""

    generation: int
    diversity: float
    average_fitness: float
    best_fitness: float
    stagnation_count: int
    mutation_rate: float
    crossover_rate: float


class EnhancedPopulationManager:
    """
    Enhanced population management with diversity control and adaptive strategies.
    """

    def __init__(
        self,
        config: Any,
        fitness_evaluator: EnhancedFitnessEvaluator,
        genetic_operators: AdaptiveGeneticOperators,
    ):
        self.config = config
        self.fitness_evaluator = fitness_evaluator
        self.genetic_operators = genetic_operators

        # Population state
        self.population: List[List[SessionGene]] = []
        self.fitness_scores: List[float] = []
        self.generation = 0

        # Evolution tracking
        self.diversity_history: List[float] = []
        self.fitness_history: List[float] = []
        self.stagnation_count = 0
        self.best_fitness = float("-inf")
        self.best_individual: Optional[List[SessionGene]] = None

        # Diversity management
        self.diversity_threshold = getattr(config.ga_config, "diversity_threshold", 0.3)
        self.stagnation_limit = getattr(config.ga_config, "stagnation_limit", 10)

        # Performance tracking
        self.generation_times: List[float] = []
        self.evaluation_count = 0

    def initialize_population(
        self,
        qts: QuantumTimeSystem,
        courses: List[Any],  # Course objects
        instructors: List[Any],  # Instructor objects
        groups: List[Any],  # Group objects
        rooms: List[Any],  # Room objects
    ) -> None:
        """Initialize population with diverse individuals"""
        # Store data for later use
        self.qts = qts
        self.courses_dict = {c.course_id: c for c in courses}
        self.instructors_dict = {i.instructor_id: i for i in instructors}
        self.groups_dict = {g.group_id: g for g in groups}
        self.rooms_dict = {r.room_id: r for r in rooms}

        self.population = []

        # Generate diverse initial population
        for i in range(self.config.ga_config.population_size):
            strategy = self._select_initialization_strategy(i)
            individual = self._generate_individual(
                strategy, qts, courses, instructors, groups, rooms
            )
            self.population.append(individual)

        # Evaluate initial population
        self._evaluate_population()

        # Track diversity
        diversity = self.genetic_operators.calculate_diversity(self.population)
        self.diversity_history.append(diversity)

    def _select_initialization_strategy(self, index: int) -> str:
        """Select initialization strategy for individual"""
        strategies = ["random", "greedy", "diversity_focused"]
        if index < len(strategies):
            return strategies[index]
        return random.choice(strategies)

    def _generate_individual(
        self,
        strategy: str,
        qts: QuantumTimeSystem,
        courses: List[Any],  # Course objects
        instructors: List[Any],  # Instructor objects
        groups: List[Any],  # Group objects
        rooms: List[Any],  # Room objects
    ) -> List[SessionGene]:
        """Generate individual using specified strategy"""
        if strategy == "greedy":
            return self._generate_greedy_individual(
                qts, courses, instructors, groups, rooms
            )
        elif strategy == "diversity_focused":
            return self._generate_diversity_focused_individual(
                qts, courses, instructors, groups, rooms
            )
        else:
            return self._generate_random_individual(
                qts, courses, instructors, groups, rooms
            )

    def _generate_random_individual(
        self,
        qts: QuantumTimeSystem,
        courses: List[Any],  # Course objects
        instructors: List[Any],  # Instructor objects
        groups: List[Any],  # Group objects
        rooms: List[Any],  # Room objects
    ) -> List[SessionGene]:
        """Generate random individual"""
        individual = []
        for course in courses:
            # Handle Course objects
            sessions_needed = getattr(course, "quanta_per_week", 1)
            course_id = course.course_id

            for _ in range(sessions_needed):
                # Find qualified instructor
                qualified_instructors = [
                    i
                    for i in instructors
                    if hasattr(i, "qualified_courses")
                    and course_id in i.qualified_courses
                ]
                if not qualified_instructors:
                    qualified_instructors = instructors  # Fallback to any instructor

                # Find enrolled groups
                enrolled_groups = [
                    g
                    for g in groups
                    if hasattr(g, "enrolled_courses")
                    and course_id in g.enrolled_courses
                ]
                if not enrolled_groups:
                    enrolled_groups = groups  # Fallback to any group

                # Select random assignments
                instructor = random.choice(qualified_instructors)
                group = random.choice(enrolled_groups)
                room = random.choice(rooms)

                # Random time slot
                available_quanta = list(range(qts.TOTAL_WEEKLY_QUANTA))
                quantum = random.choice(available_quanta)

                session = SessionGene(
                    course_id=course_id,
                    instructor_id=instructor.instructor_id,
                    group_id=group.group_id,
                    room_id=room.room_id,
                    quanta=[quantum],
                )
                individual.append(session)

        return individual

    def _generate_greedy_individual(
        self,
        qts: QuantumTimeSystem,
        courses: List[Any],  # Course objects
        instructors: List[Any],  # Instructor objects
        groups: List[Any],  # Group objects
        rooms: List[Any],  # Room objects
    ) -> List[SessionGene]:
        """Generate greedy individual prioritizing constraints"""
        # For now, use random generation
        # TODO: Implement actual greedy heuristic
        return self._generate_random_individual(
            qts, courses, instructors, groups, rooms
        )

    def _generate_diversity_focused_individual(
        self,
        qts: QuantumTimeSystem,
        courses: List[Any],  # Course objects
        instructors: List[Any],  # Instructor objects
        groups: List[Any],  # Group objects
        rooms: List[Any],  # Room objects
    ) -> List[SessionGene]:
        """Generate individual focused on diversity"""
        # For now, use random generation
        # TODO: Implement diversity-focused heuristic
        return self._generate_random_individual(
            qts, courses, instructors, groups, rooms
        )

    def evolve_generation(
        self,
        qts: QuantumTimeSystem,
        courses: List[Any],  # Course objects
        instructors: List[Any],  # Instructor objects
        groups: List[Any],  # Group objects
        rooms: List[Any],  # Room objects
    ) -> Dict[str, Any]:
        """Evolve one generation"""
        self.generation += 1

        # Calculate diversity
        diversity = self.genetic_operators.calculate_diversity(self.population)
        self.diversity_history.append(diversity)

        # Create new population
        new_population = []

        # Elitism - keep best individuals
        elitism_rate = getattr(self.config.ga_config, "elitism_rate", 0.1)
        elite_size = max(1, int(self.config.ga_config.population_size * elitism_rate))
        elite_indices = np.argsort(self.fitness_scores)[-elite_size:]
        elite_individuals = [self.population[i] for i in elite_indices]
        new_population.extend(elite_individuals)

        # Generate offspring
        while len(new_population) < self.config.ga_config.population_size:
            # Select parents using tournament selection
            parents = self.genetic_operators.tournament_selection(
                self.population, self.fitness_scores, 2
            )
            parent1, parent2 = parents[0], parents[1]

            # Crossover
            offspring1, offspring2 = self.genetic_operators.enhanced_crossover(
                parent1,
                parent2,
                qts,
                self.courses_dict,
                self.instructors_dict,
                self.groups_dict,
                self.rooms_dict,
            )

            # Mutation
            offspring1 = self.genetic_operators.adaptive_mutation(
                offspring1,
                qts,
                self.courses_dict,
                self.instructors_dict,
                self.groups_dict,
                self.rooms_dict,
            )
            offspring2 = self.genetic_operators.adaptive_mutation(
                offspring2,
                qts,
                self.courses_dict,
                self.instructors_dict,
                self.groups_dict,
                self.rooms_dict,
            )

            new_population.extend([offspring1, offspring2])

        # Trim to exact size
        new_population = new_population[: self.config.ga_config.population_size]

        # Update population
        self.population = new_population
        self._evaluate_population()

        # Update best solution
        current_best_fitness = max(self.fitness_scores)
        if current_best_fitness > self.best_fitness:
            self.best_fitness = current_best_fitness
            best_idx = self.fitness_scores.index(current_best_fitness)
            self.best_individual = self.population[best_idx].copy()
            self.stagnation_count = 0
        else:
            self.stagnation_count += 1

        # Track fitness history
        self.fitness_history.append(current_best_fitness)

        # Return generation statistics
        return {
            "generation": self.generation,
            "best_fitness": current_best_fitness,
            "avg_fitness": np.mean(self.fitness_scores),
            "diversity": diversity,
            "stagnation_count": self.stagnation_count,
            "population_size": len(self.population),
        }

    def _evaluate_population(self) -> None:
        """Evaluate fitness of entire population"""
        self.fitness_scores = []
        for individual in self.population:
            fitness, breakdown = self.fitness_evaluator.evaluate_individual(
                individual,
                self.qts,
                self.courses_dict,
                self.instructors_dict,
                self.groups_dict,
                self.rooms_dict,
            )
            self.fitness_scores.append(fitness)
            self.evaluation_count += 1

    def get_best_individual(self) -> Tuple[List[SessionGene], float]:
        """Get best individual and fitness"""
        if self.best_individual is not None:
            return self.best_individual, self.best_fitness

        # Fallback to current best
        if self.fitness_scores:
            best_idx = self.fitness_scores.index(max(self.fitness_scores))
            return self.population[best_idx], self.fitness_scores[best_idx]

        return [], 0.0

    def check_convergence(self) -> bool:
        """Check if population has converged"""
        return self.stagnation_count >= self.stagnation_limit

    def get_statistics(self) -> Dict[str, Any]:
        """Get population statistics"""
        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "evaluations": self.evaluation_count,
            "diversity_history": self.diversity_history,
            "fitness_history": self.fitness_history,
            "stagnation_count": self.stagnation_count,
            "best_fitness": self.best_fitness,
            "convergence": self.check_convergence(),
        }

    def get_diversity_stats(self) -> Dict[str, float]:
        """Get diversity statistics"""
        if not self.diversity_history:
            return {"current": 0.0, "average": 0.0, "trend": 0.0}

        current = self.diversity_history[-1]
        average = np.mean(self.diversity_history)
        trend = (
            (current - self.diversity_history[0]) / len(self.diversity_history)
            if len(self.diversity_history) > 1
            else 0.0
        )

        return {
            "current": current,
            "average": average,
            "trend": trend,
            "history": self.diversity_history,
        }

    def apply_diversity_control(self) -> None:
        """Apply diversity control mechanisms"""
        if not self.diversity_history:
            return

        current_diversity = self.diversity_history[-1]

        # If diversity is too low, inject new individuals
        if current_diversity < self.diversity_threshold:
            self._inject_diverse_individuals()

        # Adjust genetic operators
        self.genetic_operators.update_parameters(
            diversity=current_diversity, stagnation=self.stagnation_count
        )

    def _inject_diverse_individuals(self) -> None:
        """Inject diverse individuals to maintain diversity"""
        # Replace worst individuals with new diverse ones
        injection_rate = getattr(self.config.ga_config, "injection_rate", 0.1)
        replacement_count = max(
            1, int(self.config.ga_config.population_size * injection_rate)
        )

        # Find worst individuals
        worst_indices = np.argsort(self.fitness_scores)[:replacement_count]

        # Generate new diverse individuals
        # For now, just generate random individuals
        # TODO: Implement actual diversity-based generation
        for idx in worst_indices:
            # This would need the parameters that were passed to initialization
            # For now, just mutate existing individuals heavily
            self.population[idx] = self.genetic_operators.adaptive_mutation(
                self.population[idx], None, None, None, None, None, intensity=2.0
            )

    def reset_for_new_run(self) -> None:
        """Reset manager for new optimization run"""
        self.population = []
        self.fitness_scores = []
        self.generation = 0
        self.diversity_history = []
        self.fitness_history = []
        self.stagnation_count = 0
        self.best_fitness = float("-inf")
        self.best_individual = None
        self.generation_times = []
        self.evaluation_count = 0
