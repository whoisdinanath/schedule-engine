"""
Enhanced Evolution Statistics Tracking Module

This module provides comprehensive tracking of GA evolution statistics
including constraint violations, diversity metrics, and convergence analysis.
"""

from typing import Dict, List, Any, Optional
import numpy as np
from dataclasses import dataclass
from src.ga_deap.sessiongene import SessionGene
from src.constraints.checker import check_all_constraints


@dataclass
class GenerationStats:
    """Statistics for a single generation."""

    generation: int
    best_fitness: float
    avg_fitness: float
    worst_fitness: float
    std_fitness: float
    hard_violations: int
    soft_violations: int
    diversity_score: float
    convergence_rate: float
    time_elapsed: float


class EvolutionTracker:
    """Comprehensive evolution tracking system."""

    def __init__(self):
        self.generation_stats: List[GenerationStats] = []
        self.constraint_history: List[Dict[str, int]] = []
        self.diversity_history: List[float] = []
        self.convergence_history: List[float] = []
        self.stagnation_counter = 0
        self.last_best_fitness = None

    def track_generation(
        self,
        population: List[SessionGene],
        generation: int,
        qts,
        courses,
        instructors,
        groups,
        rooms,
        time_elapsed: float,
    ):
        """Track statistics for a generation."""

        # Basic fitness statistics
        fitnesses = [ind.fitness.values[0] for ind in population]
        best_fitness = max(fitnesses)
        avg_fitness = np.mean(fitnesses)
        worst_fitness = min(fitnesses)
        std_fitness = np.std(fitnesses)

        # Constraint violations for best individual
        best_individual = max(population, key=lambda x: x.fitness.values[0])
        violations = check_all_constraints(
            best_individual, qts, courses, instructors, groups, rooms
        )
        hard_violations = sum(v for k, v in violations.items() if "hard" in k)
        soft_violations = sum(v for k, v in violations.items() if "soft" in k)

        # Diversity calculation
        diversity_score = self._calculate_diversity(population)

        # Convergence rate
        convergence_rate = self._calculate_convergence_rate(best_fitness)

        # Store statistics
        stats = GenerationStats(
            generation=generation,
            best_fitness=best_fitness,
            avg_fitness=avg_fitness,
            worst_fitness=worst_fitness,
            std_fitness=std_fitness,
            hard_violations=hard_violations,
            soft_violations=soft_violations,
            diversity_score=diversity_score,
            convergence_rate=convergence_rate,
            time_elapsed=time_elapsed,
        )

        self.generation_stats.append(stats)
        self.constraint_history.append(violations)
        self.diversity_history.append(diversity_score)
        self.convergence_history.append(convergence_rate)

        # Update stagnation counter
        if self.last_best_fitness is None or best_fitness > self.last_best_fitness:
            self.stagnation_counter = 0
        else:
            self.stagnation_counter += 1

        self.last_best_fitness = best_fitness

    def _calculate_diversity(self, population: List[SessionGene]) -> float:
        """Calculate population diversity using fitness variance."""
        fitnesses = [ind.fitness.values[0] for ind in population]
        return np.std(fitnesses) / (np.mean(fitnesses) + 1e-10)

    def _calculate_convergence_rate(self, current_fitness: float) -> float:
        """Calculate convergence rate based on fitness improvement."""
        if len(self.generation_stats) < 2:
            return 0.0

        last_fitness = self.generation_stats[-1].best_fitness
        return (current_fitness - last_fitness) / (last_fitness + 1e-10)

    def get_convergence_analysis(self) -> Dict[str, Any]:
        """Get comprehensive convergence analysis."""
        if not self.generation_stats:
            return {}

        return {
            "total_generations": len(self.generation_stats),
            "final_fitness": self.generation_stats[-1].best_fitness,
            "initial_fitness": self.generation_stats[0].best_fitness,
            "total_improvement": self.generation_stats[-1].best_fitness
            - self.generation_stats[0].best_fitness,
            "stagnation_generations": self.stagnation_counter,
            "avg_convergence_rate": np.mean(self.convergence_history),
            "avg_diversity": np.mean(self.diversity_history),
            "final_hard_violations": self.generation_stats[-1].hard_violations,
            "final_soft_violations": self.generation_stats[-1].soft_violations,
            "premature_convergence": self.stagnation_counter > 20,
            "solution_quality": (
                "excellent"
                if self.generation_stats[-1].hard_violations == 0
                else "poor"
            ),
        }
