"""
Enhanced Constraint Checker Module

This module provides comprehensive constraint checking with detailed violation tracking,
constraint weighting, and repair mechanisms.
"""

from typing import Dict, List, Any, Tuple
from collections import defaultdict
import logging

from src.entities import Course, Instructor, Group, Room
from src.ga_deap.sessiongene import SessionGene


class ConstraintViolation:
    """Represents a single constraint violation."""

    def __init__(
        self,
        violation_type: str,
        severity: str,
        description: str,
        entities_involved: List[str],
        penalty_score: float,
    ):
        self.violation_type = violation_type
        self.severity = severity  # 'hard', 'soft', 'preference'
        self.description = description
        self.entities_involved = entities_involved
        self.penalty_score = penalty_score
        self.timestamp = None


class EnhancedConstraintChecker:
    """Enhanced constraint checking with detailed tracking."""

    def __init__(self):
        self.violation_history = []
        self.constraint_weights = {
            # Hard constraints
            "instructor_conflict": 1000,
            "room_conflict": 1000,
            "group_conflict": 1000,
            "room_capacity": 1000,
            "availability_violation": 1000,
            # Soft constraints
            "preference_violation": 50,
            "workload_imbalance": 30,
            "schedule_compactness": 20,
            "room_utilization": 15,
            "lunch_break": 40,
            # Quality metrics
            "consecutive_classes": 10,
            "travel_time": 25,
            "resource_optimization": 15,
        }

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
        Perform comprehensive constraint checking.

        Returns:
            Dictionary with violation details, penalties, and suggestions
        """
        violations = []
        penalty_score = 0

        # Track resource usage
        time_slot_usage = defaultdict(lambda: defaultdict(list))
        instructor_schedule = defaultdict(list)
        room_schedule = defaultdict(list)
        group_schedule = defaultdict(list)

        # Build usage maps
        for session in chromosome:
            for quantum in session.quanta:
                time_slot_usage[quantum]["instructor"].append(session.instructor_id)
                time_slot_usage[quantum]["room"].append(session.room_id)
                time_slot_usage[quantum]["group"].append(session.group_id)

                instructor_schedule[session.instructor_id].append((quantum, session))
                room_schedule[session.room_id].append((quantum, session))
                group_schedule[session.group_id].append((quantum, session))

        # Check hard constraints
        penalty_score += self._check_hard_constraints(
            violations,
            time_slot_usage,
            chromosome,
            qts,
            courses,
            instructors,
            groups,
            rooms,
        )

        # Check soft constraints
        penalty_score += self._check_soft_constraints(
            violations,
            instructor_schedule,
            room_schedule,
            group_schedule,
            chromosome,
            qts,
            courses,
            instructors,
            groups,
            rooms,
        )

        # Check quality metrics
        penalty_score += self._check_quality_metrics(
            violations,
            instructor_schedule,
            group_schedule,
            chromosome,
            qts,
            courses,
            instructors,
            groups,
            rooms,
        )

        return {
            "total_penalty": penalty_score,
            "violations": violations,
            "hard_violations": len([v for v in violations if v.severity == "hard"]),
            "soft_violations": len([v for v in violations if v.severity == "soft"]),
            "violation_summary": self._summarize_violations(violations),
            "is_feasible": penalty_score < 1000,  # No hard constraint violations
            "quality_score": max(0, 100 - (penalty_score / 10)),
        }

    def _check_hard_constraints(
        self,
        violations: List[ConstraintViolation],
        time_slot_usage: Dict,
        chromosome: List[SessionGene],
        qts,
        courses,
        instructors,
        groups,
        rooms,
    ) -> float:
        """Check hard constraints and return penalty."""
        penalty = 0

        # Resource conflicts
        for quantum, resources in time_slot_usage.items():
            # Instructor conflicts
            instructor_count = defaultdict(int)
            for instructor_id in resources["instructor"]:
                instructor_count[instructor_id] += 1
                if instructor_count[instructor_id] > 1:
                    violation = ConstraintViolation(
                        violation_type="instructor_conflict",
                        severity="hard",
                        description=f"Instructor {instructor_id} has multiple sessions at quantum {quantum}",
                        entities_involved=[instructor_id],
                        penalty_score=self.constraint_weights["instructor_conflict"],
                    )
                    violations.append(violation)
                    penalty += violation.penalty_score

            # Room conflicts
            room_count = defaultdict(int)
            for room_id in resources["room"]:
                room_count[room_id] += 1
                if room_count[room_id] > 1:
                    violation = ConstraintViolation(
                        violation_type="room_conflict",
                        severity="hard",
                        description=f"Room {room_id} has multiple sessions at quantum {quantum}",
                        entities_involved=[room_id],
                        penalty_score=self.constraint_weights["room_conflict"],
                    )
                    violations.append(violation)
                    penalty += violation.penalty_score

            # Group conflicts
            group_count = defaultdict(int)
            for group_id in resources["group"]:
                group_count[group_id] += 1
                if group_count[group_id] > 1:
                    violation = ConstraintViolation(
                        violation_type="group_conflict",
                        severity="hard",
                        description=f"Group {group_id} has multiple sessions at quantum {quantum}",
                        entities_involved=[group_id],
                        penalty_score=self.constraint_weights["group_conflict"],
                    )
                    violations.append(violation)
                    penalty += violation.penalty_score

        # Room capacity constraints
        for session in chromosome:
            room = rooms[session.room_id]
            group = groups[session.group_id]
            if group.student_count > room.capacity:
                violation = ConstraintViolation(
                    violation_type="room_capacity",
                    severity="hard",
                    description=f"Group {group.group_id} (size {group.student_count}) exceeds room {room.room_id} capacity ({room.capacity})",
                    entities_involved=[group.group_id, room.room_id],
                    penalty_score=self.constraint_weights["room_capacity"],
                )
                violations.append(violation)
                penalty += violation.penalty_score

        return penalty

    def _check_soft_constraints(
        self,
        violations: List[ConstraintViolation],
        instructor_schedule: Dict,
        room_schedule: Dict,
        group_schedule: Dict,
        chromosome: List[SessionGene],
        qts,
        courses,
        instructors,
        groups,
        rooms,
    ) -> float:
        """Check soft constraints and return penalty."""
        penalty = 0

        # Workload balance
        instructor_workloads = {}
        for instructor_id, sessions in instructor_schedule.items():
            workload = sum(len(session[1].quanta) for session in sessions)
            instructor_workloads[instructor_id] = workload

        if instructor_workloads:
            avg_workload = sum(instructor_workloads.values()) / len(
                instructor_workloads
            )
            for instructor_id, workload in instructor_workloads.items():
                if abs(workload - avg_workload) > avg_workload * 0.3:  # 30% deviation
                    violation = ConstraintViolation(
                        violation_type="workload_imbalance",
                        severity="soft",
                        description=f"Instructor {instructor_id} workload ({workload}) deviates significantly from average ({avg_workload:.1f})",
                        entities_involved=[instructor_id],
                        penalty_score=self.constraint_weights["workload_imbalance"],
                    )
                    violations.append(violation)
                    penalty += violation.penalty_score

        # Schedule compactness for students
        for group_id, sessions in group_schedule.items():
            if len(sessions) > 1:
                quanta = sorted([quantum for quantum, _ in sessions])
                gaps = []
                for i in range(1, len(quanta)):
                    gap = quanta[i] - quanta[i - 1] - 1
                    if gap > 0:
                        gaps.append(gap)

                if gaps and max(gaps) > 2:  # Gap of more than 2 time slots
                    violation = ConstraintViolation(
                        violation_type="schedule_compactness",
                        severity="soft",
                        description=f"Group {group_id} has large gaps in schedule (max gap: {max(gaps)} slots)",
                        entities_involved=[group_id],
                        penalty_score=self.constraint_weights["schedule_compactness"]
                        * max(gaps),
                    )
                    violations.append(violation)
                    penalty += violation.penalty_score

        return penalty

    def _check_quality_metrics(
        self,
        violations: List[ConstraintViolation],
        instructor_schedule: Dict,
        group_schedule: Dict,
        chromosome: List[SessionGene],
        qts,
        courses,
        instructors,
        groups,
        rooms,
    ) -> float:
        """Check quality metrics and return penalty."""
        penalty = 0

        # Lunch break preservation
        lunch_quantum_start = qts.time_to_quanta(
            "Monday", "12:00"
        )  # Assuming lunch at 12:00
        lunch_quantum_end = qts.time_to_quanta("Monday", "13:00")

        for group_id, sessions in group_schedule.items():
            lunch_violations = 0
            for quantum, session in sessions:
                if lunch_quantum_start <= quantum <= lunch_quantum_end:
                    lunch_violations += 1

            if lunch_violations > 0:
                violation = ConstraintViolation(
                    violation_type="lunch_break",
                    severity="soft",
                    description=f"Group {group_id} has {lunch_violations} sessions during lunch time",
                    entities_involved=[group_id],
                    penalty_score=self.constraint_weights["lunch_break"]
                    * lunch_violations,
                )
                violations.append(violation)
                penalty += violation.penalty_score

        return penalty

    def _summarize_violations(
        self, violations: List[ConstraintViolation]
    ) -> Dict[str, int]:
        """Summarize violations by type."""
        summary = defaultdict(int)
        for violation in violations:
            summary[violation.violation_type] += 1
        return dict(summary)

    def suggest_repairs(self, violations: List[ConstraintViolation]) -> List[str]:
        """Suggest repair actions for violations."""
        suggestions = []

        violation_types = [v.violation_type for v in violations]

        if "instructor_conflict" in violation_types:
            suggestions.append(
                "Consider reassigning sessions to different time slots to avoid instructor conflicts"
            )

        if "room_conflict" in violation_types:
            suggestions.append("Reassign sessions to different rooms or time slots")

        if "room_capacity" in violation_types:
            suggestions.append("Assign groups to larger rooms or split large groups")

        if "workload_imbalance" in violation_types:
            suggestions.append(
                "Redistribute teaching load more evenly among instructors"
            )

        if "schedule_compactness" in violation_types:
            suggestions.append(
                "Rearrange sessions to minimize gaps in student schedules"
            )

        return suggestions
