"""
Local search operators for escaping local optima in the timetabling system.
Implements hill climbing and neighborhood search strategies.
"""

import random
from typing import List, Dict, Tuple, Optional
from ..ga.chromosome import Chromosome, Gene
from ..entities import Course, Instructor, Room, Group
from ..constraints.checker import ConstraintChecker
from ..utils.logger import get_logger
from ..utils.config import TIME_SLOTS


class LocalSearch:
    """Local search operator to escape local optima."""
    
    def __init__(self, constraint_checker: ConstraintChecker):
        self.constraint_checker = constraint_checker
        self.logger = get_logger(self.__class__.__name__)
    
    def hill_climbing(self, 
                     chromosome: Chromosome,
                     courses: Dict[str, Course],
                     instructors: Dict[str, Instructor],
                     rooms: Dict[str, Room],
                     groups: Dict[str, Group],
                     max_iterations: int = 30) -> Chromosome:
        """Apply hill climbing to improve chromosome."""
        current = chromosome.copy()
        current_fitness = self._evaluate_fitness(current, courses, instructors, rooms, groups)
        
        improvements = 0
        
        for iteration in range(max_iterations):
            # Generate neighborhood solutions
            neighbors = self._generate_neighbors(current, courses, instructors, rooms, groups)
            
            # Find best neighbor
            best_neighbor = None
            best_fitness = current_fitness
            
            for neighbor in neighbors:
                neighbor_fitness = self._evaluate_fitness(neighbor, courses, instructors, rooms, groups)
                if neighbor_fitness > best_fitness:
                    best_neighbor = neighbor
                    best_fitness = neighbor_fitness
            
            # Move to best neighbor if improvement found
            if best_neighbor is not None:
                current = best_neighbor
                current_fitness = best_fitness
                improvements += 1
            else:
                break  # No improvement found
        
        if improvements > 0:
            self.logger.debug(f"Hill climbing found {improvements} improvements in {iteration + 1} iterations")
        
        return current
    
    def variable_neighborhood_search(self,
                                   chromosome: Chromosome,
                                   courses: Dict[str, Course],
                                   instructors: Dict[str, Instructor],
                                   rooms: Dict[str, Room],
                                   groups: Dict[str, Group],
                                   max_neighborhoods: int = 3) -> Chromosome:
        """Apply variable neighborhood search."""
        current = chromosome.copy()
        current_fitness = self._evaluate_fitness(current, courses, instructors, rooms, groups)
        
        for k in range(1, max_neighborhoods + 1):
            # Generate solution in k-th neighborhood
            neighbor = self._shake(current, k, courses, instructors, rooms, groups)
            
            # Apply local search
            improved = self.hill_climbing(neighbor, courses, instructors, rooms, groups, max_iterations=15)
            improved_fitness = self._evaluate_fitness(improved, courses, instructors, rooms, groups)
            
            # Move if improvement found
            if improved_fitness > current_fitness:
                current = improved
                current_fitness = improved_fitness
                k = 1  # Reset to first neighborhood
            
        return current
    
    def constraint_guided_repair(self,
                                chromosome: Chromosome,
                                courses: Dict[str, Course],
                                instructors: Dict[str, Instructor],
                                rooms: Dict[str, Room],
                                groups: Dict[str, Group]) -> Chromosome:
        """Repair chromosome by fixing constraint violations."""
        repaired = chromosome.copy()
        
        # Get current violations
        hard_violations, _ = self.constraint_checker.check_all_constraints(
            repaired, courses, instructors, rooms, groups
        )
        
        # Focus on major violations first
        violation_order = ['course_group_isolation', 'group_conflict', 'instructor_conflict', 
                          'room_conflict', 'availability_violation']
        
        for violation_type in violation_order:
            if violation_type in hard_violations and hard_violations[violation_type] > 0:
                repaired = self._repair_specific_violation(
                    repaired, violation_type, courses, instructors, rooms, groups
                )
        
        return repaired
    
    def _generate_neighbors(self,
                           chromosome: Chromosome,
                           courses: Dict[str, Course],
                           instructors: Dict[str, Instructor],
                           rooms: Dict[str, Room],
                           groups: Dict[str, Group],
                           max_neighbors: int = 50) -> List[Chromosome]:
        """Generate neighboring solutions."""
        neighbors = []
        
        # Strategy 1: Change instructor for random genes
        for _ in range(max_neighbors // 3):
            neighbor = chromosome.copy()
            gene_idx = random.randint(0, len(neighbor.genes) - 1)
            gene = neighbor.genes[gene_idx]
            
            if gene.course_id in courses:
                qualified_instructors = [
                    inst_id for inst_id, inst in instructors.items()
                    if inst.is_qualified_for_course(gene.course_id) and inst_id != gene.instructor_id
                ]
                if qualified_instructors:
                    neighbor.genes[gene_idx].instructor_id = random.choice(qualified_instructors)
                    neighbors.append(neighbor)
        
        # Strategy 2: Change room for random genes
        for _ in range(max_neighbors // 3):
            neighbor = chromosome.copy()
            gene_idx = random.randint(0, len(neighbor.genes) - 1)
            gene = neighbor.genes[gene_idx]
            
            if gene.course_id in courses:
                suitable_rooms = [
                    room_id for room_id, room in rooms.items()
                    if (room.is_suitable_for_course_type(courses[gene.course_id].required_room_type) 
                        and room_id != gene.room_id)
                ]
                if suitable_rooms:
                    neighbor.genes[gene_idx].room_id = random.choice(suitable_rooms)
                    neighbors.append(neighbor)
        
        # Strategy 3: Change time slot for random genes
        for _ in range(max_neighbors // 3):
            neighbor = chromosome.copy()
            gene_idx = random.randint(0, len(neighbor.genes) - 1)
            gene = neighbor.genes[gene_idx]
            
            available_slots = []
            for day in TIME_SLOTS['days']:
                for time_slot in TIME_SLOTS['slots']:
                    if f"{day}_{time_slot}" != f"{gene.day}_{gene.time_slot}":
                        available_slots.append((day, time_slot))
            
            if available_slots:
                new_day, new_time = random.choice(available_slots)
                neighbor.genes[gene_idx].day = new_day
                neighbor.genes[gene_idx].time_slot = new_time
                neighbors.append(neighbor)
        
        return neighbors
    
    def _shake(self,
               chromosome: Chromosome,
               k: int,
               courses: Dict[str, Course],
               instructors: Dict[str, Instructor],
               rooms: Dict[str, Room],
               groups: Dict[str, Group]) -> Chromosome:
        """Shake the solution by making k random changes."""
        shaken = chromosome.copy()
        
        for _ in range(k):
            if len(shaken.genes) == 0:
                break
                
            gene_idx = random.randint(0, len(shaken.genes) - 1)
            gene = shaken.genes[gene_idx]
            
            # Randomly choose what to change
            change_type = random.choice(['instructor', 'room', 'time'])
            
            if change_type == 'instructor' and gene.course_id in courses:
                qualified_instructors = [
                    inst_id for inst_id, inst in instructors.items()
                    if inst.is_qualified_for_course(gene.course_id)
                ]
                if qualified_instructors:
                    shaken.genes[gene_idx].instructor_id = random.choice(qualified_instructors)
            
            elif change_type == 'room' and gene.course_id in courses:
                suitable_rooms = [
                    room_id for room_id, room in rooms.items()
                    if room.is_suitable_for_course_type(courses[gene.course_id].required_room_type)
                ]
                if suitable_rooms:
                    shaken.genes[gene_idx].room_id = random.choice(suitable_rooms)
            
            elif change_type == 'time':
                new_day = random.choice(TIME_SLOTS['days'])
                new_time = random.choice(TIME_SLOTS['slots'])
                shaken.genes[gene_idx].day = new_day
                shaken.genes[gene_idx].time_slot = new_time
        
        return shaken
    
    def _repair_specific_violation(self,
                                  chromosome: Chromosome,
                                  violation_type: str,
                                  courses: Dict[str, Course],
                                  instructors: Dict[str, Instructor],
                                  rooms: Dict[str, Room],
                                  groups: Dict[str, Group]) -> Chromosome:
        """Repair specific type of constraint violation."""
        repaired = chromosome.copy()
        
        if violation_type == 'course_group_isolation':
            # Fix multiple groups from same course at same time
            repaired = self._fix_course_group_isolation(repaired, courses, groups)
        
        elif violation_type == 'group_conflict':
            # Fix same group scheduled multiple times
            repaired = self._fix_group_conflicts(repaired, groups)
        
        elif violation_type == 'instructor_conflict':
            # Fix instructor double-booking
            repaired = self._fix_instructor_conflicts(repaired, instructors)
        
        elif violation_type == 'room_conflict':
            # Fix room double-booking
            repaired = self._fix_room_conflicts(repaired, rooms)
        
        return repaired
    
    def _fix_course_group_isolation(self, chromosome: Chromosome, courses: Dict[str, Course], groups: Dict[str, Group]) -> Chromosome:
        """Fix course group isolation violations."""
        # Group genes by course and time slot
        from collections import defaultdict
        course_time_groups = defaultdict(list)
        
        for i, gene in enumerate(chromosome.genes):
            time_key = f"{gene.day}_{gene.time_slot}"
            course_time_groups[(gene.course_id, time_key)].append(i)
        
        # Fix conflicts by moving genes to different time slots
        for (course_id, time_key), gene_indices in course_time_groups.items():
            if len(gene_indices) > 1:
                # Keep first gene, move others
                for i in range(1, len(gene_indices)):
                    gene_idx = gene_indices[i]
                    # Find alternative time slot
                    new_day = random.choice(TIME_SLOTS['days'])
                    new_time = random.choice(TIME_SLOTS['slots'])
                    chromosome.genes[gene_idx].day = new_day
                    chromosome.genes[gene_idx].time_slot = new_time
        
        return chromosome
    
    def _fix_group_conflicts(self, chromosome: Chromosome, groups: Dict[str, Group]) -> Chromosome:
        """Fix group conflicts (same group scheduled multiple times)."""
        from collections import defaultdict
        group_time_slots = defaultdict(list)
        
        for i, gene in enumerate(chromosome.genes):
            if gene.group_id:
                time_key = f"{gene.day}_{gene.time_slot}"
                group_time_slots[(gene.group_id, time_key)].append(i)
        
        # Fix conflicts by moving genes
        for (group_id, time_key), gene_indices in group_time_slots.items():
            if len(gene_indices) > 1:
                # Keep first gene, move others
                for i in range(1, len(gene_indices)):
                    gene_idx = gene_indices[i]
                    new_day = random.choice(TIME_SLOTS['days'])
                    new_time = random.choice(TIME_SLOTS['slots'])
                    chromosome.genes[gene_idx].day = new_day
                    chromosome.genes[gene_idx].time_slot = new_time
        
        return chromosome
    
    def _fix_instructor_conflicts(self, chromosome: Chromosome, instructors: Dict[str, Instructor]) -> Chromosome:
        """Fix instructor conflicts."""
        from collections import defaultdict
        instructor_time_slots = defaultdict(list)
        
        for i, gene in enumerate(chromosome.genes):
            time_key = f"{gene.day}_{gene.time_slot}"
            instructor_time_slots[(gene.instructor_id, time_key)].append(i)
        
        # Fix conflicts by moving genes
        for (instructor_id, time_key), gene_indices in instructor_time_slots.items():
            if len(gene_indices) > 1:
                for i in range(1, len(gene_indices)):
                    gene_idx = gene_indices[i]
                    new_day = random.choice(TIME_SLOTS['days'])
                    new_time = random.choice(TIME_SLOTS['slots'])
                    chromosome.genes[gene_idx].day = new_day
                    chromosome.genes[gene_idx].time_slot = new_time
        
        return chromosome
    
    def _fix_room_conflicts(self, chromosome: Chromosome, rooms: Dict[str, Room]) -> Chromosome:
        """Fix room conflicts."""
        from collections import defaultdict
        room_time_slots = defaultdict(list)
        
        for i, gene in enumerate(chromosome.genes):
            time_key = f"{gene.day}_{gene.time_slot}"
            room_time_slots[(gene.room_id, time_key)].append(i)
        
        # Fix conflicts by moving genes
        for (room_id, time_key), gene_indices in room_time_slots.items():
            if len(gene_indices) > 1:
                for i in range(1, len(gene_indices)):
                    gene_idx = gene_indices[i]
                    new_day = random.choice(TIME_SLOTS['days'])
                    new_time = random.choice(TIME_SLOTS['slots'])
                    chromosome.genes[gene_idx].day = new_day
                    chromosome.genes[gene_idx].time_slot = new_time
        
        return chromosome
    
    def _evaluate_fitness(self,
                         chromosome: Chromosome,
                         courses: Dict[str, Course],
                         instructors: Dict[str, Instructor],
                         rooms: Dict[str, Room],
                         groups: Dict[str, Group]) -> float:
        """Evaluate fitness of chromosome."""
        hard_violations, soft_penalties = self.constraint_checker.check_all_constraints(
            chromosome, courses, instructors, rooms, groups
        )
        
        total_hard = sum(hard_violations.values())
        total_soft = sum(soft_penalties.values())
        
        return -(1000 * total_hard + total_soft)
