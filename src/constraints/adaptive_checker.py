"""
Enhanced Constraint System with Adaptive Penalties and Repair Mechanisms

This module demonstrates how to implement a more sophisticated constraint
handling system for the UCTP solver.
"""

from typing import Dict, List, Any, Tuple, Optional
from collections import defaultdict
import numpy as np
from dataclasses import dataclass
from enum import Enum

from src.entities import Course, Instructor, Group, Room
from src.ga_deap.sessiongene import SessionGene


class ConstraintType(Enum):
    """Constraint classification"""

    HARD = "hard"
    SOFT = "soft"
    PREFERENCE = "preference"


class ViolationSeverity(Enum):
    """Violation severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ConstraintViolation:
    """Enhanced constraint violation with repair suggestions"""

    constraint_id: str
    violation_type: ConstraintType
    severity: ViolationSeverity
    description: str
    affected_entities: List[str]
    penalty_score: float
    repair_suggestions: List[str]
    quantum: Optional[int] = None
    confidence: float = 1.0


class AdaptiveConstraintChecker:
    """
    Enhanced constraint checker with adaptive penalties and repair mechanisms
    """

    def __init__(self):
        self.violation_history = []
        self.adaptive_weights = {
            # Start with base weights
            "instructor_conflict": 1000,
            "room_conflict": 1000,
            "group_conflict": 1000,
            "room_capacity": 1000,
            "instructor_qualification": 500,
            "preference_violation": 100,
            "workload_balance": 50,
            "schedule_compactness": 30,
        }

        # Adaptation parameters
        self.adaptation_rate = 0.1
        self.generation_counter = 0
        self.constraint_satisfaction_history = defaultdict(list)

    def update_generation(self, generation: int):
        """Update generation counter for adaptive penalties"""
        self.generation_counter = generation
        self._adapt_constraint_weights()

    def _adapt_constraint_weights(self):
        """Adapt constraint weights based on violation history"""
        if len(self.violation_history) < 10:
            return

        # Get recent violations
        recent_violations = self.violation_history[-10:]

        # Calculate violation frequencies
        violation_counts = defaultdict(int)
        for violations in recent_violations:
            for violation in violations:
                violation_counts[violation.constraint_id] += 1

        # Adapt weights: increase weight for frequently violated constraints
        for constraint_id, count in violation_counts.items():
            if constraint_id in self.adaptive_weights:
                if count > 5:  # Frequently violated
                    self.adaptive_weights[constraint_id] *= 1 + self.adaptation_rate
                elif count < 2:  # Rarely violated
                    self.adaptive_weights[constraint_id] *= (
                        1 - self.adaptation_rate * 0.5
                    )

    def check_comprehensive_constraints(
        self,
        chromosome: List[SessionGene],
        qts,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> Dict[str, Any]:
        """
        Comprehensive constraint checking with adaptive penalties
        """
        violations = []
        total_penalty = 0

        # Resource usage tracking
        resource_usage = self._build_resource_usage_map(chromosome)

        # Check hard constraints
        hard_violations = self._check_hard_constraints(
            chromosome, resource_usage, qts, courses, instructors, groups, rooms
        )
        violations.extend(hard_violations)

        # Check soft constraints
        soft_violations = self._check_soft_constraints(
            chromosome, resource_usage, qts, courses, instructors, groups, rooms
        )
        violations.extend(soft_violations)

        # Calculate total penalty with adaptive weights
        for violation in violations:
            weight = self.adaptive_weights.get(violation.constraint_id, 1.0)
            total_penalty += violation.penalty_score * weight

        # Store violation history for adaptation
        self.violation_history.append(violations)

        # Generate repair suggestions
        repair_plan = self._generate_repair_plan(violations, chromosome)

        return {
            "violations": violations,
            "total_penalty": total_penalty,
            "hard_violations": len(
                [v for v in violations if v.violation_type == ConstraintType.HARD]
            ),
            "soft_violations": len(
                [v for v in violations if v.violation_type == ConstraintType.SOFT]
            ),
            "is_feasible": len(
                [v for v in violations if v.violation_type == ConstraintType.HARD]
            )
            == 0,
            "quality_score": self._calculate_quality_score(violations, total_penalty),
            "repair_plan": repair_plan,
            "adaptive_weights": self.adaptive_weights.copy(),
        }

    def _build_resource_usage_map(self, chromosome: List[SessionGene]) -> Dict:
        """Build comprehensive resource usage map"""
        usage = {
            "time_slots": defaultdict(lambda: defaultdict(list)),
            "instructor_schedule": defaultdict(list),
            "room_schedule": defaultdict(list),
            "group_schedule": defaultdict(list),
        }

        for session in chromosome:
            for quantum in session.quanta:
                # Time slot usage
                usage["time_slots"][quantum]["instructor"].append(session.instructor_id)
                usage["time_slots"][quantum]["room"].append(session.room_id)
                usage["time_slots"][quantum]["group"].append(session.group_id)

                # Individual schedules
                usage["instructor_schedule"][session.instructor_id].append(
                    (quantum, session)
                )
                usage["room_schedule"][session.room_id].append((quantum, session))
                usage["group_schedule"][session.group_id].append((quantum, session))

        return usage

    def _check_hard_constraints(
        self,
        chromosome: List[SessionGene],
        resource_usage: Dict,
        qts,
        courses,
        instructors,
        groups,
        rooms,
    ) -> List[ConstraintViolation]:
        """Check hard constraints with enhanced detection"""
        violations = []

        # 1. Resource conflicts
        for quantum, resources in resource_usage["time_slots"].items():
            # Instructor conflicts
            instructor_conflicts = self._find_duplicates(resources["instructor"])
            for instructor_id, count in instructor_conflicts.items():
                if count > 1:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="instructor_conflict",
                            violation_type=ConstraintType.HARD,
                            severity=ViolationSeverity.CRITICAL,
                            description=f"Instructor {instructor_id} has {count} sessions at quantum {quantum}",
                            affected_entities=[instructor_id],
                            penalty_score=1000 * count,
                            repair_suggestions=[
                                f"Reschedule one of the conflicting sessions to a different time slot",
                                f"Assign a different qualified instructor to one of the sessions",
                            ],
                            quantum=quantum,
                        )
                    )

            # Room conflicts
            room_conflicts = self._find_duplicates(resources["room"])
            for room_id, count in room_conflicts.items():
                if count > 1:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="room_conflict",
                            violation_type=ConstraintType.HARD,
                            severity=ViolationSeverity.CRITICAL,
                            description=f"Room {room_id} has {count} sessions at quantum {quantum}",
                            affected_entities=[room_id],
                            penalty_score=1000 * count,
                            repair_suggestions=[
                                f"Reassign one session to a different available room",
                                f"Reschedule one session to a different time slot",
                            ],
                            quantum=quantum,
                        )
                    )

            # Group conflicts
            group_conflicts = self._find_duplicates(resources["group"])
            for group_id, count in group_conflicts.items():
                if count > 1:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="group_conflict",
                            violation_type=ConstraintType.HARD,
                            severity=ViolationSeverity.CRITICAL,
                            description=f"Group {group_id} has {count} sessions at quantum {quantum}",
                            affected_entities=[group_id],
                            penalty_score=1000 * count,
                            repair_suggestions=[
                                f"Reschedule one session to a different time slot",
                                f"Split the group if course policies allow",
                            ],
                            quantum=quantum,
                        )
                    )

        # 2. Capacity constraints
        for session in chromosome:
            if session.group_id in groups and session.room_id in rooms:
                group = groups[session.group_id]
                room = rooms[session.room_id]

                if group.student_count > room.capacity:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="room_capacity",
                            violation_type=ConstraintType.HARD,
                            severity=ViolationSeverity.HIGH,
                            description=f"Group {group.group_id} ({group.student_count} students) exceeds room {room.room_id} capacity ({room.capacity})",
                            affected_entities=[group.group_id, room.room_id],
                            penalty_score=1000,
                            repair_suggestions=[
                                f"Assign group to a larger room with capacity >= {group.student_count}",
                                f"Split the group into smaller sections",
                                f"Use a different room type if available",
                            ],
                        )
                    )

        return violations

    def _check_soft_constraints(
        self,
        chromosome: List[SessionGene],
        resource_usage: Dict,
        qts,
        courses,
        instructors,
        groups,
        rooms,
    ) -> List[ConstraintViolation]:
        """Check soft constraints with preference scoring"""
        violations = []

        # 1. Instructor qualifications
        for session in chromosome:
            if session.instructor_id in instructors and session.course_id in courses:
                instructor = instructors[session.instructor_id]
                if session.course_id not in instructor.qualified_courses:
                    violations.append(
                        ConstraintViolation(
                            constraint_id="instructor_qualification",
                            violation_type=ConstraintType.SOFT,
                            severity=ViolationSeverity.HIGH,
                            description=f"Instructor {instructor.name} is not qualified for course {session.course_id}",
                            affected_entities=[
                                session.instructor_id,
                                session.course_id,
                            ],
                            penalty_score=500,
                            repair_suggestions=[
                                f"Assign a qualified instructor to course {session.course_id}",
                                f"Provide additional training to instructor {instructor.name}",
                            ],
                        )
                    )

        # 2. Workload balance
        instructor_workloads = self._calculate_instructor_workloads(
            resource_usage["instructor_schedule"]
        )
        avg_workload = (
            np.mean(list(instructor_workloads.values())) if instructor_workloads else 0
        )

        for instructor_id, workload in instructor_workloads.items():
            deviation = abs(workload - avg_workload)
            if deviation > avg_workload * 0.3:  # 30% deviation threshold
                violations.append(
                    ConstraintViolation(
                        constraint_id="workload_balance",
                        violation_type=ConstraintType.SOFT,
                        severity=ViolationSeverity.MEDIUM,
                        description=f"Instructor {instructor_id} workload ({workload:.1f}h) deviates significantly from average ({avg_workload:.1f}h)",
                        affected_entities=[instructor_id],
                        penalty_score=50 * deviation,
                        repair_suggestions=[
                            f"Redistribute courses to balance workload",
                            f"Assign additional sessions to underloaded instructors",
                        ],
                    )
                )

        return violations

    def _find_duplicates(self, items: List[str]) -> Dict[str, int]:
        """Find duplicate items and their counts"""
        counts = defaultdict(int)
        for item in items:
            counts[item] += 1
        return {k: v for k, v in counts.items() if v > 1}

    def _calculate_instructor_workloads(
        self, instructor_schedule: Dict
    ) -> Dict[str, float]:
        """Calculate instructor workloads in hours"""
        workloads = {}
        for instructor_id, sessions in instructor_schedule.items():
            total_hours = sum(
                len(session[1].quanta) * 0.5 for session in sessions
            )  # 0.5h per quantum
            workloads[instructor_id] = total_hours
        return workloads

    def _calculate_quality_score(
        self, violations: List[ConstraintViolation], total_penalty: float
    ) -> float:
        """Calculate overall solution quality score (0-100)"""
        # Base score
        base_score = 100

        # Penalty for hard violations
        hard_violations = [
            v for v in violations if v.violation_type == ConstraintType.HARD
        ]
        base_score -= len(hard_violations) * 20

        # Penalty for soft violations
        soft_violations = [
            v for v in violations if v.violation_type == ConstraintType.SOFT
        ]
        base_score -= len(soft_violations) * 5

        # Penalty based on total penalty score
        penalty_factor = min(total_penalty / 1000, 50)  # Cap at 50 points
        base_score -= penalty_factor

        return max(0, base_score)

    def _generate_repair_plan(
        self, violations: List[ConstraintViolation], chromosome: List[SessionGene]
    ) -> List[str]:
        """Generate a comprehensive repair plan"""
        repair_actions = []

        # Prioritize hard violations
        hard_violations = [
            v for v in violations if v.violation_type == ConstraintType.HARD
        ]

        if hard_violations:
            repair_actions.append("CRITICAL: Address hard constraint violations first")

            # Group violations by type
            violation_types = defaultdict(list)
            for v in hard_violations:
                violation_types[v.constraint_id].append(v)

            # Generate specific repair suggestions
            for violation_type, violations_list in violation_types.items():
                repair_actions.append(
                    f"- {violation_type.title()}: {len(violations_list)} violations"
                )
                for v in violations_list[:3]:  # Show first 3 suggestions
                    repair_actions.extend(
                        [f"  • {suggestion}" for suggestion in v.repair_suggestions[:2]]
                    )

        # Add soft constraint suggestions
        soft_violations = [
            v for v in violations if v.violation_type == ConstraintType.SOFT
        ]
        if soft_violations:
            repair_actions.append("IMPROVEMENTS: Address soft constraint violations")
            for v in soft_violations[:3]:  # Show first 3
                repair_actions.extend(
                    [f"  • {suggestion}" for suggestion in v.repair_suggestions[:1]]
                )

        return repair_actions


# Usage example and integration suggestions
def integrate_adaptive_constraints():
    """
    Example of how to integrate the adaptive constraint system
    """
    # In your main GA loop:
    # 1. Replace the current constraint checker with AdaptiveConstraintChecker
    # 2. Update generation counter during evolution
    # 3. Use the repair plan for guided mutation
    # 4. Track constraint satisfaction over time

    pass
