"""
Hard constraint checker module
"""

from typing import Dict, List, Any
from src.ga_deap.sessiongene import SessionGene
from src.entities import Course, Instructor, Group, Room


class HardConstraintChecker:
    """Checks hard constraints that must not be violated"""

    def __init__(self):
        self.violations = []

    def check_constraints(
        self,
        individual: List[SessionGene],
        qts,
        courses: Dict[str, Course],
        instructors: Dict[str, Instructor],
        groups: Dict[str, Group],
        rooms: Dict[str, Room],
    ) -> Dict[str, int]:
        """Check all hard constraints"""
        violations = {
            "total": 0,
            "instructor_conflicts": 0,
            "room_conflicts": 0,
            "group_conflicts": 0,
            "capacity_violations": 0,
        }

        # Implementation would go here
        return violations
