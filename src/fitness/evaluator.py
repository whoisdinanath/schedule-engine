"""
Fitness evaluator for the genetic algorithm timetabling system.
Calculates fitness scores for chromosomes based on constraint violations.
"""

from typing import Dict, List, Any, Optional, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..ga.chromosome import Chromosome
from ..entities import Course, Instructor, Room, Group
from ..constraints.checker import ConstraintChecker
from ..utils.logger import get_logger
from ..utils.config import CONSTRAINT_WEIGHTS


class FitnessEvaluator:
    """
    Evaluates fitness of chromosomes based on constraint violations.
    Implements the fitness function F = -α * H - β * S where:
    - H = hard constraint violations
    - S = soft constraint penalties
    - α, β = weights (α >> β)
    """
    
    def __init__(self, parallel_evaluation: bool = False, max_workers: int = 4):
        """
        Initialize the fitness evaluator.
        
        Args:
            parallel_evaluation: Whether to use parallel evaluation
            max_workers: Maximum number of worker threads for parallel evaluation
        """
        self.logger = get_logger(self.__class__.__name__)
        self.constraint_checker = ConstraintChecker()
        self.parallel_evaluation = parallel_evaluation
        self.max_workers = max_workers
        
        # Get fitness weights from configuration
        self.alpha = CONSTRAINT_WEIGHTS['fitness_weights']['hard_constraint_weight']
        self.beta = CONSTRAINT_WEIGHTS['fitness_weights']['soft_constraint_weight']
        self.diversity_bonus = CONSTRAINT_WEIGHTS['fitness_weights']['diversity_bonus']
        
        # Adaptive constraint weights (will be updated dynamically)
        self.adaptive_weights = None
        
        # Statistics
        self.evaluation_count = 0
        self.total_evaluation_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Simple cache for fitness values
        self.fitness_cache = {}
        self.cache_max_size = 1000
    
    def evaluate_chromosome(self,
                          chromosome: Chromosome,
                          courses: Dict[str, Course],
                          instructors: Dict[str, Instructor],
                          rooms: Dict[str, Room],
                          groups: Dict[str, Group],
                          use_cache: bool = True) -> float:
        """
        Evaluate fitness of a single chromosome.
        
        Args:
            chromosome: Chromosome to evaluate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
            use_cache: Whether to use fitness caching
        
        Returns:
            Fitness score (higher is better)
        """
        start_time = time.time()
        
        # Check cache first
        if use_cache and chromosome.fitness_calculated:
            self.cache_hits += 1
            return chromosome.fitness
        
        # Generate cache key
        cache_key = self._generate_cache_key(chromosome) if use_cache else None
        
        if cache_key and cache_key in self.fitness_cache:
            self.cache_hits += 1
            fitness = self.fitness_cache[cache_key]
            chromosome.fitness = fitness
            chromosome.fitness_calculated = True
            return fitness
        
        self.cache_misses += 1
        
        # Evaluate constraints
        hard_violations, soft_penalties = self.constraint_checker.check_all_constraints(
            chromosome, courses, instructors, rooms, groups
        )
        
        # Calculate fitness score
        fitness = self._calculate_fitness(hard_violations, soft_penalties)
        
        # Store in chromosome
        chromosome.fitness = fitness
        chromosome.fitness_calculated = True
        
        # Cache the result
        if cache_key and len(self.fitness_cache) < self.cache_max_size:
            self.fitness_cache[cache_key] = fitness
        
        # Update statistics
        self.evaluation_count += 1
        self.total_evaluation_time += time.time() - start_time
        
        return fitness
    
    def evaluate_population(self,
                          chromosomes: List[Chromosome],
                          courses: Dict[str, Course],
                          instructors: Dict[str, Instructor],
                          rooms: Dict[str, Room],
                          groups: Dict[str, Group]) -> List[float]:
        """
        Evaluate fitness of multiple chromosomes.
        
        Args:
            chromosomes: List of chromosomes to evaluate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            List of fitness scores
        """
        if self.parallel_evaluation and len(chromosomes) > 1:
            return self._evaluate_population_parallel(
                chromosomes, courses, instructors, rooms, groups
            )
        else:
            return self._evaluate_population_sequential(
                chromosomes, courses, instructors, rooms, groups
            )
    
    def _evaluate_population_sequential(self,
                                      chromosomes: List[Chromosome],
                                      courses: Dict[str, Course],
                                      instructors: Dict[str, Instructor],
                                      rooms: Dict[str, Room],
                                      groups: Dict[str, Group]) -> List[float]:
        """Evaluate population sequentially."""
        fitness_scores = []
        
        for chromosome in chromosomes:
            fitness = self.evaluate_chromosome(
                chromosome, courses, instructors, rooms, groups
            )
            fitness_scores.append(fitness)
        
        return fitness_scores
    
    def _evaluate_population_parallel(self,
                                    chromosomes: List[Chromosome],
                                    courses: Dict[str, Course],
                                    instructors: Dict[str, Instructor],
                                    rooms: Dict[str, Room],
                                    groups: Dict[str, Group]) -> List[float]:
        """Evaluate population in parallel."""
        fitness_scores = [0.0] * len(chromosomes)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit evaluation tasks
            future_to_index = {
                executor.submit(
                    self.evaluate_chromosome,
                    chromosome, courses, instructors, rooms, groups
                ): i
                for i, chromosome in enumerate(chromosomes)
            }
            
            # Collect results
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    fitness = future.result()
                    fitness_scores[index] = fitness
                except Exception as e:
                    self.logger.error(f"Error evaluating chromosome {index}: {str(e)}")
                    fitness_scores[index] = float('-inf')
        
        return fitness_scores
    
    def _calculate_fitness(self,
                         hard_violations: Dict[str, int],
                         soft_penalties: Dict[str, float]) -> float:
        """
        Calculate fitness score from constraint violations.
        
        Args:
            hard_violations: Dictionary of hard constraint violation counts
            soft_penalties: Dictionary of soft constraint penalty scores
        
        Returns:
            Fitness score (higher is better)
        """
        if self.adaptive_weights:
            # Use adaptive weights for individual constraints
            total_hard_penalty = 0
            total_soft_penalty = 0
            
            # Apply specific weights to each constraint type
            for constraint_type, violations in hard_violations.items():
                weight = self.adaptive_weights.get(constraint_type, self.alpha)
                total_hard_penalty += weight * violations
            
            for constraint_type, penalty in soft_penalties.items():
                weight = self.adaptive_weights.get(constraint_type, self.beta)
                total_soft_penalty += weight * penalty
            
            fitness = -(total_hard_penalty + total_soft_penalty)
        else:
            # Use default weights
            total_hard_violations = sum(hard_violations.values())
            total_soft_penalty = sum(soft_penalties.values())
            fitness = -(self.alpha * total_hard_violations + self.beta * total_soft_penalty)
        
        return fitness
    
    def _generate_cache_key(self, chromosome: Chromosome) -> str:
        """
        Generate a cache key for a chromosome.
        
        Args:
            chromosome: Chromosome to generate key for
        
        Returns:
            Cache key string
        """
        # Create a hash based on gene assignments
        gene_strings = []
        for gene in chromosome.genes:
            gene_string = f"{gene.course_id}_{gene.instructor_id}_{gene.room_id}_{gene.day}_{gene.time_slot}"
            gene_strings.append(gene_string)
        
        # Sort to ensure consistent ordering
        gene_strings.sort()
        
        # Create hash
        import hashlib
        cache_key = hashlib.md5('|'.join(gene_strings).encode()).hexdigest()
        
        return cache_key
    
    def calculate_fitness_diversity_bonus(self,
                                        chromosome: Chromosome,
                                        population_chromosomes: List[Chromosome]) -> float:
        """
        Calculate diversity bonus for a chromosome based on population diversity.
        
        Args:
            chromosome: Chromosome to calculate bonus for
            population_chromosomes: Other chromosomes in the population
        
        Returns:
            Diversity bonus score
        """
        if len(population_chromosomes) < 2:
            return 0.0
        
        # Calculate average distance to other chromosomes
        total_distance = 0.0
        comparison_count = 0
        
        for other_chromosome in population_chromosomes:
            if other_chromosome != chromosome:
                distance = self._calculate_chromosome_distance(chromosome, other_chromosome)
                total_distance += distance
                comparison_count += 1
        
        if comparison_count == 0:
            return 0.0
        
        average_distance = total_distance / comparison_count
        diversity_bonus = average_distance * self.diversity_bonus
        
        return diversity_bonus
    
    def _calculate_chromosome_distance(self, chr1: Chromosome, chr2: Chromosome) -> float:
        """
        Calculate normalized distance between two chromosomes.
        
        Args:
            chr1: First chromosome
            chr2: Second chromosome
        
        Returns:
            Distance score between 0 and 1
        """
        if len(chr1.genes) != len(chr2.genes):
            return 1.0  # Maximum distance if different sizes
        
        differences = 0
        total_genes = len(chr1.genes)
        
        for gene1, gene2 in zip(chr1.genes, chr2.genes):
            # Count differences in gene attributes
            if gene1.instructor_id != gene2.instructor_id:
                differences += 1
            if gene1.room_id != gene2.room_id:
                differences += 1
            if gene1.day != gene2.day:
                differences += 1
            if gene1.time_slot != gene2.time_slot:
                differences += 1
        
        # Normalize by total possible differences (4 attributes per gene)
        if total_genes == 0:
            return 0.0
        
        max_differences = total_genes * 4
        return differences / max_differences
    
    def get_fitness_breakdown(self,
                            chromosome: Chromosome,
                            courses: Dict[str, Course],
                            instructors: Dict[str, Instructor],
                            rooms: Dict[str, Room],
                            groups: Dict[str, Group]) -> Dict[str, Any]:
        """
        Get detailed fitness breakdown for a chromosome.
        
        Args:
            chromosome: Chromosome to analyze
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Dictionary with detailed fitness breakdown
        """
        # Get constraint violations
        hard_violations, soft_penalties = self.constraint_checker.check_all_constraints(
            chromosome, courses, instructors, rooms, groups
        )
        
        # Calculate components
        total_hard_violations = sum(hard_violations.values())
        total_soft_penalty = sum(soft_penalties.values())
        
        hard_penalty = self.alpha * total_hard_violations
        soft_penalty = self.beta * total_soft_penalty
        
        fitness = -(hard_penalty + soft_penalty)
        
        return {
            'fitness': fitness,
            'hard_violations': hard_violations,
            'soft_penalties': soft_penalties,
            'total_hard_violations': total_hard_violations,
            'total_soft_penalty': total_soft_penalty,
            'hard_penalty': hard_penalty,
            'soft_penalty': soft_penalty,
            'weights': {
                'alpha': self.alpha,
                'beta': self.beta
            }
        }
    
    def compare_chromosomes(self,
                          chr1: Chromosome,
                          chr2: Chromosome,
                          courses: Dict[str, Course],
                          instructors: Dict[str, Instructor],
                          rooms: Dict[str, Room],
                          groups: Dict[str, Group]) -> Dict[str, Any]:
        """
        Compare two chromosomes and return detailed comparison.
        
        Args:
            chr1: First chromosome
            chr2: Second chromosome
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Comparison results dictionary
        """
        breakdown1 = self.get_fitness_breakdown(chr1, courses, instructors, rooms, groups)
        breakdown2 = self.get_fitness_breakdown(chr2, courses, instructors, rooms, groups)
        
        return {
            'chromosome1': breakdown1,
            'chromosome2': breakdown2,
            'fitness_difference': breakdown1['fitness'] - breakdown2['fitness'],
            'better_chromosome': 1 if breakdown1['fitness'] > breakdown2['fitness'] else 2,
            'distance': self._calculate_chromosome_distance(chr1, chr2)
        }
    
    def update_weights(self, alpha: float, beta: float, diversity_bonus: float = None) -> None:
        """
        Update fitness function weights.
        
        Args:
            alpha: Weight for hard constraints
            beta: Weight for soft constraints
            diversity_bonus: Optional diversity bonus weight
        """
        self.alpha = alpha
        self.beta = beta
        
        if diversity_bonus is not None:
            self.diversity_bonus = diversity_bonus
        
        # Clear cache since weights changed
        self.fitness_cache.clear()
        
        self.logger.info(f"Fitness weights updated: α={alpha}, β={beta}")
    
    def update_constraint_weights(self, weights: Dict[str, float]) -> None:
        """
        Update constraint weights for adaptive constraint weight system.
        
        Args:
            weights: Dictionary of constraint weights
        """
        self.adaptive_weights = weights
        self.logger.info(f"Updated constraint weights: {weights}")
        
        # Clear cache when weights change
        self.fitness_cache.clear()
    
    def clear_cache(self) -> None:
        """Clear the fitness cache."""
        self.fitness_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger.info("Fitness cache cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get evaluator statistics.
        
        Returns:
            Dictionary with statistics
        """
        avg_time = (self.total_evaluation_time / self.evaluation_count 
                   if self.evaluation_count > 0 else 0)
        
        cache_hit_rate = (self.cache_hits / (self.cache_hits + self.cache_misses)
                         if (self.cache_hits + self.cache_misses) > 0 else 0)
        
        return {
            'evaluation_count': self.evaluation_count,
            'total_evaluation_time': self.total_evaluation_time,
            'average_evaluation_time': avg_time,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self.fitness_cache),
            'weights': {
                'alpha': self.alpha,
                'beta': self.beta,
                'diversity_bonus': self.diversity_bonus
            }
        }
    
    def reset_statistics(self) -> None:
        """Reset evaluator statistics."""
        self.evaluation_count = 0
        self.total_evaluation_time = 0.0
        self.cache_hits = 0
        self.cache_misses = 0
        self.logger.info("Evaluator statistics reset")
    
    def __str__(self) -> str:
        stats = self.get_statistics()
        return f"FitnessEvaluator(evaluations={stats['evaluation_count']}, α={self.alpha}, β={self.beta})"
    
    def __repr__(self) -> str:
        return self.__str__()
