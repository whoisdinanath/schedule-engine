"""
Population class for managing collections of chromosomes in the genetic algorithm.
"""

from typing import List, Dict, Any, Optional, Callable, Tuple
import random
import statistics
from collections import defaultdict
import copy

from .chromosome import Chromosome, Gene
from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger
from ..utils.config import TIME_SLOTS


class Population:
    """
    Manages a collection of chromosomes representing potential timetable solutions.
    Provides methods for initialization, evaluation, and selection operations.
    """
    
    def __init__(self, size: int = 50):
        """
        Initialize population with specified size.
        
        Args:
            size: Number of chromosomes in the population
        """
        self.size = size
        self.chromosomes: List[Chromosome] = []
        self.generation = 0
        self.best_fitness_history: List[float] = []
        self.avg_fitness_history: List[float] = []
        self.diversity_history: List[float] = []
        self.logger = get_logger(self.__class__.__name__)
    
    def initialize_random(self,
                         courses: Dict[str, Course],
                         instructors: Dict[str, Instructor],
                         rooms: Dict[str, Room],
                         groups: Dict[str, Group]) -> None:
        """
        Initialize population with random chromosomes.
        
        Args:
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        """
        self.logger.info(f"Initializing population with {self.size} random chromosomes...")
        
        self.chromosomes.clear()
        
        for i in range(self.size):
            chromosome = self._create_random_chromosome(courses, instructors, rooms, groups)
            if chromosome:
                self.chromosomes.append(chromosome)
            else:
                self.logger.warning(f"Failed to create chromosome {i}")
        
        self.logger.info(f"Successfully created {len(self.chromosomes)} chromosomes")
    
    def _create_random_chromosome(self,
                                courses: Dict[str, Course],
                                instructors: Dict[str, Instructor],
                                rooms: Dict[str, Room],
                                groups: Dict[str, Group]) -> Optional[Chromosome]:
        """
        Create a single random chromosome.
        
        Args:
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities  
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Random chromosome or None if creation failed
        """
        try:
            genes = []
            
            # Create genes for each required course session
            for course_id, course in courses.items():
                for session_index in range(course.sessions_per_week):
                    gene = self._create_random_gene(
                        course, instructors, rooms, groups, session_index
                    )
                    if gene:
                        genes.append(gene)
            
            return Chromosome(genes)
            
        except Exception as e:
            self.logger.error(f"Error creating random chromosome: {str(e)}")
            return None
    
    def _create_random_gene(self,
                          course: Course,
                          instructors: Dict[str, Instructor],
                          rooms: Dict[str, Room],
                          groups: Dict[str, Group],
                          session_index: int) -> Optional[Gene]:
        """
        Create a random gene for a course session.
        
        Args:
            course: Course entity
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
            session_index: Index of the session within the course
        
        Returns:
            Random gene or None if creation failed
        """
        try:
            # Get qualified instructors
            qualified_instructors = [
                instructor_id for instructor_id in course.qualified_instructor_ids
                if instructor_id in instructors
            ]
            
            if not qualified_instructors:
                self.logger.warning(f"No qualified instructors found for course {course.course_id}")
                return None
            
            # Get suitable rooms
            suitable_rooms = [
                room_id for room_id, room in rooms.items()
                if room.is_suitable_for_course_type(course.required_room_type)
            ]
            
            if not suitable_rooms:
                self.logger.warning(f"No suitable rooms found for course {course.course_id}")
                return None
            
            # Get available time slots (all possible combinations)
            available_slots = []
            for day in TIME_SLOTS['days']:
                for time_slot in TIME_SLOTS['slots']:
                    available_slots.append((day, time_slot))
            
            if not available_slots:
                self.logger.warning("No time slots available")
                return None
            
            # Randomly select instructor, room, and time slot
            instructor_id = random.choice(qualified_instructors)
            room_id = random.choice(suitable_rooms)
            day, time_slot = random.choice(available_slots)
            
            # Create and return gene
            return Gene(
                course_id=course.course_id,
                instructor_id=instructor_id,
                room_id=room_id,
                day=day,
                time_slot=time_slot,
                session_index=session_index
            )
            
        except Exception as e:
            self.logger.error(f"Error creating random gene for course {course.course_id}: {str(e)}")
            return None
    
    def add_chromosome(self, chromosome: Chromosome) -> None:
        """Add a chromosome to the population."""
        self.chromosomes.append(chromosome)
    
    def remove_chromosome(self, index: int) -> Chromosome:
        """Remove and return a chromosome at the specified index."""
        if 0 <= index < len(self.chromosomes):
            return self.chromosomes.pop(index)
        raise IndexError(f"Chromosome index {index} out of range")
    
    def get_chromosome(self, index: int) -> Chromosome:
        """Get chromosome at specified index."""
        return self.chromosomes[index]
    
    def set_chromosome(self, index: int, chromosome: Chromosome) -> None:
        """Set chromosome at specified index."""
        self.chromosomes[index] = chromosome
    
    def get_size(self) -> int:
        """Get current population size."""
        return len(self.chromosomes)
    
    def get_best_chromosome(self) -> Optional[Chromosome]:
        """Get the chromosome with the best fitness."""
        if not self.chromosomes:
            return None
        
        # Find chromosome with highest fitness (assuming higher is better)
        best_chromosome = max(self.chromosomes, key=lambda c: c.fitness if c.fitness != float('-inf') else float('-inf'))
        
        if best_chromosome.fitness == float('-inf'):
            return None
            
        return best_chromosome
    
    def get_worst_chromosome(self) -> Optional[Chromosome]:
        """Get the chromosome with the worst fitness."""
        if not self.chromosomes:
            return None
        
        # Find chromosome with lowest fitness
        worst_chromosome = min(self.chromosomes, key=lambda c: c.fitness if c.fitness != float('-inf') else float('inf'))
        
        return worst_chromosome
    
    def get_fitness_statistics(self) -> Dict[str, float]:
        """
        Get fitness statistics for the population.
        
        Returns:
            Dictionary with fitness statistics
        """
        if not self.chromosomes:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        
        fitness_values = [c.fitness for c in self.chromosomes if c.fitness != float('-inf')]
        
        if not fitness_values:
            return {'mean': 0, 'std': 0, 'min': 0, 'max': 0, 'median': 0}
        
        return {
            'mean': statistics.mean(fitness_values),
            'std': statistics.stdev(fitness_values) if len(fitness_values) > 1 else 0,
            'min': min(fitness_values),
            'max': max(fitness_values),
            'median': statistics.median(fitness_values)
        }
    
    def calculate_diversity(self) -> float:
        """
        Calculate population diversity based on genotype differences.
        
        Returns:
            Diversity score between 0 and 1
        """
        if len(self.chromosomes) < 2:
            return 0.0
        
        total_distance = 0
        comparisons = 0
        
        for i in range(len(self.chromosomes)):
            for j in range(i + 1, len(self.chromosomes)):
                distance = self._calculate_chromosome_distance(
                    self.chromosomes[i], self.chromosomes[j]
                )
                total_distance += distance
                comparisons += 1
        
        if comparisons == 0:
            return 0.0
        
        average_distance = total_distance / comparisons
        return min(average_distance, 1.0)  # Normalize to [0, 1]
    
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
    
    def sort_by_fitness(self, reverse: bool = True) -> None:
        """
        Sort population by fitness.
        
        Args:
            reverse: If True, sort in descending order (best first)
        """
        self.chromosomes.sort(
            key=lambda c: c.fitness if c.fitness != float('-inf') else (float('-inf') if reverse else float('inf')),
            reverse=reverse
        )
    
    def truncate(self, new_size: int) -> None:
        """
        Truncate population to specified size, keeping the best chromosomes.
        
        Args:
            new_size: New population size
        """
        if new_size < len(self.chromosomes):
            self.sort_by_fitness(reverse=True)
            self.chromosomes = self.chromosomes[:new_size]
            self.size = new_size
    
    def extend(self, chromosomes: List[Chromosome]) -> None:
        """
        Add multiple chromosomes to the population.
        
        Args:
            chromosomes: List of chromosomes to add
        """
        self.chromosomes.extend(chromosomes)
    
    def clear(self) -> None:
        """Clear all chromosomes from the population."""
        self.chromosomes.clear()
    
    def update_history(self) -> None:
        """Update fitness and diversity history."""
        stats = self.get_fitness_statistics()
        diversity = self.calculate_diversity()
        
        self.best_fitness_history.append(stats['max'])
        self.avg_fitness_history.append(stats['mean'])
        self.diversity_history.append(diversity)
    
    def get_elite(self, elite_size: int) -> List[Chromosome]:
        """
        Get elite chromosomes (best performers).
        
        Args:
            elite_size: Number of elite chromosomes to return
        
        Returns:
            List of elite chromosomes
        """
        self.sort_by_fitness(reverse=True)
        return [chromosome.copy() for chromosome in self.chromosomes[:elite_size]]
    
    def replace_worst(self, new_chromosomes: List[Chromosome]) -> None:
        """
        Replace worst chromosomes with new ones.
        
        Args:
            new_chromosomes: List of new chromosomes to add
        """
        self.sort_by_fitness(reverse=True)
        
        # Replace worst chromosomes
        num_to_replace = min(len(new_chromosomes), len(self.chromosomes))
        self.chromosomes[-num_to_replace:] = new_chromosomes[:num_to_replace]
    
    def tournament_selection(self, tournament_size: int = 5) -> Chromosome:
        """
        Select a chromosome using tournament selection.
        
        Args:
            tournament_size: Size of the tournament
        
        Returns:
            Selected chromosome
        """
        if tournament_size > len(self.chromosomes):
            tournament_size = len(self.chromosomes)
        
        # Randomly select chromosomes for tournament
        tournament = random.sample(self.chromosomes, tournament_size)
        
        # Return the best chromosome from tournament
        return max(tournament, key=lambda c: c.fitness if c.fitness != float('-inf') else float('-inf'))
    
    def roulette_selection(self) -> Chromosome:
        """
        Select a chromosome using roulette wheel selection.
        
        Returns:
            Selected chromosome
        """
        fitness_values = [c.fitness for c in self.chromosomes]
        
        # Handle negative fitness values by shifting
        min_fitness = min(fitness_values)
        if min_fitness < 0:
            adjusted_fitness = [f - min_fitness + 1 for f in fitness_values]
        else:
            adjusted_fitness = fitness_values
        
        total_fitness = sum(adjusted_fitness)
        
        if total_fitness == 0:
            return random.choice(self.chromosomes)
        
        # Spin the roulette wheel
        pick = random.uniform(0, total_fitness)
        current = 0
        
        for i, fitness in enumerate(adjusted_fitness):
            current += fitness
            if current >= pick:
                return self.chromosomes[i]
        
        # Fallback (shouldn't reach here)
        return self.chromosomes[-1]
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive population statistics.
        
        Returns:
            Dictionary with population statistics
        """
        fitness_stats = self.get_fitness_statistics()
        diversity = self.calculate_diversity()
        
        return {
            'size': len(self.chromosomes),
            'generation': self.generation,
            'fitness_stats': fitness_stats,
            'diversity': diversity,
            'best_fitness_history': self.best_fitness_history.copy(),
            'avg_fitness_history': self.avg_fitness_history.copy(),
            'diversity_history': self.diversity_history.copy()
        }
    
    def __len__(self) -> int:
        """Get population size."""
        return len(self.chromosomes)
    
    def __iter__(self):
        """Make population iterable over chromosomes."""
        return iter(self.chromosomes)
    
    def __getitem__(self, index: int) -> Chromosome:
        """Get chromosome by index."""
        return self.chromosomes[index]
    
    def __setitem__(self, index: int, chromosome: Chromosome) -> None:
        """Set chromosome by index."""
        self.chromosomes[index] = chromosome
    
    def __str__(self) -> str:
        stats = self.get_fitness_statistics()
        return f"Population(size={len(self.chromosomes)}, gen={self.generation}, best_fitness={stats['max']:.4f})"
    
    def __repr__(self) -> str:
        return self.__str__()
