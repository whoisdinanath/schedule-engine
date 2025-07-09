"""
Genetic operators for the PURE GA-based timetabling system.
Implements selection, crossover, mutation, and other genetic operations.
No local search or hybrid optimization components.
"""

from typing import List, Tuple, Dict, Any, Optional
import random
import copy
from collections import Counter

from .chromosome import Chromosome, Gene
from .population import Population
from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger
from ..utils.config import GA_CONFIG, TIME_SLOTS


class GeneticOperators:
    """
    Implements genetic operators for the timetabling GA.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize genetic operators.
        
        Args:
            config: Configuration dictionary (uses default GA_CONFIG if None)
        """
        self.logger = get_logger(self.__class__.__name__)
        self.config = config or GA_CONFIG
        
        # Set up parameters
        self.tournament_size = self.config.get('tournament_size', 5)
        self.crossover_rate = self.config.get('crossover_rate', 0.8)
        self.mutation_rate = self.config.get('mutation_rate', 0.1)
        self.elite_size = self.config.get('elite_size', 5)
        
    def tournament_selection(self, 
                           population: Population, 
                           fitness_scores: List[float], 
                           tournament_size: Optional[int] = None) -> Chromosome:
        """
        Perform tournament selection to choose a parent chromosome.
        
        Args:
            population: Population to select from
            fitness_scores: Fitness scores for each chromosome
            tournament_size: Size of tournament (uses config default if None)
        
        Returns:
            Selected chromosome
        """
        tournament_size = tournament_size or self.tournament_size
        tournament_size = min(tournament_size, len(population.chromosomes))
        
        # Randomly select tournament participants
        tournament_indices = random.sample(range(len(population.chromosomes)), tournament_size)
        
        # Find the best chromosome in the tournament (highest fitness)
        best_index = max(tournament_indices, key=lambda i: fitness_scores[i])
        
        return population.chromosomes[best_index].copy()
    
    def roulette_wheel_selection(self, 
                               population: Population, 
                               fitness_scores: List[float]) -> Chromosome:
        """
        Perform roulette wheel selection.
        
        Args:
            population: Population to select from
            fitness_scores: Fitness scores for each chromosome
        
        Returns:
            Selected chromosome
        """
        # Handle negative fitness scores by shifting
        min_fitness = min(fitness_scores)
        if min_fitness < 0:
            adjusted_scores = [score - min_fitness + 1 for score in fitness_scores]
        else:
            adjusted_scores = fitness_scores
        
        total_fitness = sum(adjusted_scores)
        if total_fitness == 0:
            # If all fitness scores are the same, select randomly
            return random.choice(population.chromosomes).copy()
        
        # Generate random number and find corresponding chromosome
        pick = random.uniform(0, total_fitness)
        current = 0
        
        for i, score in enumerate(adjusted_scores):
            current += score
            if current >= pick:
                return population.chromosomes[i].copy()
        
        # Fallback (should not reach here)
        return population.chromosomes[-1].copy()
    
    def rank_selection(self, 
                      population: Population, 
                      fitness_scores: List[float]) -> Chromosome:
        """
        Perform rank-based selection.
        
        Args:
            population: Population to select from
            fitness_scores: Fitness scores for each chromosome
        
        Returns:
            Selected chromosome
        """
        # Create rank-based probabilities
        sorted_indices = sorted(range(len(fitness_scores)), 
                              key=lambda i: fitness_scores[i], reverse=True)
        
        # Assign ranks (higher rank = better fitness)
        ranks = [0] * len(fitness_scores)
        for rank, index in enumerate(sorted_indices):
            ranks[index] = len(fitness_scores) - rank
        
        # Use ranks for roulette wheel selection
        total_rank = sum(ranks)
        pick = random.uniform(0, total_rank)
        current = 0
        
        for i, rank in enumerate(ranks):
            current += rank
            if current >= pick:
                return population.chromosomes[i].copy()
        
        return population.chromosomes[-1].copy()
    
    def uniform_crossover(self, 
                         parent1: Chromosome, 
                         parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """
        Perform uniform crossover between two parent chromosomes.
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
        
        Returns:
            Tuple of two offspring chromosomes
        """
        if len(parent1.genes) != len(parent2.genes):
            self.logger.warning("Parents have different lengths for crossover")
            return parent1.copy(), parent2.copy()
        
        # Create offspring
        offspring1_genes = []
        offspring2_genes = []
        
        # Uniform crossover: each gene has 50% chance of coming from either parent
        for i in range(len(parent1.genes)):
            if random.random() < 0.5:
                offspring1_genes.append(copy.deepcopy(parent1.genes[i]))
                offspring2_genes.append(copy.deepcopy(parent2.genes[i]))
            else:
                offspring1_genes.append(copy.deepcopy(parent2.genes[i]))
                offspring2_genes.append(copy.deepcopy(parent1.genes[i]))
        
        return Chromosome(offspring1_genes), Chromosome(offspring2_genes)
    
    def single_point_crossover(self, 
                             parent1: Chromosome, 
                             parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """
        Perform single-point crossover between two parent chromosomes.
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
        
        Returns:
            Tuple of two offspring chromosomes
        """
        if len(parent1.genes) != len(parent2.genes):
            self.logger.warning("Parents have different lengths for crossover")
            return parent1.copy(), parent2.copy()
        
        if len(parent1.genes) <= 1:
            return parent1.copy(), parent2.copy()
        
        # Choose crossover point
        crossover_point = random.randint(1, len(parent1.genes) - 1)
        
        # Create offspring
        offspring1_genes = (copy.deepcopy(parent1.genes[:crossover_point]) + 
                           copy.deepcopy(parent2.genes[crossover_point:]))
        offspring2_genes = (copy.deepcopy(parent2.genes[:crossover_point]) + 
                           copy.deepcopy(parent1.genes[crossover_point:]))
        
        return Chromosome(offspring1_genes), Chromosome(offspring2_genes)
    
    def two_point_crossover(self, 
                          parent1: Chromosome, 
                          parent2: Chromosome) -> Tuple[Chromosome, Chromosome]:
        """
        Perform two-point crossover between two parent chromosomes.
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
        
        Returns:
            Tuple of two offspring chromosomes
        """
        if len(parent1.genes) != len(parent2.genes):
            self.logger.warning("Parents have different lengths for crossover")
            return parent1.copy(), parent2.copy()
        
        if len(parent1.genes) <= 2:
            return self.single_point_crossover(parent1, parent2)
        
        # Choose two crossover points
        point1 = random.randint(1, len(parent1.genes) - 2)
        point2 = random.randint(point1 + 1, len(parent1.genes) - 1)
        
        # Create offspring
        offspring1_genes = (copy.deepcopy(parent1.genes[:point1]) +
                           copy.deepcopy(parent2.genes[point1:point2]) +
                           copy.deepcopy(parent1.genes[point2:]))
        
        offspring2_genes = (copy.deepcopy(parent2.genes[:point1]) +
                           copy.deepcopy(parent1.genes[point1:point2]) +
                           copy.deepcopy(parent2.genes[point2:]))
        
        return Chromosome(offspring1_genes), Chromosome(offspring2_genes)
    
    def random_mutation(self, 
                       chromosome: Chromosome,
                       courses: Dict[str, Course],
                       instructors: Dict[str, Instructor],
                       rooms: Dict[str, Room],
                       groups: Dict[str, Group]) -> Chromosome:
        """
        Perform random mutation on a chromosome.
        
        Args:
            chromosome: Chromosome to mutate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Mutated chromosome
        """
        mutated = chromosome.copy()
        
        # Mutate each gene with probability equal to mutation rate
        for i in range(len(mutated.genes)):
            if random.random() < self.mutation_rate:
                gene = mutated.genes[i]
                
                # Get course info
                if gene.course_id not in courses:
                    continue
                
                course = courses[gene.course_id]
                
                # Randomly choose what to mutate: instructor, room, or time slot
                mutation_type = random.choice(['instructor', 'room', 'time'])
                
                if mutation_type == 'instructor':
                    # Mutate instructor
                    qualified_instructors = [
                        inst_id for inst_id in course.qualified_instructor_ids
                        if inst_id in instructors
                    ]
                    if qualified_instructors:
                        gene.instructor_id = random.choice(qualified_instructors)
                
                elif mutation_type == 'room':
                    # Mutate room
                    suitable_rooms = [
                        room_id for room_id, room in rooms.items()
                        if room.is_suitable_for_course_type(course.required_room_type)
                    ]
                    if suitable_rooms:
                        gene.room_id = random.choice(suitable_rooms)
                
                elif mutation_type == 'time':
                    # Mutate time slot
                    available_slots = []
                    for day in TIME_SLOTS['days']:
                        for time_slot in TIME_SLOTS['slots']:
                            available_slots.append((day, time_slot))
                    
                    if available_slots:
                        new_day, new_time = random.choice(available_slots)
                        gene.day = new_day
                        gene.time_slot = new_time
        
        return mutated
    
    def swap_mutation(self, chromosome: Chromosome) -> Chromosome:
        """
        Perform swap mutation by swapping time slots of random genes.
        
        Args:
            chromosome: Chromosome to mutate
        
        Returns:
            Mutated chromosome
        """
        mutated = chromosome.copy()
        
        if len(mutated.genes) < 2:
            return mutated
        
        # Select two random genes and swap their time slots
        if random.random() < self.mutation_rate:
            idx1, idx2 = random.sample(range(len(mutated.genes)), 2)
            gene1, gene2 = mutated.genes[idx1], mutated.genes[idx2]
            
            # Swap time information
            gene1.day, gene2.day = gene2.day, gene1.day
            gene1.time_slot, gene2.time_slot = gene2.time_slot, gene1.time_slot
        
        return mutated
    
    def adaptive_mutation(self, chromosome: Chromosome,
                         courses: Dict[str, Course],
                         instructors: Dict[str, Instructor],
                         rooms: Dict[str, Room],
                         groups: Dict[str, Group],
                         stagnation_counter: int = 0,
                         diversity: float = 0.5) -> Chromosome:
        """
        Perform adaptive mutation that increases intensity based on stagnation and diversity.
        
        Args:
            chromosome: Chromosome to mutate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
            stagnation_counter: Number of generations without improvement
            diversity: Population diversity (0-1)
        
        Returns:
            Mutated chromosome
        """
        # Calculate adaptive mutation intensity
        base_intensity = self.mutation_rate
        
        # Increase intensity based on stagnation
        stagnation_factor = 1.0 + (stagnation_counter / 50.0) * 2.0
        
        # Increase intensity when diversity is low
        diversity_factor = 1.0 + (1.0 - diversity) * 1.5
        
        # Combined adaptive intensity
        adaptive_intensity = min(base_intensity * stagnation_factor * diversity_factor, 0.8)
        
        mutated = chromosome.copy()
        
        # Apply more aggressive mutations when intensity is high
        if adaptive_intensity > 0.3:
            # Multi-gene mutation for high intensity
            num_mutations = min(int(len(mutated.genes) * adaptive_intensity), len(mutated.genes))
            mutation_indices = random.sample(range(len(mutated.genes)), num_mutations)
        else:
            # Single gene mutation for low intensity
            mutation_indices = [random.randint(0, len(mutated.genes) - 1)]
        
        for gene_idx in mutation_indices:
            gene = mutated.genes[gene_idx]
            
            # Get course info
            if gene.course_id not in courses:
                continue
                
            course = courses[gene.course_id]
            
            # Choose mutation type based on intensity
            if adaptive_intensity > 0.5:
                # High intensity: mutate multiple aspects
                mutation_types = ['instructor', 'room', 'time']
                for mut_type in random.sample(mutation_types, random.randint(1, len(mutation_types))):
                    self._apply_single_mutation(gene, mut_type, course, courses, instructors, rooms, groups)
            else:
                # Low intensity: mutate single aspect
                mutation_type = random.choice(['instructor', 'room', 'time'])
                self._apply_single_mutation(gene, mutation_type, course, courses, instructors, rooms, groups)
        
        return mutated
    
    def _apply_single_mutation(self, gene: Gene, mutation_type: str, course: Course,
                              courses: Dict[str, Course],
                              instructors: Dict[str, Instructor],
                              rooms: Dict[str, Room],
                              groups: Dict[str, Group]) -> None:
        """
        Apply a single mutation operation to a gene.
        
        Args:
            gene: Gene to mutate
            mutation_type: Type of mutation ('instructor', 'room', 'time')
            course: Course entity for the gene
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        """
        if mutation_type == 'instructor':
            qualified_instructors = [
                inst_id for inst_id in course.qualified_instructor_ids
                if inst_id in instructors
            ]
            if qualified_instructors:
                gene.instructor_id = random.choice(qualified_instructors)
        
        elif mutation_type == 'room':
            suitable_rooms = [
                room_id for room_id, room in rooms.items()
                if room.is_suitable_for_course_type(course.required_room_type)
            ]
            if suitable_rooms:
                gene.room_id = random.choice(suitable_rooms)
        
        elif mutation_type == 'time':
            available_slots = []
            for day in TIME_SLOTS['days']:
                for time_slot in TIME_SLOTS['slots']:
                    available_slots.append((day, time_slot))
            
            if available_slots:
                new_day, new_time = random.choice(available_slots)
                gene.day = new_day
                gene.time_slot = new_time

    def adaptive_crossover(self, parent1: Chromosome, parent2: Chromosome,
                          diversity: float = 0.5) -> Tuple[Chromosome, Chromosome]:
        """
        Perform adaptive crossover that adjusts strategy based on diversity.
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
            diversity: Population diversity (0-1)
        
        Returns:
            Tuple of two offspring chromosomes
        """
        # Choose crossover method based on diversity
        if diversity < 0.3:
            # Low diversity: use two-point crossover for more exploration
            return self.two_point_crossover(parent1, parent2)
        elif diversity > 0.7:
            # High diversity: use uniform crossover for more exploitation
            return self.uniform_crossover(parent1, parent2)
        else:
            # Medium diversity: use single-point crossover
            return self.single_point_crossover(parent1, parent2)

    def crossover(self, parent1: Chromosome, parent2: Chromosome,
                  diversity: float = 0.5) -> Tuple[Chromosome, Chromosome]:
        """
        Perform crossover based on configured method.
        
        Args:
            parent1: First parent chromosome
            parent2: Second parent chromosome
            diversity: Population diversity (0-1)
        
        Returns:
            Tuple of two offspring chromosomes
        """
        method = self.config.get('crossover_method', 'uniform')
        
        if method == 'uniform':
            return self.uniform_crossover(parent1, parent2)
        elif method == 'single_point':
            return self.single_point_crossover(parent1, parent2)
        elif method == 'two_point':
            return self.two_point_crossover(parent1, parent2)
        elif method == 'adaptive':
            return self.adaptive_crossover(parent1, parent2, diversity)
        else:
            self.logger.warning(f"Unknown crossover method: {method}, using uniform")
            return self.uniform_crossover(parent1, parent2)
    
    def mutate(self, chromosome: Chromosome,
               courses: Dict[str, Course],
               instructors: Dict[str, Instructor],
               rooms: Dict[str, Room],
               groups: Dict[str, Group],
               stagnation_counter: int = 0,
               diversity: float = 0.5) -> Chromosome:
        """
        Perform mutation based on configured method.
        
        Args:
            chromosome: Chromosome to mutate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Mutated chromosome
        """
        method = self.config.get('mutation_method', 'random')
        
        if method == 'random':
            return self.random_mutation(chromosome, courses, instructors, rooms, groups)
        elif method == 'swap':
            return self.swap_mutation(chromosome)
        elif method == 'adaptive':
            return self.adaptive_mutation(chromosome, courses, instructors, rooms, groups, stagnation_counter, diversity)
        else:
            self.logger.warning(f"Unknown mutation method: {method}, using random")
            return self.random_mutation(chromosome, courses, instructors, rooms, groups)
    
    def select_parents(self, population: Population, fitness_scores: List[float]) -> Chromosome:
        """
        Select a parent based on configured selection method.
        
        Args:
            population: Population to select from
            fitness_scores: Fitness scores for each chromosome
        
        Returns:
            Selected chromosome
        """
        method = self.config.get('selection_method', 'tournament')
        
        if method == 'tournament':
            return self.tournament_selection(population, fitness_scores)
        elif method == 'roulette':
            return self.roulette_wheel_selection(population, fitness_scores)
        elif method == 'rank':
            return self.rank_selection(population, fitness_scores)
        else:
            self.logger.warning(f"Unknown selection method: {method}, using tournament")
            return self.tournament_selection(population, fitness_scores)
    
    def apply_elitism(self, population: Population, fitness_scores: List[float]) -> List[Chromosome]:
        """
        Apply elitism by selecting the best chromosomes.
        
        Args:
            population: Current population
            fitness_scores: Fitness scores for each chromosome
        
        Returns:
            List of elite chromosomes
        """
        if self.elite_size <= 0:
            return []
        
        # Get indices of best chromosomes
        elite_indices = sorted(range(len(fitness_scores)), 
                             key=lambda i: fitness_scores[i], 
                             reverse=True)[:self.elite_size]
        
        # Return copies of elite chromosomes
        return [population.chromosomes[i].copy() for i in elite_indices]
    
    def calculate_diversity(self, population: Population) -> float:
        """
        Calculate population diversity based on gene distribution.
        
        Args:
            population: Population to analyze
        
        Returns:
            Diversity score (0.0 to 1.0, higher is more diverse)
        """
        if not population.chromosomes:
            return 0.0
        
        # Count unique gene combinations
        gene_combinations = set()
        
        for chromosome in population.chromosomes:
            for gene in chromosome.genes:
                combination = (gene.course_id, gene.instructor_id, 
                             gene.room_id, gene.day, gene.time_slot)
                gene_combinations.add(combination)
        
        # Calculate diversity as ratio of unique combinations to total genes
        total_genes = sum(len(chromosome.genes) for chromosome in population.chromosomes)
        if total_genes == 0:
            return 0.0
        
        return len(gene_combinations) / total_genes
