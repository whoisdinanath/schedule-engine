"""
Chromosome and Gene classes for the genetic algorithm.
Represents individual solutions in the population.
"""

from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
import random
import copy
from collections import defaultdict

from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger


@dataclass
class Gene:
    """
    Represents a single scheduled session (gene) in a chromosome.
    
    Attributes:
        course_id: ID of the course being scheduled
        instructor_id: ID of the assigned instructor
        room_id: ID of the assigned room
        day: Day of the week (e.g., 'monday')
        time_slot: Time slot (e.g., '09:00-10:30')
        session_index: Index of this session within the course's weekly sessions
    """
    
    course_id: str
    instructor_id: str
    room_id: str
    day: str
    time_slot: str
    session_index: int = 0
    
    def __hash__(self) -> int:
        """Make Gene hashable for use in sets and as dict keys."""
        return hash((self.course_id, self.instructor_id, self.room_id, 
                    self.day, self.time_slot, self.session_index))
    
    def __eq__(self, other) -> bool:
        """Check equality of two genes."""
        if not isinstance(other, Gene):
            return False
        return (self.course_id == other.course_id and
                self.instructor_id == other.instructor_id and
                self.room_id == other.room_id and
                self.day == other.day and
                self.time_slot == other.time_slot and
                self.session_index == other.session_index)
    
    def get_time_key(self) -> str:
        """Get a unique key for the time slot."""
        return f"{self.day}_{self.time_slot}"
    
    def conflicts_with(self, other: 'Gene') -> bool:
        """
        Check if this gene conflicts with another gene.
        
        Args:
            other: Another gene to check conflict with
        
        Returns:
            True if there's a conflict (same time, same resource)
        """
        if self.day != other.day or self.time_slot != other.time_slot:
            return False
        
        # Check for instructor conflict
        if self.instructor_id == other.instructor_id:
            return True
        
        # Check for room conflict
        if self.room_id == other.room_id:
            return True
        
        return False
    
    def __str__(self) -> str:
        return f"Gene({self.course_id}, {self.instructor_id}, {self.room_id}, {self.day} {self.time_slot})"
    
    def __repr__(self) -> str:
        return self.__str__()


class Chromosome:
    """
    Represents a complete timetable solution as a collection of genes.
    Each chromosome contains all scheduled sessions for all courses.
    """
    
    def __init__(self, genes: Optional[List[Gene]] = None):
        """
        Initialize chromosome with optional genes.
        
        Args:
            genes: List of genes representing scheduled sessions
        """
        self.genes: List[Gene] = genes if genes is not None else []
        self.fitness: float = float('-inf')
        self.fitness_calculated: bool = False
        self.constraint_violations: Dict[str, int] = {}
        self.logger = get_logger(self.__class__.__name__)
    
    def add_gene(self, gene: Gene) -> None:
        """Add a gene to the chromosome."""
        self.genes.append(gene)
        self.fitness_calculated = False
    
    def remove_gene(self, index: int) -> Gene:
        """Remove and return a gene at the specified index."""
        if 0 <= index < len(self.genes):
            gene = self.genes.pop(index)
            self.fitness_calculated = False
            return gene
        raise IndexError(f"Gene index {index} out of range")
    
    def get_gene(self, index: int) -> Gene:
        """Get gene at specified index."""
        return self.genes[index]
    
    def set_gene(self, index: int, gene: Gene) -> None:
        """Set gene at specified index."""
        self.genes[index] = gene
        self.fitness_calculated = False
    
    def size(self) -> int:
        """Get number of genes in chromosome."""
        return len(self.genes)
    
    def copy(self) -> 'Chromosome':
        """Create a deep copy of the chromosome."""
        new_genes = [copy.deepcopy(gene) for gene in self.genes]
        new_chromosome = Chromosome(new_genes)
        new_chromosome.fitness = self.fitness
        new_chromosome.fitness_calculated = self.fitness_calculated
        new_chromosome.constraint_violations = self.constraint_violations.copy()
        return new_chromosome
    
    def get_genes_by_course(self, course_id: str) -> List[Gene]:
        """Get all genes for a specific course."""
        return [gene for gene in self.genes if gene.course_id == course_id]
    
    def get_genes_by_instructor(self, instructor_id: str) -> List[Gene]:
        """Get all genes assigned to a specific instructor."""
        return [gene for gene in self.genes if gene.instructor_id == instructor_id]
    
    def get_genes_by_room(self, room_id: str) -> List[Gene]:
        """Get all genes assigned to a specific room."""
        return [gene for gene in self.genes if gene.room_id == room_id]
    
    def get_genes_by_day(self, day: str) -> List[Gene]:
        """Get all genes scheduled on a specific day."""
        return [gene for gene in self.genes if gene.day == day]
    
    def get_genes_by_time_slot(self, day: str, time_slot: str) -> List[Gene]:
        """Get all genes scheduled at a specific time slot."""
        return [gene for gene in self.genes 
                if gene.day == day and gene.time_slot == time_slot]
    
    def get_instructor_schedule(self, instructor_id: str) -> Dict[str, List[Gene]]:
        """
        Get instructor's weekly schedule organized by day.
        
        Args:
            instructor_id: ID of the instructor
        
        Returns:
            Dictionary mapping days to lists of genes
        """
        schedule = defaultdict(list)
        instructor_genes = self.get_genes_by_instructor(instructor_id)
        
        for gene in instructor_genes:
            schedule[gene.day].append(gene)
        
        # Sort genes by time slot for each day
        for day in schedule:
            schedule[day].sort(key=lambda g: g.time_slot)
        
        return dict(schedule)
    
    def get_room_schedule(self, room_id: str) -> Dict[str, List[Gene]]:
        """
        Get room's weekly schedule organized by day.
        
        Args:
            room_id: ID of the room
        
        Returns:
            Dictionary mapping days to lists of genes
        """
        schedule = defaultdict(list)
        room_genes = self.get_genes_by_room(room_id)
        
        for gene in room_genes:
            schedule[gene.day].append(gene)
        
        # Sort genes by time slot for each day
        for day in schedule:
            schedule[day].sort(key=lambda g: g.time_slot)
        
        return dict(schedule)
    
    def get_conflicts(self) -> List[Tuple[Gene, Gene]]:
        """
        Find all conflicting gene pairs in the chromosome.
        
        Returns:
            List of tuples containing conflicting gene pairs
        """
        conflicts = []
        
        for i in range(len(self.genes)):
            for j in range(i + 1, len(self.genes)):
                if self.genes[i].conflicts_with(self.genes[j]):
                    conflicts.append((self.genes[i], self.genes[j]))
        
        return conflicts
    
    def has_conflicts(self) -> bool:
        """Check if chromosome has any conflicts."""
        return len(self.get_conflicts()) > 0
    
    def get_time_slot_usage(self) -> Dict[str, int]:
        """
        Get usage count for each time slot.
        
        Returns:
            Dictionary mapping time slot keys to usage counts
        """
        usage = defaultdict(int)
        for gene in self.genes:
            usage[gene.get_time_key()] += 1
        return dict(usage)
    
    def get_instructor_workload(self) -> Dict[str, int]:
        """
        Get session count for each instructor.
        
        Returns:
            Dictionary mapping instructor IDs to session counts
        """
        workload = defaultdict(int)
        for gene in self.genes:
            workload[gene.instructor_id] += 1
        return dict(workload)
    
    def get_room_utilization(self) -> Dict[str, int]:
        """
        Get usage count for each room.
        
        Returns:
            Dictionary mapping room IDs to usage counts
        """
        utilization = defaultdict(int)
        for gene in self.genes:
            utilization[gene.room_id] += 1
        return dict(utilization)
    
    def get_course_sessions(self) -> Dict[str, int]:
        """
        Get session count for each course.
        
        Returns:
            Dictionary mapping course IDs to session counts
        """
        sessions = defaultdict(int)
        for gene in self.genes:
            sessions[gene.course_id] += 1
        return dict(sessions)
    
    def is_complete(self, courses: Dict[str, Course]) -> bool:
        """
        Check if chromosome represents a complete timetable.
        
        Args:
            courses: Dictionary of course entities
        
        Returns:
            True if all required sessions are scheduled
        """
        course_sessions = self.get_course_sessions()
        
        for course_id, course in courses.items():
            scheduled_sessions = course_sessions.get(course_id, 0)
            if scheduled_sessions != course.sessions_per_week:
                return False
        
        return True
    
    def validate_structure(self, courses: Dict[str, Course],
                          instructors: Dict[str, Instructor],
                          rooms: Dict[str, Room]) -> List[str]:
        """
        Validate chromosome structure and return list of issues.
        
        Args:
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
        
        Returns:
            List of validation error messages
        """
        issues = []
        
        for i, gene in enumerate(self.genes):
            # Check if entities exist
            if gene.course_id not in courses:
                issues.append(f"Gene {i}: Unknown course {gene.course_id}")
            
            if gene.instructor_id not in instructors:
                issues.append(f"Gene {i}: Unknown instructor {gene.instructor_id}")
            
            if gene.room_id not in rooms:
                issues.append(f"Gene {i}: Unknown room {gene.room_id}")
            
            # Check qualifications and suitability
            if (gene.course_id in courses and 
                gene.instructor_id in instructors and
                not instructors[gene.instructor_id].is_qualified_for_course(gene.course_id)):
                issues.append(f"Gene {i}: Instructor {gene.instructor_id} not qualified for course {gene.course_id}")
            
            if (gene.course_id in courses and 
                gene.room_id in rooms and
                not rooms[gene.room_id].is_suitable_for_course_type(courses[gene.course_id].required_room_type)):
                issues.append(f"Gene {i}: Room {gene.room_id} not suitable for course {gene.course_id}")
        
        return issues
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive statistics about the chromosome.
        
        Returns:
            Dictionary containing various statistics
        """
        return {
            'total_genes': len(self.genes),
            'unique_courses': len(set(gene.course_id for gene in self.genes)),
            'unique_instructors': len(set(gene.instructor_id for gene in self.genes)),
            'unique_rooms': len(set(gene.room_id for gene in self.genes)),
            'unique_time_slots': len(set(gene.get_time_key() for gene in self.genes)),
            'conflicts': len(self.get_conflicts()),
            'fitness': self.fitness,
            'fitness_calculated': self.fitness_calculated,
            'constraint_violations': self.constraint_violations.copy()
        }
    
    def __len__(self) -> int:
        """Get number of genes in chromosome."""
        return len(self.genes)
    
    def __iter__(self):
        """Make chromosome iterable over genes."""
        return iter(self.genes)
    
    def __getitem__(self, index: int) -> Gene:
        """Get gene by index."""
        return self.genes[index]
    
    def __setitem__(self, index: int, gene: Gene) -> None:
        """Set gene by index."""
        self.genes[index] = gene
        self.fitness_calculated = False
    
    def __str__(self) -> str:
        return f"Chromosome({len(self.genes)} genes, fitness={self.fitness:.4f})"
    
    def __repr__(self) -> str:
        return self.__str__()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert chromosome to dictionary format."""
        return {
            'genes': [
                {
                    'course_id': gene.course_id,
                    'instructor_id': gene.instructor_id,
                    'room_id': gene.room_id,
                    'day': gene.day,
                    'time_slot': gene.time_slot,
                    'session_index': gene.session_index
                }
                for gene in self.genes
            ],
            'fitness': self.fitness,
            'constraint_violations': self.constraint_violations,
            'statistics': self.get_statistics()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Chromosome':
        """Create chromosome from dictionary format."""
        genes = [
            Gene(
                course_id=gene_data['course_id'],
                instructor_id=gene_data['instructor_id'],
                room_id=gene_data['room_id'],
                day=gene_data['day'],
                time_slot=gene_data['time_slot'],
                session_index=gene_data.get('session_index', 0)
            )
            for gene_data in data['genes']
        ]
        
        chromosome = cls(genes)
        chromosome.fitness = data.get('fitness', float('-inf'))
        chromosome.fitness_calculated = chromosome.fitness != float('-inf')
        chromosome.constraint_violations = data.get('constraint_violations', {})
        
        return chromosome
