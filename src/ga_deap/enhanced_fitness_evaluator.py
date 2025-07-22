"""
Enhanced Fitness Evaluator with Multi-Criteria Assessment
Provides comprehensive fitness evaluation with constraint analysis and performance optimization.
"""

import time
import hashlib
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np

from .sessiongene import SessionGene
from src.encoders import QuantumTimeSystem
from src.entities import Course, Instructor, Group, Room


@dataclass
class FitnessBreakdown:
    """Detailed fitness breakdown for analysis"""

    total_fitness: float
    hard_constraint_violations: int
    soft_constraint_violations: int
    resource_utilization_score: float
    schedule_quality_score: float
    constraint_details: Dict[str, int]


class EnhancedFitnessEvaluator:
    """
    Advanced fitness evaluator with multi-criteria assessment and caching.
    """

    def __init__(self, enable_caching: bool = True, cache_size: int = 1000):
        self.enable_caching = enable_caching
        self.cache_size = cache_size
        self.fitness_cache = {}
        self.evaluation_count = 0
        self.cache_hits = 0

        # Fitness weights (can be adjusted based on problem requirements)
        self.weights = {
            "hard_violations": 1000,  # Heavy penalty for hard constraints
            "soft_violations": 10,  # Lighter penalty for soft constraints
            "resource_utilization": 50,  # Bonus for efficient resource use
            "schedule_quality": 30,  # Bonus for high-quality schedules
        }

    def evaluate_individual(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> Tuple[float, FitnessBreakdown]:
        """
        Comprehensive fitness evaluation with detailed breakdown.
        """
        # Check cache first
        if self.enable_caching:
            cache_key = self._generate_cache_key(individual)
            if cache_key in self.fitness_cache:
                self.cache_hits += 1
                return self.fitness_cache[cache_key]

        self.evaluation_count += 1
        start_time = time.time()

        # Initialize fitness components
        hard_violations = 0
        soft_violations = 0
        constraint_details = defaultdict(int)

        # Track resource usage
        resource_usage = self._analyze_resource_usage(
            individual, qts, courses, instructors, groups, rooms
        )

        # Evaluate hard constraints
        hard_violations, hard_details = self._evaluate_hard_constraints(
            individual, qts, courses, instructors, groups, rooms, resource_usage
        )
        constraint_details.update(hard_details)

        # Evaluate soft constraints
        soft_violations, soft_details = self._evaluate_soft_constraints(
            individual, qts, courses, instructors, groups, rooms, resource_usage
        )
        constraint_details.update(soft_details)

        # Calculate resource utilization score
        resource_score = self._calculate_resource_utilization_score(
            resource_usage, instructors, rooms
        )

        # Calculate schedule quality score
        quality_score = self._calculate_schedule_quality_score(individual, qts, groups)

        # Calculate total fitness
        total_fitness = (
            -self.weights["hard_violations"] * hard_violations
            - self.weights["soft_violations"] * soft_violations
            + self.weights["resource_utilization"] * resource_score
            + self.weights["schedule_quality"] * quality_score
        )

        # Create detailed breakdown
        breakdown = FitnessBreakdown(
            total_fitness=total_fitness,
            hard_constraint_violations=hard_violations,
            soft_constraint_violations=soft_violations,
            resource_utilization_score=resource_score,
            schedule_quality_score=quality_score,
            constraint_details=dict(constraint_details),
        )

        # Cache result
        if self.enable_caching and len(self.fitness_cache) < self.cache_size:
            self.fitness_cache[cache_key] = (total_fitness, breakdown)

        return total_fitness, breakdown

    def _generate_cache_key(self, individual: List[SessionGene]) -> str:
        """Generate unique cache key for individual"""
        # Create a string representation of the individual
        individual_str = ""
        for session in individual:
            individual_str += f"{session.course_id}:{session.instructor_id}:{session.room_id}:{session.group_id}:{','.join(map(str, session.quanta))};"

        # Return hash of the string
        return hashlib.md5(individual_str.encode()).hexdigest()

    def _analyze_resource_usage(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> Dict[str, Any]:
        """Analyze resource usage patterns"""
        usage = {
            "quantum_instructor": set(),
            "quantum_room": set(),
            "quantum_group": set(),
            "instructor_load": defaultdict(int),
            "room_utilization": defaultdict(int),
            "group_schedule": defaultdict(list),
            "time_slot_usage": defaultdict(int),
        }

        for session in individual:
            for quantum in session.quanta:
                # Track conflicts
                usage["quantum_instructor"].add((quantum, session.instructor_id))
                usage["quantum_room"].add((quantum, session.room_id))
                usage["quantum_group"].add((quantum, session.group_id))

                # Track loads
                usage["instructor_load"][session.instructor_id] += 1
                usage["room_utilization"][session.room_id] += 1
                usage["group_schedule"][session.group_id].append(quantum)
                usage["time_slot_usage"][quantum] += 1

        return usage

    def _evaluate_hard_constraints(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
        resource_usage: Dict[str, Any],
    ) -> Tuple[int, Dict[str, int]]:
        """Evaluate hard constraints (must be satisfied)"""
        violations = 0
        details = defaultdict(int)

        # Track used slots for conflict detection
        used_slots = {"instructor": set(), "room": set(), "group": set()}

        for session in individual:
            course = courses.get(session.course_id)
            instructor = instructors.get(session.instructor_id)
            group = groups.get(session.group_id)
            room = rooms.get(session.room_id)

            if not all([course, instructor, group, room]):
                violations += 1
                details["missing_entities"] += 1
                continue

            for quantum in session.quanta:
                # Check conflicts
                if (quantum, session.instructor_id) in used_slots["instructor"]:
                    violations += 1
                    details["instructor_conflict"] += 1
                else:
                    used_slots["instructor"].add((quantum, session.instructor_id))

                if (quantum, session.room_id) in used_slots["room"]:
                    violations += 1
                    details["room_conflict"] += 1
                else:
                    used_slots["room"].add((quantum, session.room_id))

                if (quantum, session.group_id) in used_slots["group"]:
                    violations += 1
                    details["group_conflict"] += 1
                else:
                    used_slots["group"].add((quantum, session.group_id))

                # Check availability constraints
                if (
                    not instructor.is_full_time
                    and quantum not in instructor.available_quanta
                ):
                    violations += 1
                    details["instructor_unavailable"] += 1

                if quantum not in group.available_quanta:
                    violations += 1
                    details["group_unavailable"] += 1

                if quantum not in room.available_quanta:
                    violations += 1
                    details["room_unavailable"] += 1

            # Check instructor qualification
            if session.course_id not in instructor.qualified_courses:
                violations += 1
                details["instructor_unqualified"] += 1

            # Check room suitability
            if not room.is_suitable_for_course_type(course.required_room_features):
                violations += 1
                details["room_unsuitable"] += 1

        return violations, dict(details)

    def _evaluate_soft_constraints(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
        resource_usage: Dict[str, Any],
    ) -> Tuple[int, Dict[str, int]]:
        """Evaluate soft constraints (preferences)"""
        violations = 0
        details = defaultdict(int)

        # Instructor workload balance
        instructor_loads = list(resource_usage["instructor_load"].values())
        if instructor_loads:
            load_std = np.std(instructor_loads)
            if load_std > 2:  # High variance in workload
                violations += int(load_std)
                details["workload_imbalance"] += int(load_std)

        # Room utilization balance
        room_utilizations = list(resource_usage["room_utilization"].values())
        if room_utilizations:
            util_std = np.std(room_utilizations)
            if util_std > 2:  # High variance in utilization
                violations += int(util_std)
                details["room_utilization_imbalance"] += int(util_std)

        # Schedule gaps for groups
        for group_id, schedule in resource_usage["group_schedule"].items():
            if len(schedule) > 1:
                sorted_schedule = sorted(schedule)
                gaps = 0
                for i in range(1, len(sorted_schedule)):
                    gap = sorted_schedule[i] - sorted_schedule[i - 1] - 1
                    if gap > 0:
                        gaps += gap

                if gaps > 3:  # Too many gaps
                    violations += gaps
                    details["schedule_gaps"] += gaps

        # Consecutive sessions check (prefer 2-hour blocks)
        time_slot_usage = resource_usage["time_slot_usage"]
        for quantum, usage_count in time_slot_usage.items():
            if usage_count == 1:  # Single session in this slot
                # Check if it can be paired with adjacent slots
                adjacent_used = time_slot_usage.get(
                    quantum + 1, 0
                ) + time_slot_usage.get(quantum - 1, 0)
                if adjacent_used == 0:
                    violations += 1
                    details["isolated_sessions"] += 1

        return violations, dict(details)

    def _calculate_resource_utilization_score(
        self,
        resource_usage: Dict[str, Any],
        instructors: Dict[str, Instructor],
        rooms: Dict[str, Room],
    ) -> float:
        """Calculate resource utilization efficiency score"""
        score = 0

        # Instructor utilization
        used_instructors = len(resource_usage["instructor_load"])
        total_instructors = len(instructors)
        if total_instructors > 0:
            instructor_utilization = used_instructors / total_instructors
            score += instructor_utilization * 25

        # Room utilization
        used_rooms = len(resource_usage["room_utilization"])
        total_rooms = len(rooms)
        if total_rooms > 0:
            room_utilization = used_rooms / total_rooms
            score += room_utilization * 25

        # Time slot efficiency
        total_sessions = sum(resource_usage["instructor_load"].values())
        unique_time_slots = len(resource_usage["time_slot_usage"])
        if unique_time_slots > 0:
            time_efficiency = min(
                1.0, total_sessions / (unique_time_slots * 2)
            )  # Ideal: 2 sessions per slot
            score += time_efficiency * 50

        return min(score, 100)

    def _calculate_schedule_quality_score(
        self,
        individual: List[SessionGene],
        qts: QuantumTimeSystem,
        groups: Dict[str, Group],
    ) -> float:
        """Calculate overall schedule quality score"""
        score = 0

        # Compactness score - prefer fewer gaps in schedules
        group_schedules = defaultdict(list)
        for session in individual:
            group_schedules[session.group_id].extend(session.quanta)

        compactness_scores = []
        for group_id, quanta in group_schedules.items():
            if len(quanta) > 1:
                sorted_quanta = sorted(quanta)
                span = sorted_quanta[-1] - sorted_quanta[0] + 1
                efficiency = len(quanta) / span
                compactness_scores.append(efficiency)

        if compactness_scores:
            score += np.mean(compactness_scores) * 50

        # Distribution score - prefer even distribution across days
        daily_distribution = defaultdict(int)
        for session in individual:
            for quantum in session.quanta:
                try:
                    day_info = qts.quanta_to_day_info(quantum)
                    daily_distribution[day_info["day"]] += 1
                except:
                    pass

        if daily_distribution:
            distribution_values = list(daily_distribution.values())
            distribution_std = np.std(distribution_values)
            max_distribution = max(distribution_values)
            if max_distribution > 0:
                distribution_score = max(0, 50 - distribution_std * 10)
                score += distribution_score

        return min(score, 100)

    def clear_cache(self):
        """Clear fitness cache"""
        self.fitness_cache.clear()
        self.cache_hits = 0

    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        hit_rate = (
            self.cache_hits / self.evaluation_count if self.evaluation_count > 0 else 0
        )
        return {
            "evaluations": self.evaluation_count,
            "cache_hits": self.cache_hits,
            "hit_rate": hit_rate,
            "cache_size": len(self.fitness_cache),
        }

    def update_weights(self, **kwargs):
        """Update fitness weights"""
        for key, value in kwargs.items():
            if key in self.weights:
                self.weights[key] = value
