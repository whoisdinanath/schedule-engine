"""
Hard constraint checker for the timetabling system.
Enforces mandatory constraints that must not be violated.
"""

from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict

from ..ga.chromosome import Chromosome, Gene
from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger


class HardConstraintChecker:
    """
    Checks and counts hard constraint violations in timetable solutions.
    Hard constraints are mandatory requirements that must be satisfied.
    """
    
    def __init__(self):
        """Initialize the hard constraint checker."""
        self.logger = get_logger(self.__class__.__name__)
    
    def check_all_constraints(self,
                            chromosome: Chromosome,
                            courses: Dict[str, Course],
                            instructors: Dict[str, Instructor],
                            rooms: Dict[str, Room],
                            groups: Dict[str, Group]) -> Dict[str, int]:
        """
        Check all hard constraints and return violation counts.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Dictionary mapping constraint names to violation counts
        """
        violations = {}
        
        # Check each hard constraint
        violations['instructor_conflict'] = self.check_instructor_conflicts(chromosome)
        violations['room_conflict'] = self.check_room_conflicts(chromosome)
        violations['group_conflict'] = self.check_group_conflicts(chromosome, courses, groups)
        violations['room_capacity'] = self.check_room_capacity_violations(chromosome, courses, rooms, groups)
        violations['instructor_qualification'] = self.check_instructor_qualifications(chromosome, courses, instructors)
        violations['room_type_mismatch'] = self.check_room_type_mismatches(chromosome, courses, rooms)
        violations['availability_violation'] = self.check_availability_violations(chromosome, instructors, rooms)
        violations['completeness'] = self.check_completeness_violations(chromosome, courses)
        
        return violations
    
    def check_instructor_conflicts(self, chromosome: Chromosome) -> int:
        """
        Check for instructor conflicts (same instructor in multiple places at same time).
        
        Args:
            chromosome: Chromosome to check
        
        Returns:
            Number of instructor conflict violations
        """
        conflicts = 0
        instructor_schedule = defaultdict(list)
        
        # Group genes by instructor and time slot
        for gene in chromosome.genes:
            time_key = f"{gene.day}_{gene.time_slot}"
            instructor_schedule[(gene.instructor_id, time_key)].append(gene)
        
        # Count conflicts (more than one session per instructor per time slot)
        for (instructor_id, time_key), genes in instructor_schedule.items():
            if len(genes) > 1:
                conflicts += len(genes) - 1  # All but one are violations
        
        return conflicts
    
    def check_room_conflicts(self, chromosome: Chromosome) -> int:
        """
        Check for room conflicts (same room used by multiple sessions at same time).
        
        Args:
            chromosome: Chromosome to check
        
        Returns:
            Number of room conflict violations
        """
        conflicts = 0
        room_schedule = defaultdict(list)
        
        # Group genes by room and time slot
        for gene in chromosome.genes:
            time_key = f"{gene.day}_{gene.time_slot}"
            room_schedule[(gene.room_id, time_key)].append(gene)
        
        # Count conflicts (more than one session per room per time slot)
        for (room_id, time_key), genes in room_schedule.items():
            if len(genes) > 1:
                conflicts += len(genes) - 1  # All but one are violations
        
        return conflicts
    
    def check_group_conflicts(self,
                            chromosome: Chromosome,
                            courses: Dict[str, Course],
                            groups: Dict[str, Group]) -> int:
        """
        Check for student group conflicts (same group in multiple sessions at same time).
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            groups: Dictionary of group entities
        
        Returns:
            Number of group conflict violations
        """
        conflicts = 0
        group_schedule = defaultdict(lambda: defaultdict(list))
        
        # Group genes by student groups and time slot
        for gene in chromosome.genes:
            if gene.course_id in courses:
                course = courses[gene.course_id]
                time_key = f"{gene.day}_{gene.time_slot}"
                
                for group_id in course.group_ids:
                    group_schedule[group_id][time_key].append(gene)
        
        # Count conflicts for each group
        for group_id, schedule in group_schedule.items():
            for time_key, genes in schedule.items():
                if len(genes) > 1:
                    conflicts += len(genes) - 1  # All but one are violations
        
        return conflicts
    
    def check_room_capacity_violations(self,
                                     chromosome: Chromosome,
                                     courses: Dict[str, Course],
                                     rooms: Dict[str, Room],
                                     groups: Dict[str, Group]) -> int:
        """
        Check for room capacity violations (room too small for enrolled students).
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Number of capacity violations
        """
        violations = 0
        
        for gene in chromosome.genes:
            if (gene.course_id in courses and 
                gene.room_id in rooms):
                
                course = courses[gene.course_id]
                room = rooms[gene.room_id]
                
                # Calculate total students for this course
                total_students = 0
                for group_id in course.group_ids:
                    if group_id in groups:
                        total_students += groups[group_id].student_count
                
                # Check if room capacity is insufficient
                if total_students > room.capacity:
                    violations += 1
        
        return violations
    
    def check_instructor_qualifications(self,
                                      chromosome: Chromosome,
                                      courses: Dict[str, Course],
                                      instructors: Dict[str, Instructor]) -> int:
        """
        Check for instructor qualification violations (unqualified instructor assigned).
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
        
        Returns:
            Number of qualification violations
        """
        violations = 0
        
        for gene in chromosome.genes:
            if (gene.course_id in courses and 
                gene.instructor_id in instructors):
                
                course = courses[gene.course_id]
                instructor = instructors[gene.instructor_id]
                
                # Check if instructor is qualified for the course
                if not instructor.is_qualified_for_course(gene.course_id):
                    violations += 1
        
        return violations
    
    def check_room_type_mismatches(self,
                                 chromosome: Chromosome,
                                 courses: Dict[str, Course],
                                 rooms: Dict[str, Room]) -> int:
        """
        Check for room type mismatches (wrong room type for course requirements).
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            rooms: Dictionary of room entities
        
        Returns:
            Number of room type violations
        """
        violations = 0
        
        for gene in chromosome.genes:
            if (gene.course_id in courses and 
                gene.room_id in rooms):
                
                course = courses[gene.course_id]
                room = rooms[gene.room_id]
                
                # Check if room type is suitable for the course
                if not room.is_suitable_for_course_type(course.required_room_type):
                    violations += 1
        
        return violations
    
    def check_availability_violations(self,
                                    chromosome: Chromosome,
                                    instructors: Dict[str, Instructor],
                                    rooms: Dict[str, Room]) -> int:
        """
        Check for availability violations (scheduling when instructor/room not available).
        
        Args:
            chromosome: Chromosome to check
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
        
        Returns:
            Number of availability violations
        """
        violations = 0
        
        for gene in chromosome.genes:
            # Check instructor availability
            if gene.instructor_id in instructors:
                instructor = instructors[gene.instructor_id]
                if not instructor.is_available_at_slot(gene.day, gene.time_slot):
                    violations += 1
            
            # Check room availability
            if gene.room_id in rooms:
                room = rooms[gene.room_id]
                if not room.is_available_at_slot(gene.day, gene.time_slot):
                    violations += 1
        
        return violations
    
    def check_completeness_violations(self,
                                    chromosome: Chromosome,
                                    courses: Dict[str, Course]) -> int:
        """
        Check for completeness violations (missing or extra course sessions).
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
        
        Returns:
            Number of completeness violations
        """
        violations = 0
        course_sessions = chromosome.get_course_sessions()
        
        for course_id, course in courses.items():
            scheduled_sessions = course_sessions.get(course_id, 0)
            required_sessions = course.sessions_per_week
            
            # Count missing or extra sessions as violations
            if scheduled_sessions != required_sessions:
                violations += abs(scheduled_sessions - required_sessions)
        
        return violations
    
    def get_constraint_details(self,
                             chromosome: Chromosome,
                             courses: Dict[str, Course],
                             instructors: Dict[str, Instructor],
                             rooms: Dict[str, Room],
                             groups: Dict[str, Group]) -> Dict[str, List[str]]:
        """
        Get detailed information about constraint violations.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Dictionary mapping constraint names to lists of violation descriptions
        """
        details = defaultdict(list)
        
        # Instructor conflicts
        instructor_schedule = defaultdict(list)
        for gene in chromosome.genes:
            time_key = f"{gene.day}_{gene.time_slot}"
            instructor_schedule[(gene.instructor_id, time_key)].append(gene)
        
        for (instructor_id, time_key), genes in instructor_schedule.items():
            if len(genes) > 1:
                courses_list = [gene.course_id for gene in genes]
                details['instructor_conflict'].append(
                    f"Instructor {instructor_id} at {time_key}: {courses_list}"
                )
        
        # Room conflicts
        room_schedule = defaultdict(list)
        for gene in chromosome.genes:
            time_key = f"{gene.day}_{gene.time_slot}"
            room_schedule[(gene.room_id, time_key)].append(gene)
        
        for (room_id, time_key), genes in room_schedule.items():
            if len(genes) > 1:
                courses_list = [gene.course_id for gene in genes]
                details['room_conflict'].append(
                    f"Room {room_id} at {time_key}: {courses_list}"
                )
        
        # Add other detailed checks as needed...
        
        return dict(details)
    
    def is_feasible(self,
                   chromosome: Chromosome,
                   courses: Dict[str, Course],
                   instructors: Dict[str, Instructor],
                   rooms: Dict[str, Room],
                   groups: Dict[str, Group]) -> bool:
        """
        Check if a chromosome represents a feasible solution (no hard constraint violations).
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            True if feasible (no hard constraint violations), False otherwise
        """
        violations = self.check_all_constraints(chromosome, courses, instructors, rooms, groups)
        return sum(violations.values()) == 0
    
    def get_violation_summary(self, violations: Dict[str, int]) -> str:
        """
        Get a human-readable summary of violations.
        
        Args:
            violations: Dictionary of violation counts
        
        Returns:
            Summary string
        """
        if sum(violations.values()) == 0:
            return "No hard constraint violations"
        
        summary_parts = []
        for constraint, count in violations.items():
            if count > 0:
                summary_parts.append(f"{constraint}: {count}")
        
        return "Hard constraint violations - " + ", ".join(summary_parts)
