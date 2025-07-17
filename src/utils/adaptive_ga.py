"""
Adaptive Genetic Algorithm Parameters Module

This module provides dynamic parameter adjustment based on evolution progress,
population diversity, and convergence analysis.
"""

from typing import Dict, Any, Tuple
import numpy as np
from src.utils.config import GA_CONFIG


class AdaptiveParameterController:
    """Controls adaptive adjustment of GA parameters during evolution."""

    def __init__(self, initial_config: Dict[str, Any] = None):
        self.config = initial_config or GA_CONFIG.copy()
        self.initial_config = self.config.copy()
        self.adaptation_history = []

    def adapt_parameters(
        self,
        generation: int,
        diversity: float,
        convergence_rate: float,
        stagnation_count: int,
    ) -> Dict[str, Any]:
        """
        Adapt GA parameters based on evolution state.

        Args:
            generation: Current generation number
            diversity: Population diversity score
            convergence_rate: Rate of fitness improvement
            stagnation_count: Number of generations without improvement

        Returns:
            Updated configuration dictionary
        """

        # Adaptive mutation rate
        if diversity < 0.1:  # Low diversity
            self.config["mutation_rate"] = min(0.5, self.config["mutation_rate"] * 1.2)
        elif diversity > 0.3:  # High diversity
            self.config["mutation_rate"] = max(0.05, self.config["mutation_rate"] * 0.9)

        # Adaptive crossover rate
        if stagnation_count > 10:
            self.config["crossover_rate"] = min(
                0.95, self.config["crossover_rate"] * 1.1
            )
        elif convergence_rate > 0.05:
            self.config["crossover_rate"] = max(
                0.6, self.config["crossover_rate"] * 0.95
            )

        # Adaptive tournament size
        if generation > 50:
            # Increase selection pressure in later generations
            self.config["tournament_size"] = min(
                50, int(self.config["tournament_size"] * 1.05)
            )

        # Adaptive population size (if needed)
        if stagnation_count > 20 and generation < 100:
            # Restart with larger population
            self.config["restart_needed"] = True

        # Log adaptation
        self.adaptation_history.append(
            {
                "generation": generation,
                "mutation_rate": self.config["mutation_rate"],
                "crossover_rate": self.config["crossover_rate"],
                "tournament_size": self.config["tournament_size"],
                "diversity": diversity,
                "stagnation": stagnation_count,
            }
        )

        return self.config.copy()

    def get_adaptation_summary(self) -> Dict[str, Any]:
        """Get summary of parameter adaptations."""
        if not self.adaptation_history:
            return {}

        return {
            "initial_mutation_rate": self.initial_config["mutation_rate"],
            "final_mutation_rate": self.config["mutation_rate"],
            "initial_crossover_rate": self.initial_config["crossover_rate"],
            "final_crossover_rate": self.config["crossover_rate"],
            "initial_tournament_size": self.initial_config["tournament_size"],
            "final_tournament_size": self.config["tournament_size"],
            "total_adaptations": len(self.adaptation_history),
            "restart_triggered": self.config.get("restart_needed", False),
        }


class MultiObjectiveOptimizer:
    """Multi-objective optimization with Pareto ranking."""

    def __init__(self, objectives: List[str]):
        self.objectives = objectives
        self.pareto_fronts = []

    def calculate_pareto_ranking(self, population):
        """Calculate Pareto ranking for multi-objective optimization."""
        # Implementation would go here
        pass

    def crowding_distance(self, front):
        """Calculate crowding distance for diversity preservation."""
        # Implementation would go here
        pass


class HybridEvolutionStrategy:
    """Hybrid strategy combining GA with local search."""

    def __init__(self, local_search_prob: float = 0.1):
        self.local_search_prob = local_search_prob

    def apply_local_search(self, individual, qts, courses, instructors, groups, rooms):
        """Apply local search to improve individual."""
        # Hill climbing or other local optimization
        # This would implement room swapping, time slot adjustments, etc.
        pass

    def adaptive_local_search(self, generation: int, diversity: float):
        """Adapt local search probability based on evolution state."""
        if diversity < 0.05:  # Low diversity
            self.local_search_prob = min(0.3, self.local_search_prob * 1.5)
        else:
            self.local_search_prob = max(0.05, self.local_search_prob * 0.9)

        return self.local_search_prob
