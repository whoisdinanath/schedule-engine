"""
Configuration settings for the Genetic Algorithm-based Timetabling System.
Contains default parameters and configuration options.
"""

from typing import Dict, Any
from dataclasses import dataclass
import os


# Genetic Algorithm Configuration - PURE GA (No Local Search)
GA_CONFIG = {
    # Population parameters
    "population_size": 200,
    "generations": 200,
    "elite_size": 3,
    # Genetic operators - PURE GA only
    "crossover_rate": 0.8,
    "mutation_rate": 0.2,
    "tournament_size": 20,
    # Selection methods - genetic selection only
    "selection_method": "tournament",  # 'tournament', 'roulette', 'rank'
    "crossover_method": "two_point",  # 'uniform', 'single_point', 'two_point'
    "mutation_method": "swap",  # 'random', 'swap'
    # Termination criteria
    "max_generations": 500,
    "target_fitness": 0.0,
    "stagnation_limit": 200,
    "time_limit_minutes": 10,
    # Display and logging
    "verbose": True,
    "log_frequency": 10,
    "save_best_individual": True,
    "save_population_history": False,
}

# Constraint Weights Configuration
CONSTRAINT_WEIGHTS = {
    # Hard constraints (violations should be heavily penalized)
    "hard_constraints": {
        "instructor_conflict": 100,  # Instructor teaching multiple courses at same time
        "room_conflict": 100,  # Room double-booked
        "group_conflict": 100,  # Student group in multiple classes
        "course_group_isolation": 100,  # Multiple groups from same course at same time
        "room_capacity": 100,  # Room too small for group
        "instructor_qualification": 100,  # Unqualified instructor assigned
        "room_type_mismatch": 100,  # Wrong room type for course
        "availability_violation": 100,  # Scheduling when not available
    },
    # Soft constraints (preferences and quality measures)
    "soft_constraints": {
        "instructor_preference": 10,  # Instructor time preferences
        "room_utilization": 5,  # Efficient room usage
        "schedule_compactness": 8,  # Minimize gaps in schedule
        "workload_balance": 6,  # Balanced instructor workload
        "student_break_time": 7,  # Adequate breaks for students
        "room_consistency": 4,  # Same room for course sessions
        "time_slot_distribution": 3,  # Even distribution across time slots
        "lunch_break_respect": 9,  # Respect lunch break requirements
        "early_late_penalty": 5,  # Penalty for very early/late classes
        "consecutive_classes": 2,  # Preference for consecutive classes
    },
    # Fitness function weights
    "fitness_weights": {
        "hard_constraint_weight": 100,  # α in fitness function
        "soft_constraint_weight": 1,  # β in fitness function
        "diversity_bonus": 0.1,  # Bonus for diverse solutions
    },
}

# Time Slot Configuration
TIME_SLOTS = {
    "days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
    "start_time": "08:00",
    "end_time": "18:00",
    "slot_duration": 90,  # minutes
    "break_duration": 15,  # minutes between slots
    "lunch_break": {"start": "12:00", "duration": 60},  # minutes
    # Generate time slots automatically
    "slots": [
        "08:00-09:30",
        "09:45-11:15",
        "11:30-13:00",
        "14:00-15:30",
        "15:45-17:15",
    ],
}

# Room Type Mappings
ROOM_TYPES = {
    "lecture": ["lecture_hall", "auditorium", "classroom"],
    "lab": ["computer_lab", "science_lab", "engineering_lab"],
    "seminar": ["seminar_room", "discussion_room", "small_classroom"],
    "workshop": ["workshop", "studio", "practical_room"],
}

# Course Type Requirements
COURSE_REQUIREMENTS = {
    "lecture": {
        "room_types": ["lecture", "seminar"],
        "equipment": ["projector", "whiteboard"],
        "min_capacity_ratio": 0.8,
    },
    "lab": {
        "room_types": ["lab"],
        "equipment": ["computers", "lab_equipment"],
        "min_capacity_ratio": 1.0,
    },
    "seminar": {
        "room_types": ["seminar", "lecture"],
        "equipment": ["whiteboard", "projector"],
        "min_capacity_ratio": 0.9,
    },
}

# Validation Rules
VALIDATION_RULES = {
    "max_sessions_per_day": 6,
    "max_consecutive_hours": 4,
    "min_break_between_sessions": 15,  # minutes
    "max_daily_hours_student": 8,
    "max_daily_hours_instructor": 8,
    "min_lunch_break": 30,  # minutes
    "max_gap_between_sessions": 4,  # hours
}

# Export Configuration

# Visualization Configuration
VISUALIZATION_CONFIG = {
    "colors": {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "success": "#2ca02c",
        "warning": "#d62728",
        "info": "#9467bd",
    },
    "chart_types": {
        "fitness_evolution": "line",
        "constraint_violations": "bar",
        "room_utilization": "heatmap",
        "instructor_workload": "bar",
    },
    "figure_size": (12, 8),
    "dpi": 300,
    "save_format": "pdf",
}
