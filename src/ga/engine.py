"""
Main Genetic Algorithm Engine for the timetabling system.
Coordinates the entire GA process from initialization to solution generation.

This is a PURE GENETIC ALGORITHM implementation without any local search components.
Uses only genetic operators: selection, crossover, mutation, and elitism.
"""

from typing import Dict, List, Optional, Tuple, Any, Callable
import time
import statistics
import random
from datetime import datetime

from .chromosome import Chromosome, Gene
from .population import Population
from .operators import GeneticOperators
from ..entities import Course, Instructor, Room, Group
from ..fitness.evaluator import FitnessEvaluator
from ..constraints.checker import ConstraintChecker
from ..utils.logger import get_logger
from ..utils.config import GA_CONFIG


class GAEngine:
    """
    Main Genetic Algorithm engine that orchestrates the optimization process.
    
    This is a PURE GENETIC ALGORITHM implementation:
    - Uses only genetic operators: selection, crossover, mutation, elitism
    - No local search, hill climbing, or other hybrid optimization techniques
    - Rooms are always available (no room availability constraints)
    - Evolution based purely on fitness-driven selection and genetic variation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the GA engine.
        
        Args:
            config: Configuration dictionary (uses default GA_CONFIG if None)
        """
        self.logger = get_logger(self.__class__.__name__)
        self.config = config or GA_CONFIG
        
        # Initialize components
        self.population = Population(size=self.config.get('population_size', 50))
        self.operators = GeneticOperators(config)
        self.fitness_evaluator = FitnessEvaluator()
        self.constraint_checker = ConstraintChecker()
        
        # Evolution tracking
        self.generation = 0
        self.best_chromosome = None
        self.best_fitness = float('-inf')
        self.fitness_history = []
        self.diversity_history = []
        self.violation_history = []
        
        # Termination criteria
        self.max_generations = self.config.get('max_generations', 100)
        self.target_fitness = self.config.get('target_fitness', 0)
        self.stagnation_limit = self.config.get('stagnation_limit', 20)
        self.time_limit = self.config.get('time_limit_minutes', None)
        
        # Statistics
        self.start_time = None
        self.end_time = None
        self.total_evaluations = 0
        
    def initialize(self,
                  courses: Dict[str, Course],
                  instructors: Dict[str, Instructor],
                  rooms: Dict[str, Room],
                  groups: Dict[str, Group]) -> None:
        """
        Initialize the population and prepare for evolution.
        
        Args:
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        """
        self.logger.info("Initializing GA engine...")
        
        # Store entity references
        self.courses = courses
        self.instructors = instructors
        self.rooms = rooms
        self.groups = groups
        
        # Initialize population
        self.logger.info(f"Creating initial population of size {self.population.size}")
        self.population.initialize_random(courses, instructors, rooms, groups)
        
        # Log initialization results
        valid_chromosomes = len([c for c in self.population.chromosomes if c is not None])
        self.logger.info(f"Successfully created {valid_chromosomes}/{self.population.size} chromosomes")
        
        if valid_chromosomes == 0:
            raise RuntimeError("Failed to create any valid chromosomes in initial population")
        
        # Remove None chromosomes
        self.population.chromosomes = [c for c in self.population.chromosomes if c is not None]
        self.population.size = len(self.population.chromosomes)
        
        # Evaluate initial population
        self._evaluate_population()
        
        self.logger.info(f"Initial population fitness range: {min(self.current_fitness):.4f} to {max(self.current_fitness):.4f}")
    
    def evolve(self, 
              courses: Dict[str, Course],
              instructors: Dict[str, Instructor],
              rooms: Dict[str, Room],
              groups: Dict[str, Group],
              callback: Optional[Callable[[int, float, Dict[str, Any]], bool]] = None) -> Chromosome:
        """
        Run the genetic algorithm evolution process.
        
        Args:
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
            callback: Optional callback function called each generation
                     Should return True to continue, False to stop
        
        Returns:
            Best chromosome found
        """
        self.logger.info("Starting GA evolution...")
        self.start_time = time.time()
        
        # Initialize if not already done
        if not hasattr(self, 'courses'):
            self.initialize(courses, instructors, rooms, groups)
        
        stagnation_counter = 0
        previous_best = self.best_fitness
        
        for generation in range(self.max_generations):
            self.generation = generation
            
            # Check time limit
            if self.time_limit and (time.time() - self.start_time) > (self.time_limit * 60):
                self.logger.info(f"Time limit reached at generation {generation}")
                break
            
            # Create new generation
            new_population = self._create_new_generation(stagnation_counter)
            
            # Replace population
            self.population.chromosomes = new_population
            self.population.size = len(new_population)
            
            # Evaluate new population
            self._evaluate_population()
            
            # Update best solution
            generation_best_idx = self.current_fitness.index(max(self.current_fitness))
            generation_best_fitness = self.current_fitness[generation_best_idx]
            
            if generation_best_fitness > self.best_fitness:
                self.best_fitness = generation_best_fitness
                self.best_chromosome = self.population.chromosomes[generation_best_idx].copy()
                stagnation_counter = 0
            else:
                stagnation_counter += 1
            
            # Record statistics
            avg_fitness = statistics.mean(self.current_fitness)
            diversity = self.operators.calculate_diversity(self.population)
            
            self.fitness_history.append({
                'generation': generation,
                'best': generation_best_fitness,
                'average': avg_fitness,
                'worst': min(self.current_fitness)
            })
            self.diversity_history.append(diversity)
            
            # Count violations in best chromosome
            best_chromosome = self.population.chromosomes[generation_best_idx]
            violations = self._count_violations(best_chromosome)
            self.violation_history.append(violations)
            
            # Log progress
            self.logger.log_ga_generation(
                generation, self.best_fitness, avg_fitness, violations['total']
            )
            
            # Call callback if provided
            if callback:
                stats = {
                    'generation': generation,
                    'best_fitness': self.best_fitness,
                    'avg_fitness': avg_fitness,
                    'diversity': diversity,
                    'violations': violations,
                    'stagnation': stagnation_counter
                }
                if not callback(generation, self.best_fitness, stats):
                    self.logger.info("Evolution stopped by callback")
                    break
            
            # Check termination criteria
            if self.best_fitness >= self.target_fitness:
                self.logger.info(f"Target fitness {self.target_fitness} reached at generation {generation}")
                break
            
            if stagnation_counter >= self.stagnation_limit:
                self.logger.info(f"Evolution stagnated for {self.stagnation_limit} generations")
                break
        
        self.end_time = time.time()
        self._log_final_statistics()
        
        return self.best_chromosome
    
    def _create_new_generation(self, stagnation_counter: int) -> List[Chromosome]:
        """
        Create a new generation using genetic operators.
        
        Returns:
            List of chromosomes for the new generation
        """
        new_population = []
        
        # Apply elitism - keep best chromosomes
        elite_chromosomes = self.operators.apply_elitism(self.population, self.current_fitness)
        new_population.extend(elite_chromosomes)
        
        # Calculate current diversity
        current_diversity = self.diversity_history[-1] if self.diversity_history else 0.5
        
        # Generate rest of population through crossover and mutation
        while len(new_population) < self.population.size:
            # Select parents
            parent1 = self.operators.select_parents(self.population, self.current_fitness)
            parent2 = self.operators.select_parents(self.population, self.current_fitness)
            
            # Apply crossover
            if random.random() < self.operators.crossover_rate:
                offspring1, offspring2 = self.operators.crossover(parent1, parent2, current_diversity)
            else:
                offspring1, offspring2 = parent1.copy(), parent2.copy()
            
            # Apply mutation
            if random.random() < self.operators.mutation_rate:
                offspring1 = self.operators.mutate(offspring1, self.courses, 
                                                  self.instructors, self.rooms, self.groups,
                                                  stagnation_counter, current_diversity)
            if random.random() < self.operators.mutation_rate:
                offspring2 = self.operators.mutate(offspring2, self.courses, 
                                                  self.instructors, self.rooms, self.groups,
                                                  stagnation_counter, current_diversity)
            
            # Add to new population
            new_population.extend([offspring1, offspring2])
        
        # Trim to exact population size
        return new_population[:self.population.size]
    
    def _evaluate_population(self) -> None:
        """
        Evaluate fitness of all chromosomes in the current population.
        """
        self.current_fitness = []
        
        for chromosome in self.population.chromosomes:
            fitness = self.fitness_evaluator.evaluate_chromosome(
                chromosome, self.courses, self.instructors, self.rooms, self.groups
            )
            self.current_fitness.append(fitness)
            self.total_evaluations += 1
    
    def _count_violations(self, chromosome: Chromosome) -> Dict[str, int]:
        """
        Count constraint violations in a chromosome.
        
        Args:
            chromosome: Chromosome to analyze
        
        Returns:
            Dictionary with violation counts
        """
        try:
            hard_violations, soft_violations = self.constraint_checker.check_all_constraints(
                chromosome, self.courses, self.instructors, self.rooms, self.groups
            )
            
            # Debug: check the structure of returned violations
            self.logger.debug(f"Hard violations: {hard_violations}")
            self.logger.debug(f"Soft violations: {soft_violations}")
            
            total_hard = sum(hard_violations.values())
            total_soft = sum(soft_violations.values())
            
            return {
                'hard': hard_violations,
                'soft': soft_violations,
                'total_hard': total_hard,
                'total_soft': total_soft,
                'total': total_hard + total_soft
            }
        except Exception as e:
            self.logger.error(f"Error counting violations: {str(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    def _log_final_statistics(self) -> None:
        """
        Log final evolution statistics.
        """
        duration = self.end_time - self.start_time if self.start_time else 0
        
        self.logger.info("=== GA Evolution Complete ===")
        self.logger.info(f"Generations completed: {self.generation + 1}")
        self.logger.info(f"Total time: {duration:.2f} seconds")
        self.logger.info(f"Total evaluations: {self.total_evaluations}")
        self.logger.info(f"Evaluations per second: {self.total_evaluations / duration:.2f}")
        self.logger.info(f"Best fitness achieved: {self.best_fitness:.6f}")
        
        if self.best_chromosome:
            violations = self._count_violations(self.best_chromosome)
            self.logger.info(f"Hard constraint violations: {violations['total_hard']}")
            self.logger.info(f"Soft constraint violations: {violations['total_soft']}")
            
            if violations['total_hard'] == 0:
                self.logger.info("✓ Found feasible solution!")
            else:
                self.logger.warning("✗ Best solution still has hard constraint violations")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive evolution statistics.
        
        Returns:
            Dictionary containing evolution statistics
        """
        duration = (self.end_time - self.start_time) if (self.start_time and self.end_time) else 0
        
        stats = {
            'evolution': {
                'generations': self.generation + 1,
                'duration_seconds': duration,
                'total_evaluations': self.total_evaluations,
                'evaluations_per_second': self.total_evaluations / duration if duration > 0 else 0
            },
            'fitness': {
                'best_achieved': self.best_fitness,
                'fitness_history': self.fitness_history,
                'diversity_history': self.diversity_history
            },
            'violations': {
                'violation_history': self.violation_history
            },
            'configuration': self.config
        }
        
        if self.best_chromosome:
            final_violations = self._count_violations(self.best_chromosome)
            stats['final_solution'] = {
                'is_feasible': final_violations['total_hard'] == 0,
                'hard_violations': final_violations['total_hard'],
                'soft_violations': final_violations['total_soft'],
                'total_genes': len(self.best_chromosome.genes)
            }
        
        return stats
    
    def get_best_solution(self) -> Optional[Chromosome]:
        """
        Get the best chromosome found during evolution.
        
        Returns:
            Best chromosome or None if evolution hasn't run
        """
        return self.best_chromosome.copy() if self.best_chromosome else None
