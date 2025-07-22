"""
Enhanced Genetic Operators for Improved Timetabling Performance
Provides advanced selection, crossover, and mutation operators with adaptive mechanisms.
"""

import random
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from deap import tools
from collections import defaultdict
from dataclasses import dataclass

from .sessiongene import SessionGene
from src.encoders import QuantumTimeSystem
from src.entities import Course, Instructor, Group, Room


@dataclass
class OperatorConfig:
    """Configuration for genetic operators"""

    crossover_rate: float = 0.8
    mutation_rate: float = 0.1
    tournament_size: int = 3
    elite_size: int = 5
    adaptive_parameters: bool = True


class AdaptiveGeneticOperators:
    """
    Advanced genetic operators with adaptive mechanisms for better performance.
    """

    def __init__(self, config: OperatorConfig = None):
        self.config = config or OperatorConfig()
        self.generation = 0
        self.performance_history = []
        self.stagnation_count = 0
        self.best_fitness_history = []

    def update_generation(self, generation: int, best_fitness: float):
        """Update generation statistics for adaptive behavior"""
        self.generation = generation
        self.best_fitness_history.append(best_fitness)

        # Check for stagnation
        if len(self.best_fitness_history) > 10:
            recent_best = self.best_fitness_history[-10:]
            if max(recent_best) - min(recent_best) < 0.01:
                self.stagnation_count += 1
            else:
                self.stagnation_count = 0

        # Adapt parameters based on performance
        if self.config.adaptive_parameters:
            self._adapt_parameters()

    def _adapt_parameters(self):
        """Adapt operator parameters based on evolution progress"""
        progress = min(self.generation / 100.0, 1.0)

        # Adaptive mutation rate
        if self.stagnation_count > 5:
            # Increase mutation when stagnating
            self.config.mutation_rate = min(0.3, self.config.mutation_rate * 1.2)
        elif self.stagnation_count == 0:
            # Decrease mutation when improving
            self.config.mutation_rate = max(0.05, self.config.mutation_rate * 0.95)

        # Adaptive tournament size
        # Increase selection pressure in later generations
        base_tournament = 3
        self.config.tournament_size = int(base_tournament + progress * 7)

    def tournament_selection(
        self, population: List, fitness_scores: List[float], selection_size: int
    ) -> List:
        """
        Enhanced tournament selection with adaptive tournament size.
        """
        selected = []

        for _ in range(selection_size):
            # Select tournament participants
            tournament_size = min(self.config.tournament_size, len(population))
            tournament_indices = random.sample(range(len(population)), tournament_size)

            # Find best individual in tournament
            best_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
            selected.append(population[best_idx])

        return selected

    def enhanced_crossover(
        self,
        parent1: List[SessionGene],
        parent2: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> Tuple[List[SessionGene], List[SessionGene]]:
        """
        Enhanced crossover that preserves feasible sessions and promotes diversity.
        """
        if random.random() > self.config.crossover_rate:
            return parent1[:], parent2[:]

        # Use different crossover strategies based on generation
        if self.generation < 20:
            # Early generations: use simple crossover for exploration
            return self._simple_crossover(parent1, parent2)
        else:
            # Later generations: use smart crossover for exploitation
            return self._smart_crossover(
                parent1, parent2, qts, courses, instructors, groups, rooms
            )

    def _simple_crossover(
        self, parent1: List[SessionGene], parent2: List[SessionGene]
    ) -> Tuple[List[SessionGene], List[SessionGene]]:
        """Simple one-point crossover"""
        if len(parent1) < 2 or len(parent2) < 2:
            return parent1[:], parent2[:]

        # Single crossover point
        crossover_point = random.randint(1, min(len(parent1), len(parent2)) - 1)

        offspring1 = parent1[:crossover_point] + parent2[crossover_point:]
        offspring2 = parent2[:crossover_point] + parent1[crossover_point:]

        return offspring1, offspring2

    def _smart_crossover(
        self,
        parent1: List[SessionGene],
        parent2: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> Tuple[List[SessionGene], List[SessionGene]]:
        """
        Smart crossover that preserves good scheduling patterns.
        """
        # Group sessions by course for better recombination
        p1_courses = defaultdict(list)
        p2_courses = defaultdict(list)

        for session in parent1:
            p1_courses[session.course_id].append(session)

        for session in parent2:
            p2_courses[session.course_id].append(session)

        # Create offspring by mixing course schedules
        offspring1, offspring2 = [], []

        all_courses = set(p1_courses.keys()) | set(p2_courses.keys())

        for course_id in all_courses:
            # Randomly choose which parent contributes sessions for this course
            if random.random() < 0.5:
                # Parent 1 contributes to offspring 1, parent 2 to offspring 2
                offspring1.extend(p1_courses.get(course_id, []))
                offspring2.extend(p2_courses.get(course_id, []))
            else:
                # Parent 2 contributes to offspring 1, parent 1 to offspring 2
                offspring1.extend(p2_courses.get(course_id, []))
                offspring2.extend(p1_courses.get(course_id, []))

        return offspring1, offspring2

    def adaptive_mutation(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> List[SessionGene]:
        """
        Adaptive mutation with multiple mutation strategies.
        """
        mutated = individual[:]

        # Different mutation strategies based on generation and stagnation
        if self.stagnation_count > 10:
            # Heavy mutation for escaping local optima
            mutation_rate = min(0.5, self.config.mutation_rate * 2)
            mutated = self._heavy_mutation(
                mutated, qts, courses, instructors, groups, rooms, mutation_rate
            )
        elif self.generation < 20:
            # Standard mutation for exploration
            mutated = self._standard_mutation(
                mutated, qts, courses, instructors, groups, rooms
            )
        else:
            # Fine-tuning mutation for exploitation
            mutated = self._fine_tuning_mutation(
                mutated, qts, courses, instructors, groups, rooms
            )

        return mutated

    def _standard_mutation(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> List[SessionGene]:
        """Standard mutation operator"""
        for session in individual:
            if random.random() < self.config.mutation_rate:
                # Choose mutation type
                mutation_type = random.choice(["time", "room", "instructor"])

                if mutation_type == "time":
                    self._mutate_time(session, qts, courses, instructors, groups, rooms)
                elif mutation_type == "room":
                    self._mutate_room(session, courses, rooms)
                elif mutation_type == "instructor":
                    self._mutate_instructor(session, courses, instructors)

        return individual

    def _heavy_mutation(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
        mutation_rate: float,
    ) -> List[SessionGene]:
        """Heavy mutation for escaping local optima"""
        for session in individual:
            if random.random() < mutation_rate:
                # Mutate multiple attributes
                self._mutate_time(session, qts, courses, instructors, groups, rooms)
                if random.random() < 0.5:
                    self._mutate_room(session, courses, rooms)
                if random.random() < 0.5:
                    self._mutate_instructor(session, courses, instructors)

        return individual

    def _fine_tuning_mutation(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> List[SessionGene]:
        """Fine-tuning mutation for local optimization"""
        # Lower mutation rate for fine-tuning
        fine_mutation_rate = self.config.mutation_rate * 0.5

        for session in individual:
            if random.random() < fine_mutation_rate:
                # Prefer time slot adjustments for fine-tuning
                if random.random() < 0.7:
                    self._mutate_time_locally(
                        session, qts, courses, instructors, groups, rooms
                    )
                else:
                    self._mutate_room(session, courses, rooms)

        return individual

    def _mutate_time(
        self,
        session: SessionGene,
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ):
        """Mutate time slot of a session"""
        course = courses[session.course_id]
        instructor = instructors[session.instructor_id]
        group = groups[session.group_id]
        room = rooms[session.room_id]

        # Find available time slots
        instructor_quanta = (
            instructor.available_quanta
            if not instructor.is_full_time
            else qts.get_all_operating_quanta()
        )
        valid_quanta = (
            group.available_quanta & instructor_quanta & room.available_quanta
        )

        if valid_quanta:
            new_quantum = random.choice(list(valid_quanta))
            session.quanta = [new_quantum]

    def _mutate_time_locally(
        self,
        session: SessionGene,
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ):
        """Mutate time slot to nearby slots (for fine-tuning)"""
        if not session.quanta:
            return

        current_quantum = session.quanta[0]

        # Try nearby time slots (±2 quanta)
        nearby_quanta = []
        for offset in [-2, -1, 1, 2]:
            candidate = current_quantum + offset
            if candidate >= 0 and candidate < qts.get_total_quanta():
                nearby_quanta.append(candidate)

        if nearby_quanta:
            course = courses[session.course_id]
            instructor = instructors[session.instructor_id]
            group = groups[session.group_id]
            room = rooms[session.room_id]

            instructor_quanta = (
                instructor.available_quanta
                if not instructor.is_full_time
                else qts.get_all_operating_quanta()
            )
            valid_nearby = (
                set(nearby_quanta)
                & group.available_quanta
                & instructor_quanta
                & room.available_quanta
            )

            if valid_nearby:
                new_quantum = random.choice(list(valid_nearby))
                session.quanta = [new_quantum]

    def _mutate_room(
        self, session: SessionGene, courses: Dict[str, Course], rooms: Dict[str, Room]
    ):
        """Mutate room assignment"""
        course = courses[session.course_id]
        suitable_rooms = [
            r
            for r in rooms.values()
            if r.is_suitable_for_course_type(course.required_room_features)
        ]

        if suitable_rooms:
            new_room = random.choice(suitable_rooms)
            session.room_id = new_room.room_id

    def _mutate_instructor(
        self,
        session: SessionGene,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
    ):
        """Mutate instructor assignment"""
        course = courses[session.course_id]
        if course.qualified_instructor_ids:
            new_instructor_id = random.choice(course.qualified_instructor_ids)
            session.instructor_id = new_instructor_id

    def elitism_selection(self, population: List, fitness_scores: List[float]) -> List:
        """Select elite individuals for next generation"""
        elite_indices = sorted(
            range(len(fitness_scores)), key=lambda i: fitness_scores[i], reverse=True
        )[: self.config.elite_size]
        return [population[i] for i in elite_indices]

    def calculate_diversity(self, population: List[List[SessionGene]]) -> float:
        """Calculate population diversity based on different scheduling patterns"""
        if len(population) < 2:
            return 1.0

        # Compare individuals pairwise
        total_comparisons = 0
        total_differences = 0

        for i in range(len(population)):
            for j in range(i + 1, len(population)):
                differences = self._calculate_individual_difference(
                    population[i], population[j]
                )
                total_differences += differences
                total_comparisons += 1

        if total_comparisons == 0:
            return 1.0

        avg_difference = total_differences / total_comparisons
        return min(1.0, avg_difference)

    def _calculate_individual_difference(
        self, ind1: List[SessionGene], ind2: List[SessionGene]
    ) -> float:
        """Calculate difference between two individuals"""
        if len(ind1) != len(ind2):
            return 1.0

        differences = 0
        for s1, s2 in zip(ind1, ind2):
            if s1.course_id != s2.course_id:
                differences += 1
            if s1.instructor_id != s2.instructor_id:
                differences += 0.5
            if s1.room_id != s2.room_id:
                differences += 0.5
            if s1.quanta != s2.quanta:
                differences += 0.5

        return differences / len(ind1)

    def get_statistics(self) -> Dict[str, Any]:
        """Get operator statistics"""
        return {
            "generation": self.generation,
            "stagnation_count": self.stagnation_count,
            "current_mutation_rate": self.config.mutation_rate,
            "current_tournament_size": self.config.tournament_size,
            "best_fitness_trend": (
                self.best_fitness_history[-10:] if self.best_fitness_history else []
            ),
        }
