"""
Enhanced Multi-Objective Fitness Function for UCTP

This module provides an improved fitness evaluation system that considers
multiple objectives and includes repair mechanisms.
"""

from typing import Dict, List, Tuple, Any
import numpy as np
from dataclasses import dataclass

from src.entities import Course, Instructor, Group, Room
from src.ga_deap.sessiongene import SessionGene
from src.constraints.adaptive_checker import AdaptiveConstraintChecker


@dataclass
class FitnessComponents:
    """Components of multi-objective fitness"""

    constraint_satisfaction: float  # Primary objective
    resource_utilization: float  # Secondary objective
    preference_satisfaction: float  # Tertiary objective
    schedule_quality: float  # Overall quality measure

    def weighted_sum(self, weights: List[float] = None) -> float:
        """Calculate weighted sum of fitness components"""
        if weights is None:
            weights = [0.6, 0.2, 0.1, 0.1]  # Default weights

        components = [
            self.constraint_satisfaction,
            self.resource_utilization,
            self.preference_satisfaction,
            self.schedule_quality,
        ]

        return sum(w * c for w, c in zip(weights, components))


class EnhancedFitnessEvaluator:
    """
    Multi-objective fitness evaluator with repair mechanisms
    """

    def __init__(self):
        self.constraint_checker = AdaptiveConstraintChecker()
        self.evaluation_cache = {}
        self.generation = 0

        # Fitness weights that adapt over time
        self.adaptive_weights = {
            "constraint_satisfaction": 0.7,
            "resource_utilization": 0.15,
            "preference_satisfaction": 0.1,
            "schedule_quality": 0.05,
        }

    def update_generation(self, generation: int):
        """Update generation for adaptive evaluation"""
        self.generation = generation
        self.constraint_checker.update_generation(generation)
        self._adapt_fitness_weights()

    def _adapt_fitness_weights(self):
        """Adapt fitness weights based on generation"""
        # Early generations: focus on constraint satisfaction
        # Later generations: balance multiple objectives

        progress = min(self.generation / 100.0, 1.0)  # Normalize to [0,1]

        # Start with high constraint focus, gradually balance
        self.adaptive_weights["constraint_satisfaction"] = 0.9 - 0.2 * progress
        self.adaptive_weights["resource_utilization"] = 0.05 + 0.1 * progress
        self.adaptive_weights["preference_satisfaction"] = 0.03 + 0.07 * progress
        self.adaptive_weights["schedule_quality"] = 0.02 + 0.05 * progress

    def evaluate_individual(
        self,
        individual: List[SessionGene],
        qts,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
        use_cache: bool = True,
    ) -> Tuple[float, FitnessComponents]:
        """
        Comprehensive fitness evaluation with multiple objectives
        """
        # Create cache key
        cache_key = self._create_cache_key(individual) if use_cache else None

        if cache_key and cache_key in self.evaluation_cache:
            return self.evaluation_cache[cache_key]

        # 1. Constraint satisfaction evaluation
        constraint_analysis = self.constraint_checker.check_comprehensive_constraints(
            individual, qts, courses, instructors, groups, rooms
        )

        constraint_fitness = self._evaluate_constraint_satisfaction(constraint_analysis)

        # 2. Resource utilization evaluation
        utilization_fitness = self._evaluate_resource_utilization(
            individual, qts, courses, instructors, groups, rooms
        )

        # 3. Preference satisfaction evaluation
        preference_fitness = self._evaluate_preference_satisfaction(
            individual, qts, courses, instructors, groups, rooms
        )

        # 4. Overall schedule quality evaluation
        quality_fitness = self._evaluate_schedule_quality(
            individual, constraint_analysis, qts, courses, instructors, groups, rooms
        )

        # Create fitness components
        components = FitnessComponents(
            constraint_satisfaction=constraint_fitness,
            resource_utilization=utilization_fitness,
            preference_satisfaction=preference_fitness,
            schedule_quality=quality_fitness,
        )

        # Calculate weighted fitness
        weights = list(self.adaptive_weights.values())
        total_fitness = components.weighted_sum(weights)

        # Cache result
        if cache_key:
            self.evaluation_cache[cache_key] = (total_fitness, components)

        return total_fitness, components

    def _evaluate_constraint_satisfaction(
        self, constraint_analysis: Dict[str, Any]
    ) -> float:
        """Evaluate constraint satisfaction (primary objective)"""
        hard_violations = constraint_analysis["hard_violations"]
        soft_violations = constraint_analysis["soft_violations"]

        # Perfect score for no hard violations
        if hard_violations == 0:
            base_score = 100
            # Reduce score based on soft violations
            soft_penalty = min(soft_violations * 2, 30)  # Cap at 30 points
            return max(0, base_score - soft_penalty)
        else:
            # Heavy penalty for hard violations
            hard_penalty = hard_violations * 25
            soft_penalty = soft_violations * 1
            return max(0, 100 - hard_penalty - soft_penalty)

    def _evaluate_resource_utilization(
        self, individual: List[SessionGene], qts, courses, instructors, groups, rooms
    ) -> float:
        """Evaluate how efficiently resources are used"""

        # Room utilization
        room_usage = {}
        instructor_usage = {}
        time_slot_usage = set()

        for session in individual:
            # Track room usage
            room_usage[session.room_id] = room_usage.get(session.room_id, 0) + len(
                session.quanta
            )

            # Track instructor usage
            instructor_usage[session.instructor_id] = instructor_usage.get(
                session.instructor_id, 0
            ) + len(session.quanta)

            # Track time slot usage
            for quantum in session.quanta:
                time_slot_usage.add(quantum)

        # Calculate utilization metrics
        room_utilization = len(room_usage) / len(rooms) if rooms else 0
        instructor_utilization = (
            len(instructor_usage) / len(instructors) if instructors else 0
        )
        time_efficiency = (
            len(time_slot_usage) / (len(individual) * 2) if individual else 0
        )  # Assume avg 2 quanta per session

        # Balanced utilization is better
        utilization_score = (
            (room_utilization + instructor_utilization + time_efficiency) / 3 * 100
        )

        return min(utilization_score, 100)

    def _evaluate_preference_satisfaction(
        self, individual: List[SessionGene], qts, courses, instructors, groups, rooms
    ) -> float:
        """Evaluate satisfaction of preferences and soft requirements"""

        preference_score = 100
        total_sessions = len(individual)

        if total_sessions == 0:
            return 0

        preference_violations = 0

        for session in individual:
            # Check instructor preferences (if available)
            if session.instructor_id in instructors:
                instructor = instructors[session.instructor_id]

                # Example: Check if instructor prefers certain time slots
                # This would need to be implemented based on your data model
                if hasattr(instructor, "preferred_quanta"):
                    session_quanta = set(session.quanta)
                    preferred_quanta = set(instructor.preferred_quanta)

                    if not session_quanta.intersection(preferred_quanta):
                        preference_violations += 1

            # Check room type preferences
            if session.room_id in rooms and session.course_id in courses:
                room = rooms[session.room_id]
                course = courses[session.course_id]

                # Example: Check if room type matches course requirements
                if hasattr(course, "preferred_room_type") and hasattr(
                    room, "room_type"
                ):
                    if course.preferred_room_type != room.room_type:
                        preference_violations += (
                            0.5  # Half penalty for room type mismatch
                        )

        # Calculate preference satisfaction
        violation_ratio = preference_violations / total_sessions
        preference_score = max(0, 100 - violation_ratio * 100)

        return preference_score

    def _evaluate_schedule_quality(
        self,
        individual: List[SessionGene],
        constraint_analysis: Dict[str, Any],
        qts,
        courses,
        instructors,
        groups,
        rooms,
    ) -> float:
        """Evaluate overall schedule quality metrics"""

        quality_metrics = []

        # 1. Schedule compactness (fewer gaps)
        compactness_score = self._calculate_compactness(individual, qts, groups)
        quality_metrics.append(compactness_score)

        # 2. Balanced daily distribution
        distribution_score = self._calculate_daily_distribution(individual, qts)
        quality_metrics.append(distribution_score)

        # 3. Lunch break preservation
        lunch_score = self._calculate_lunch_preservation(individual, qts, groups)
        quality_metrics.append(lunch_score)

        # 4. Consecutive class optimization
        consecutive_score = self._calculate_consecutive_optimization(
            individual, qts, groups
        )
        quality_metrics.append(consecutive_score)

        # Average quality metrics
        return np.mean(quality_metrics) if quality_metrics else 0

    def _calculate_compactness(
        self, individual: List[SessionGene], qts, groups: Dict[str, Group]
    ) -> float:
        """Calculate schedule compactness for groups"""
        group_schedules = {}

        # Build group schedules
        for session in individual:
            if session.group_id not in group_schedules:
                group_schedules[session.group_id] = []
            group_schedules[session.group_id].extend(session.quanta)

        compactness_scores = []

        for group_id, quanta in group_schedules.items():
            if len(quanta) <= 1:
                compactness_scores.append(100)
                continue

            sorted_quanta = sorted(quanta)
            gaps = 0

            for i in range(1, len(sorted_quanta)):
                gap = sorted_quanta[i] - sorted_quanta[i - 1] - 1
                if gap > 0:
                    gaps += gap

            # Better compactness = fewer gaps
            max_possible_gaps = max(1, len(sorted_quanta) - 1)
            compactness = max(0, 100 - (gaps / max_possible_gaps) * 100)
            compactness_scores.append(compactness)

        return np.mean(compactness_scores) if compactness_scores else 100

    def _calculate_daily_distribution(
        self, individual: List[SessionGene], qts
    ) -> float:
        """Calculate how evenly sessions are distributed across days"""
        daily_counts = {}

        for session in individual:
            for quantum in session.quanta:
                try:
                    day, _ = qts.quanta_to_time(quantum)
                    daily_counts[day] = daily_counts.get(day, 0) + 1
                except:
                    continue

        if not daily_counts:
            return 100

        # Calculate coefficient of variation (lower is better)
        counts = list(daily_counts.values())
        if len(counts) <= 1:
            return 100

        mean_count = np.mean(counts)
        std_count = np.std(counts)

        if mean_count == 0:
            return 100

        cv = std_count / mean_count
        distribution_score = max(0, 100 - cv * 100)

        return distribution_score

    def _calculate_lunch_preservation(
        self, individual: List[SessionGene], qts, groups: Dict[str, Group]
    ) -> float:
        """Calculate lunch break preservation"""
        lunch_violations = 0
        total_group_days = 0

        # Define lunch time quanta (this would need to be configured)
        try:
            lunch_start = qts.time_to_quanta("Monday", "12:00")
            lunch_end = qts.time_to_quanta("Monday", "13:00")
        except:
            # If quantum system doesn't support this, return neutral score
            return 100

        group_daily_schedules = {}

        for session in individual:
            for quantum in session.quanta:
                try:
                    day, _ = qts.quanta_to_time(quantum)
                    key = (session.group_id, day)

                    if key not in group_daily_schedules:
                        group_daily_schedules[key] = []
                    group_daily_schedules[key].append(quantum)

                except:
                    continue

        for (group_id, day), quanta in group_daily_schedules.items():
            total_group_days += 1

            # Check if any session conflicts with lunch time
            lunch_conflict = any(lunch_start <= q <= lunch_end for q in quanta)
            if lunch_conflict:
                lunch_violations += 1

        if total_group_days == 0:
            return 100

        preservation_rate = 1 - (lunch_violations / total_group_days)
        return preservation_rate * 100

    def _calculate_consecutive_optimization(
        self, individual: List[SessionGene], qts, groups: Dict[str, Group]
    ) -> float:
        """Calculate optimization of consecutive classes"""
        # This is a placeholder - implement based on your specific requirements
        # Could check for optimal spacing between related courses, etc.
        return 100  # Neutral score for now

    def _create_cache_key(self, individual: List[SessionGene]) -> str:
        """Create a cache key for the individual"""
        # Simple hash based on session structure
        key_parts = []
        for session in individual:
            key_parts.append(
                f"{session.course_id}-{session.instructor_id}-{session.room_id}-{session.group_id}-{tuple(session.quanta)}"
            )

        return hash(tuple(sorted(key_parts)))

    def get_fitness_statistics(self) -> Dict[str, Any]:
        """Get statistics about fitness evaluations"""
        return {
            "cache_size": len(self.evaluation_cache),
            "current_generation": self.generation,
            "adaptive_weights": self.adaptive_weights.copy(),
        }


# Integration example
def integrate_enhanced_fitness():
    """
    Example of how to integrate the enhanced fitness function
    """
    # In your GA runner:
    # 1. Replace simple fitness evaluation with EnhancedFitnessEvaluator
    # 2. Update generation counter during evolution
    # 3. Use FitnessComponents for detailed analysis
    # 4. Implement repair operators based on fitness components

    pass
