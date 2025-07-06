"""
Main constraint checker that combines hard and soft constraint checking.
"""

from typing import Dict, List, Tuple, Any

from .hard_constraints import HardConstraintChecker
from .soft_constraints import SoftConstraintChecker
from ..ga.chromosome import Chromosome
from ..entities import Course, Instructor, Room, Group
from ..utils.logger import get_logger
from ..utils.config import CONSTRAINT_WEIGHTS


class ConstraintChecker:
    """
    Main constraint checker that combines hard and soft constraint evaluation.
    Provides a unified interface for constraint checking and penalty calculation.
    """
    
    def __init__(self):
        """Initialize the constraint checker."""
        self.logger = get_logger(self.__class__.__name__)
        self.hard_checker = HardConstraintChecker()
        self.soft_checker = SoftConstraintChecker()
        self.constraint_weights = CONSTRAINT_WEIGHTS
    
    def check_all_constraints(self,
                            chromosome: Chromosome,
                            courses: Dict[str, Course],
                            instructors: Dict[str, Instructor],
                            rooms: Dict[str, Room],
                            groups: Dict[str, Group]) -> Tuple[Dict[str, int], Dict[str, float]]:
        """
        Check all constraints (hard and soft) for a chromosome.
        
        Args:
            chromosome: Chromosome to evaluate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Tuple of (hard_violations, soft_penalties)
        """
        # Check hard constraints
        hard_violations = self.hard_checker.check_all_constraints(
            chromosome, courses, instructors, rooms, groups
        )
        
        # Check soft constraints
        soft_penalties = self.soft_checker.check_all_constraints(
            chromosome, courses, instructors, rooms, groups
        )
        
        # Store results in chromosome for caching
        chromosome.constraint_violations = {
            'hard': hard_violations,
            'soft': soft_penalties
        }
        
        return hard_violations, soft_penalties
    
    def calculate_constraint_penalty(self,
                                   hard_violations: Dict[str, int],
                                   soft_penalties: Dict[str, float]) -> float:
        """
        Calculate total constraint penalty score.
        
        Args:
            hard_violations: Dictionary of hard constraint violation counts
            soft_penalties: Dictionary of soft constraint penalty scores
        
        Returns:
            Total penalty score
        """
        total_penalty = 0.0
        
        # Calculate hard constraint penalties (heavily weighted)
        hard_weights = self.constraint_weights['hard_constraints']
        for constraint, violations in hard_violations.items():
            if constraint in hard_weights:
                total_penalty += violations * hard_weights[constraint]
            else:
                total_penalty += violations * 1000  # Default heavy penalty
        
        # Calculate soft constraint penalties
        soft_weights = self.constraint_weights['soft_constraints']
        for constraint, penalty in soft_penalties.items():
            if constraint in soft_weights:
                total_penalty += penalty * soft_weights[constraint]
            else:
                total_penalty += penalty  # Default weight of 1
        
        return total_penalty
    
    def is_feasible(self,
                   chromosome: Chromosome,
                   courses: Dict[str, Course],
                   instructors: Dict[str, Instructor],
                   rooms: Dict[str, Room],
                   groups: Dict[str, Group]) -> bool:
        """
        Check if a chromosome represents a feasible solution.
        
        Args:
            chromosome: Chromosome to check
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            True if feasible (no hard constraint violations), False otherwise
        """
        return self.hard_checker.is_feasible(chromosome, courses, instructors, rooms, groups)
    
    def evaluate_solution_quality(self,
                                 chromosome: Chromosome,
                                 courses: Dict[str, Course],
                                 instructors: Dict[str, Instructor],
                                 rooms: Dict[str, Room],
                                 groups: Dict[str, Group]) -> Dict[str, Any]:
        """
        Evaluate overall solution quality with detailed metrics.
        
        Args:
            chromosome: Chromosome to evaluate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Dictionary with detailed quality metrics
        """
        hard_violations, soft_penalties = self.check_all_constraints(
            chromosome, courses, instructors, rooms, groups
        )
        
        total_hard_violations = sum(hard_violations.values())
        total_soft_penalty = sum(soft_penalties.values())
        total_penalty = self.calculate_constraint_penalty(hard_violations, soft_penalties)
        
        # Calculate quality metrics
        feasible = total_hard_violations == 0
        completeness = chromosome.is_complete(courses)
        
        # Calculate efficiency metrics
        room_utilization = self._calculate_room_utilization_efficiency(
            chromosome, courses, rooms, groups
        )
        instructor_workload_balance = self._calculate_workload_balance(
            chromosome, instructors, courses
        )
        
        return {
            'feasible': feasible,
            'complete': completeness,
            'total_hard_violations': total_hard_violations,
            'total_soft_penalty': total_soft_penalty,
            'total_penalty': total_penalty,
            'room_utilization_efficiency': room_utilization,
            'workload_balance': instructor_workload_balance,
            'hard_violations_detail': hard_violations,
            'soft_penalties_detail': soft_penalties,
            'quality_score': self._calculate_quality_score(
                feasible, total_hard_violations, total_soft_penalty
            )
        }
    
    def _calculate_room_utilization_efficiency(self,
                                             chromosome: Chromosome,
                                             courses: Dict[str, Course],
                                             rooms: Dict[str, Room],
                                             groups: Dict[str, Group]) -> float:
        """Calculate overall room utilization efficiency."""
        if not chromosome.genes:
            return 0.0
        
        total_efficiency = 0.0
        session_count = 0
        
        for gene in chromosome.genes:
            if (gene.course_id in courses and 
                gene.room_id in rooms):
                
                course = courses[gene.course_id]
                room = rooms[gene.room_id]
                
                # Calculate students for this course
                total_students = sum(
                    groups[group_id].student_count
                    for group_id in course.group_ids
                    if group_id in groups
                )
                
                # Get utilization score
                utilization = room.calculate_utilization_score(total_students)
                total_efficiency += utilization
                session_count += 1
        
        return total_efficiency / session_count if session_count > 0 else 0.0
    
    def _calculate_workload_balance(self,
                                  chromosome: Chromosome,
                                  instructors: Dict[str, Instructor],
                                  courses: Dict[str, Course]) -> float:
        """Calculate instructor workload balance."""
        if not instructors:
            return 1.0
        
        # Calculate workload for each instructor
        workloads = []
        for instructor_id in instructors.keys():
            instructor_genes = chromosome.get_genes_by_instructor(instructor_id)
            
            total_hours = sum(
                courses[gene.course_id].duration / 60.0
                for gene in instructor_genes
                if gene.course_id in courses
            )
            
            workloads.append(total_hours)
        
        if not workloads or max(workloads) == 0:
            return 1.0
        
        # Calculate coefficient of variation (lower is better balance)
        mean_workload = sum(workloads) / len(workloads)
        if mean_workload == 0:
            return 1.0
        
        variance = sum((w - mean_workload) ** 2 for w in workloads) / len(workloads)
        std_dev = variance ** 0.5
        cv = std_dev / mean_workload
        
        # Convert to balance score (1 = perfect balance, 0 = poor balance)
        return max(0.0, 1.0 - cv)
    
    def _calculate_quality_score(self,
                               feasible: bool,
                               hard_violations: int,
                               soft_penalty: float) -> float:
        """
        Calculate an overall quality score for the solution.
        
        Args:
            feasible: Whether solution is feasible
            hard_violations: Number of hard constraint violations
            soft_penalty: Total soft constraint penalty
        
        Returns:
            Quality score between 0 and 100
        """
        if not feasible:
            # Heavily penalize infeasible solutions
            return max(0.0, 50.0 - hard_violations * 5)
        
        # For feasible solutions, base score on soft constraint performance
        base_score = 100.0
        
        # Deduct points for soft constraint violations
        # Normalize soft penalty (this might need tuning based on typical values)
        normalized_penalty = min(soft_penalty / 10.0, 50.0)  # Cap at 50 points deduction
        
        quality_score = base_score - normalized_penalty
        
        return max(0.0, quality_score)
    
    def get_violation_summary(self,
                            hard_violations: Dict[str, int],
                            soft_penalties: Dict[str, float]) -> str:
        """
        Get a human-readable summary of all constraint violations.
        
        Args:
            hard_violations: Dictionary of hard constraint violation counts
            soft_penalties: Dictionary of soft constraint penalty scores
        
        Returns:
            Summary string
        """
        summary_parts = []
        
        # Hard constraints summary
        hard_summary = self.hard_checker.get_violation_summary(hard_violations)
        if "No hard constraint violations" not in hard_summary:
            summary_parts.append(hard_summary)
        
        # Soft constraints summary
        soft_summary = self.soft_checker.get_penalty_summary(soft_penalties)
        if "No soft constraint penalties" not in soft_summary:
            summary_parts.append(soft_summary)
        
        if not summary_parts:
            return "No constraint violations detected - optimal solution"
        
        return " | ".join(summary_parts)
    
    def get_detailed_report(self,
                          chromosome: Chromosome,
                          courses: Dict[str, Course],
                          instructors: Dict[str, Instructor],
                          rooms: Dict[str, Room],
                          groups: Dict[str, Group]) -> Dict[str, Any]:
        """
        Generate a detailed constraint evaluation report.
        
        Args:
            chromosome: Chromosome to evaluate
            courses: Dictionary of course entities
            instructors: Dictionary of instructor entities
            rooms: Dictionary of room entities
            groups: Dictionary of group entities
        
        Returns:
            Detailed report dictionary
        """
        quality_metrics = self.evaluate_solution_quality(
            chromosome, courses, instructors, rooms, groups
        )
        
        # Get detailed violation information
        violation_details = self.hard_checker.get_constraint_details(
            chromosome, courses, instructors, rooms, groups
        )
        
        return {
            'quality_metrics': quality_metrics,
            'violation_details': violation_details,
            'summary': self.get_violation_summary(
                quality_metrics['hard_violations_detail'],
                quality_metrics['soft_penalties_detail']
            ),
            'recommendations': self._generate_recommendations(quality_metrics)
        }
    
    def _generate_recommendations(self, quality_metrics: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations based on quality metrics."""
        recommendations = []
        
        if not quality_metrics['feasible']:
            recommendations.append("Focus on eliminating hard constraint violations first")
        
        if quality_metrics['room_utilization_efficiency'] < 0.7:
            recommendations.append("Improve room utilization by better matching room sizes to class sizes")
        
        if quality_metrics['workload_balance'] < 0.7:
            recommendations.append("Balance instructor workloads more evenly")
        
        # Add specific recommendations based on violation types
        hard_violations = quality_metrics['hard_violations_detail']
        
        if hard_violations.get('instructor_conflict', 0) > 0:
            recommendations.append("Resolve instructor scheduling conflicts")
        
        if hard_violations.get('room_conflict', 0) > 0:
            recommendations.append("Resolve room double-booking issues")
        
        if hard_violations.get('room_capacity', 0) > 0:
            recommendations.append("Ensure rooms can accommodate enrolled students")
        
        return recommendations
    
    def update_weights(self, new_weights: Dict[str, Any]) -> None:
        """
        Update constraint weights for penalty calculation.
        
        Args:
            new_weights: New weight configuration
        """
        if 'hard_constraints' in new_weights:
            self.constraint_weights['hard_constraints'].update(new_weights['hard_constraints'])
        
        if 'soft_constraints' in new_weights:
            self.constraint_weights['soft_constraints'].update(new_weights['soft_constraints'])
        
        if 'fitness_weights' in new_weights:
            self.constraint_weights['fitness_weights'].update(new_weights['fitness_weights'])
        
        self.logger.info("Constraint weights updated")
    
    def reset_weights(self) -> None:
        """Reset constraint weights to default values."""
        self.constraint_weights = CONSTRAINT_WEIGHTS.copy()
        self.logger.info("Constraint weights reset to defaults")
