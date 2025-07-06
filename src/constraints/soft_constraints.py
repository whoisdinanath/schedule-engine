"""
Soft constraint checker for the timetabling system.
Evaluates preferences and quality measures that improve solution quality.
"""

from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict
from datetime import datetime, timedelta

from ..ga.chromosome import Chromosome, Gene
from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger


class SoftConstraintChecker:
    """
    Checks and evaluates soft constraint violations in timetable solutions.
    Soft constraints represent preferences and quality measures.
    """
    
    def __init__(self):
        """Initialize the soft constraint checker."""
        self.logger = get_logger(self.__class__.__name__)
    
    def check_all_constraints(self,
                            chromosome: Chromosome,
                            courses: Dict[str, Course],
                            instructors: Dict[str, Instructor],
                            rooms: Dict[str, Room],
                            groups: Dict[str, Group]) -> Dict[str, float]:
        """
        Check all soft constraints and return penalty scores.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Dictionary mapping constraint names to penalty scores
        """
        penalties = {}
        
        # Check each soft constraint
        penalties['instructor_preference'] = self.check_instructor_preferences(chromosome, instructors)
        penalties['room_utilization'] = self.check_room_utilization(chromosome, courses, rooms, groups)
        penalties['schedule_compactness'] = self.check_schedule_compactness(chromosome, instructors, groups, courses)
        penalties['workload_balance'] = self.check_workload_balance(chromosome, instructors, courses)
        penalties['student_break_time'] = self.check_student_break_time(chromosome, courses, groups)
        penalties['room_consistency'] = self.check_room_consistency(chromosome, courses)
        penalties['time_slot_distribution'] = self.check_time_slot_distribution(chromosome)
        penalties['lunch_break_respect'] = self.check_lunch_break_respect(chromosome, courses, groups)
        penalties['early_late_penalty'] = self.check_early_late_penalty(chromosome)
        penalties['consecutive_classes'] = self.check_consecutive_classes(chromosome, courses, groups)
        
        return penalties
    
    def check_instructor_preferences(self,
                                   chromosome: Chromosome,
                                   instructors: Dict[str, Instructor]) -> float:
        """
        Check instructor time preferences.
        
        Args:
            chromosome: Chromosome to check
            instructors: Dictionary of instructor entities
        
        Returns:
            Penalty score for preference violations
        """
        penalty = 0.0
        total_sessions = 0
        
        for gene in chromosome.genes:
            if gene.instructor_id in instructors:
                instructor = instructors[gene.instructor_id]
                total_sessions += 1
                
                # Calculate preference score (0 = not preferred, 1 = highly preferred)
                preference_score = instructor.calculate_preference_score(gene.day, gene.time_slot)
                
                # Penalty is inverse of preference (higher penalty for lower preference)
                penalty += (1.0 - preference_score)
        
        # Normalize by total sessions
        return penalty / total_sessions if total_sessions > 0 else 0.0
    
    def check_room_utilization(self,
                             chromosome: Chromosome,
                             courses: Dict[str, Course],
                             rooms: Dict[str, Room],
                             groups: Dict[str, Group]) -> float:
        """
        Check room utilization efficiency.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Penalty score for poor room utilization
        """
        penalty = 0.0
        total_sessions = 0
        
        for gene in chromosome.genes:
            if (gene.course_id in courses and 
                gene.room_id in rooms):
                
                course = courses[gene.course_id]
                room = rooms[gene.room_id]
                total_sessions += 1
                
                # Calculate total students for this course
                total_students = 0
                for group_id in course.group_ids:
                    if group_id in groups:
                        total_students += groups[group_id].student_count
                
                # Get utilization score (1.0 = optimal, 0.0 = poor)
                utilization_score = room.calculate_utilization_score(total_students)
                
                # Penalty is inverse of utilization
                penalty += (1.0 - utilization_score)
        
        # Normalize by total sessions
        return penalty / total_sessions if total_sessions > 0 else 0.0
    
    def check_schedule_compactness(self,
                                 chromosome: Chromosome,
                                 instructors: Dict[str, Instructor],
                                 groups: Dict[str, Group],
                                 courses: Dict[str, Course]) -> float:
        """
        Check schedule compactness (minimize gaps in schedules).
        
        Args:
            chromosome: Chromosome to check
            instructors: Dictionary of instructor entities
            groups: Dictionary of group entities
            courses: Dictionary of course entities
        
        Returns:
            Penalty score for schedule fragmentation
        """
        penalty = 0.0
        
        # Check instructor schedule compactness
        penalty += self._check_instructor_compactness(chromosome, instructors)
        
        # Check student group schedule compactness
        penalty += self._check_group_compactness(chromosome, groups, courses)
        
        return penalty / 2.0  # Average of instructor and group penalties
    
    def _check_instructor_compactness(self,
                                    chromosome: Chromosome,
                                    instructors: Dict[str, Instructor]) -> float:
        """Check compactness of instructor schedules."""
        penalty = 0.0
        instructor_count = 0
        
        for instructor_id in instructors.keys():
            instructor_genes = chromosome.get_genes_by_instructor(instructor_id)
            if not instructor_genes:
                continue
            
            instructor_count += 1
            daily_schedules = defaultdict(list)
            
            # Group by day
            for gene in instructor_genes:
                daily_schedules[gene.day].append(gene)
            
            # Check compactness for each day
            for day, daily_genes in daily_schedules.items():
                if len(daily_genes) > 1:
                    # Sort by time slot
                    daily_genes.sort(key=lambda g: g.time_slot)
                    
                    # Count gaps between sessions
                    gaps = self._count_time_gaps(daily_genes)
                    penalty += gaps * 0.1  # 0.1 penalty per gap
        
        return penalty / instructor_count if instructor_count > 0 else 0.0
    
    def _check_group_compactness(self,
                               chromosome: Chromosome,
                               groups: Dict[str, Group],
                               courses: Dict[str, Course]) -> float:
        """Check compactness of student group schedules."""
        penalty = 0.0
        group_count = 0
        
        for group_id, group in groups.items():
            group_genes = []
            
            # Find all sessions for this group
            for gene in chromosome.genes:
                if (gene.course_id in courses and 
                    group_id in courses[gene.course_id].group_ids):
                    group_genes.append(gene)
            
            if not group_genes:
                continue
            
            group_count += 1
            daily_schedules = defaultdict(list)
            
            # Group by day
            for gene in group_genes:
                daily_schedules[gene.day].append(gene)
            
            # Check compactness for each day
            for day, daily_genes in daily_schedules.items():
                if len(daily_genes) > 1:
                    # Sort by time slot
                    daily_genes.sort(key=lambda g: g.time_slot)
                    
                    # Count gaps between sessions
                    gaps = self._count_time_gaps(daily_genes)
                    penalty += gaps * 0.1  # 0.1 penalty per gap
        
        return penalty / group_count if group_count > 0 else 0.0
    
    def _count_time_gaps(self, sorted_genes: List[Gene]) -> int:
        """Count gaps in a sorted list of genes."""
        gaps = 0
        
        for i in range(len(sorted_genes) - 1):
            current_end = self._get_session_end_time(sorted_genes[i])
            next_start = self._get_session_start_time(sorted_genes[i + 1])
            
            # If there's more than a 30-minute gap, count it
            if self._time_difference_minutes(current_end, next_start) > 30:
                gaps += 1
        
        return gaps
    
    def check_workload_balance(self,
                             chromosome: Chromosome,
                             instructors: Dict[str, Instructor],
                             courses: Dict[str, Course]) -> float:
        """
        Check instructor workload balance.
        
        Args:
            chromosome: Chromosome to check
            instructors: Dictionary of instructor entities
            courses: Dictionary of course entities
        
        Returns:
            Penalty score for workload imbalance
        """
        if not instructors:
            return 0.0
        
        # Calculate workload for each instructor
        workloads = {}
        for instructor_id in instructors.keys():
            instructor_genes = chromosome.get_genes_by_instructor(instructor_id)
            
            # Calculate total hours
            total_hours = 0
            for gene in instructor_genes:
                if gene.course_id in courses:
                    total_hours += courses[gene.course_id].duration / 60.0  # Convert to hours
            
            workloads[instructor_id] = total_hours
        
        if not workloads:
            return 0.0
        
        # Calculate workload statistics
        workload_values = list(workloads.values())
        avg_workload = sum(workload_values) / len(workload_values)
        
        # Calculate penalty based on deviation from average
        penalty = 0.0
        for workload in workload_values:
            deviation = abs(workload - avg_workload)
            penalty += deviation / avg_workload if avg_workload > 0 else 0
        
        return penalty / len(workloads)
    
    def check_student_break_time(self,
                               chromosome: Chromosome,
                               courses: Dict[str, Course],
                               groups: Dict[str, Group]) -> float:
        """
        Check adequate break time for student groups.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            groups: Dictionary of group entities
        
        Returns:
            Penalty score for insufficient break time
        """
        penalty = 0.0
        group_count = 0
        
        for group_id, group in groups.items():
            group_genes = []
            
            # Find all sessions for this group
            for gene in chromosome.genes:
                if (gene.course_id in courses and 
                    group_id in courses[gene.course_id].group_ids):
                    group_genes.append(gene)
            
            if len(group_genes) < 2:
                continue
            
            group_count += 1
            daily_schedules = defaultdict(list)
            
            # Group by day
            for gene in group_genes:
                daily_schedules[gene.day].append(gene)
            
            # Check break times for each day
            for day, daily_genes in daily_schedules.items():
                if len(daily_genes) > 1:
                    # Sort by time slot
                    daily_genes.sort(key=lambda g: g.time_slot)
                    
                    # Check breaks between consecutive sessions
                    for i in range(len(daily_genes) - 1):
                        current_end = self._get_session_end_time(daily_genes[i])
                        next_start = self._get_session_start_time(daily_genes[i + 1])
                        
                        break_time = self._time_difference_minutes(current_end, next_start)
                        
                        # Penalty if break is too short (less than preferred)
                        min_break = group.preferred_break_duration
                        if break_time < min_break:
                            penalty += (min_break - break_time) / min_break
        
        return penalty / group_count if group_count > 0 else 0.0
    
    def check_room_consistency(self,
                             chromosome: Chromosome,
                             courses: Dict[str, Course]) -> float:
        """
        Check room consistency for courses that require it.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
        
        Returns:
            Penalty score for room inconsistency
        """
        penalty = 0.0
        course_count = 0
        
        for course_id, course in courses.items():
            if course.room_consistency_required:
                course_genes = chromosome.get_genes_by_course(course_id)
                
                if len(course_genes) > 1:
                    course_count += 1
                    
                    # Get unique rooms used for this course
                    rooms_used = set(gene.room_id for gene in course_genes)
                    
                    # Penalty for using multiple rooms when consistency is required
                    if len(rooms_used) > 1:
                        penalty += (len(rooms_used) - 1) / len(course_genes)
        
        return penalty / course_count if course_count > 0 else 0.0
    
    def check_time_slot_distribution(self, chromosome: Chromosome) -> float:
        """
        Check even distribution of sessions across time slots.
        
        Args:
            chromosome: Chromosome to check
        
        Returns:
            Penalty score for uneven time slot distribution
        """
        if not chromosome.genes:
            return 0.0
        
        # Count usage of each time slot
        slot_usage = chromosome.get_time_slot_usage()
        
        if not slot_usage:
            return 0.0
        
        # Calculate average usage
        usage_values = list(slot_usage.values())
        avg_usage = sum(usage_values) / len(usage_values)
        
        # Calculate penalty based on deviation from average
        penalty = 0.0
        for usage in usage_values:
            deviation = abs(usage - avg_usage)
            penalty += deviation / avg_usage if avg_usage > 0 else 0
        
        return penalty / len(usage_values)
    
    def check_lunch_break_respect(self,
                                chromosome: Chromosome,
                                courses: Dict[str, Course],
                                groups: Dict[str, Group]) -> float:
        """
        Check respect for lunch break requirements.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            groups: Dictionary of group entities
        
        Returns:
            Penalty score for lunch break violations
        """
        penalty = 0.0
        group_count = 0
        
        for group_id, group in groups.items():
            if not group.lunch_break_required:
                continue
            
            group_genes = []
            
            # Find all sessions for this group
            for gene in chromosome.genes:
                if (gene.course_id in courses and 
                    group_id in courses[gene.course_id].group_ids):
                    group_genes.append(gene)
            
            if not group_genes:
                continue
            
            group_count += 1
            daily_schedules = defaultdict(list)
            
            # Group by day
            for gene in group_genes:
                daily_schedules[gene.day].append(gene)
            
            # Check lunch break for each day
            for day, daily_genes in daily_schedules.items():
                if len(daily_genes) > 2:  # Only check if more than 2 sessions
                    # Sort by time slot
                    daily_genes.sort(key=lambda g: g.time_slot)
                    
                    # Check if there's adequate lunch break
                    if not self._has_adequate_lunch_break(daily_genes, group, courses):
                        penalty += 1.0
        
        return penalty / group_count if group_count > 0 else 0.0
    
    def check_early_late_penalty(self, chromosome: Chromosome) -> float:
        """
        Apply penalty for very early or late classes.
        
        Args:
            chromosome: Chromosome to check
        
        Returns:
            Penalty score for early/late scheduling
        """
        penalty = 0.0
        total_sessions = len(chromosome.genes)
        
        if total_sessions == 0:
            return 0.0
        
        for gene in chromosome.genes:
            start_time = self._get_session_start_time(gene)
            
            # Penalty for very early sessions (before 8:30 AM)
            if self._time_to_minutes(start_time) < 8.5 * 60:
                penalty += 0.5
            
            # Penalty for very late sessions (after 5:30 PM)
            elif self._time_to_minutes(start_time) > 17.5 * 60:
                penalty += 0.5
        
        return penalty / total_sessions
    
    def check_consecutive_classes(self,
                                chromosome: Chromosome,
                                courses: Dict[str, Course],
                                groups: Dict[str, Group]) -> float:
        """
        Check preference for consecutive classes (when appropriate).
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            groups: Dictionary of group entities
        
        Returns:
            Penalty score for lack of beneficial consecutive scheduling
        """
        # This is a complex constraint that depends on course types and preferences
        # For now, return a placeholder implementation
        return 0.0
    
    def _get_session_start_time(self, gene: Gene) -> str:
        """Extract start time from time slot."""
        return gene.time_slot.split('-')[0]
    
    def _get_session_end_time(self, gene: Gene) -> str:
        """Extract end time from time slot."""
        return gene.time_slot.split('-')[1]
    
    def _time_to_minutes(self, time_str: str) -> int:
        """Convert time string (HH:MM) to minutes since midnight."""
        try:
            hours, minutes = map(int, time_str.split(':'))
            return hours * 60 + minutes
        except:
            return 0
    
    def _time_difference_minutes(self, time1: str, time2: str) -> int:
        """Calculate difference between two times in minutes."""
        return self._time_to_minutes(time2) - self._time_to_minutes(time1)
    
    def _has_adequate_lunch_break(self,
                                sorted_genes: List[Gene],
                                group: Group,
                                courses: Dict[str, Course]) -> bool:
        """Check if there's an adequate lunch break in the daily schedule."""
        lunch_start = self._time_to_minutes(group.lunch_break_start)
        lunch_end = lunch_start + group.lunch_break_duration
        
        # Check if any session overlaps with lunch time
        for gene in sorted_genes:
            session_start = self._time_to_minutes(self._get_session_start_time(gene))
            session_end = self._time_to_minutes(self._get_session_end_time(gene))
            
            # Check for overlap with lunch break
            if not (session_end <= lunch_start or session_start >= lunch_end):
                return False  # Lunch break is violated
        
        return True
    
    def get_penalty_summary(self, penalties: Dict[str, float]) -> str:
        """
        Get a human-readable summary of soft constraint penalties.
        
        Args:
            penalties: Dictionary of penalty scores
        
        Returns:
            Summary string
        """
        if sum(penalties.values()) == 0:
            return "No soft constraint penalties"
        
        summary_parts = []
        for constraint, penalty in penalties.items():
            if penalty > 0:
                summary_parts.append(f"{constraint}: {penalty:.3f}")
        
        return "Soft constraint penalties - " + ", ".join(summary_parts)
