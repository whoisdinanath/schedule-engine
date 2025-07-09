"""
Configuration settings for the Genetic Algorithm-based Timetabling System.
Contains default parameters and configuration options.
"""

from typing import Dict, Any
from dataclasses import dataclass
import os


@dataclass
class Config:
    """Main configuration class for the timetabling system."""
    
    # Data paths
    data_dir: str = "data"
    output_dir: str = "output"
    logs_dir: str = "logs"
    
    # File formats
    supported_input_formats: list = None
    default_output_format: str = "csv"
    
    # Logging
    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True
    
    # Performance
    max_memory_mb: int = 500
    max_runtime_minutes: int = 10
    
    def __post_init__(self):
        if self.supported_input_formats is None:
            self.supported_input_formats = ["csv", "json"]
        
        # Create directories if they don't exist
        for directory in [self.data_dir, self.output_dir, self.logs_dir]:
            os.makedirs(directory, exist_ok=True)


# Genetic Algorithm Configuration - PURE GA (No Local Search)
GA_CONFIG = {
    # Population parameters
    'population_size': 80,
    'generations': 200,
    'elite_size': 5,
    
    # Genetic operators - PURE GA only
    'crossover_rate': 0.8,
    'mutation_rate': 0.1,
    'tournament_size': 5,
    
    # Selection methods - genetic selection only
    'selection_method': 'tournament',  # 'tournament', 'roulette', 'rank'
    'crossover_method': 'uniform',     # 'uniform', 'single_point', 'two_point'
    'mutation_method': 'random',       # 'random', 'swap'
    
    # Termination criteria
    'max_generations': 500,
    'target_fitness': 0.0,
    'stagnation_limit': 20,
    'time_limit_minutes': 10,
    
    # Display and logging
    'verbose': True,
    'log_frequency': 10,
    'save_best_individual': True,
    'save_population_history': False
}

# Constraint Weights Configuration
CONSTRAINT_WEIGHTS = {
    # Hard constraints (violations should be heavily penalized)
    'hard_constraints': {
        'instructor_conflict': 1000,      # Instructor teaching multiple courses at same time
        'room_conflict': 1000,            # Room double-booked
        'group_conflict': 1000,           # Student group in multiple classes
        'course_group_isolation': 1000,   # Multiple groups from same course at same time
        'room_capacity': 1000,            # Room too small for group
        'instructor_qualification': 1000,  # Unqualified instructor assigned
        'room_type_mismatch': 1000,       # Wrong room type for course
        'availability_violation': 1000,   # Scheduling when not available
    },
    
    # Soft constraints (preferences and quality measures)
    'soft_constraints': {
        'instructor_preference': 10,       # Instructor time preferences
        'room_utilization': 5,            # Efficient room usage
        'schedule_compactness': 8,        # Minimize gaps in schedule
        'workload_balance': 6,            # Balanced instructor workload
        'student_break_time': 7,          # Adequate breaks for students
        'room_consistency': 4,            # Same room for course sessions
        'time_slot_distribution': 3,      # Even distribution across time slots
        'lunch_break_respect': 9,         # Respect lunch break requirements
        'early_late_penalty': 5,          # Penalty for very early/late classes
        'consecutive_classes': 2,         # Preference for consecutive classes
    },
    
    # Fitness function weights
    'fitness_weights': {
        'hard_constraint_weight': 100,    # α in fitness function
        'soft_constraint_weight': 1,      # β in fitness function
        'diversity_bonus': 0.1,           # Bonus for diverse solutions
    }
}

# Time Slot Configuration
TIME_SLOTS = {
    'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
    'start_time': '08:00',
    'end_time': '18:00',
    'slot_duration': 90,  # minutes
    'break_duration': 15,  # minutes between slots
    'lunch_break': {
        'start': '12:00',
        'duration': 60  # minutes
    },
    
    # Generate time slots automatically
    'slots': [
        '08:00-09:30',
        '09:45-11:15',
        '11:30-13:00',
        '14:00-15:30',
        '15:45-17:15'
    ]
}

# Room Type Mappings
ROOM_TYPES = {
    'lecture': ['lecture_hall', 'auditorium', 'classroom'],
    'lab': ['computer_lab', 'science_lab', 'engineering_lab'],
    'seminar': ['seminar_room', 'discussion_room', 'small_classroom'],
    'workshop': ['workshop', 'studio', 'practical_room']
}

# Course Type Requirements
COURSE_REQUIREMENTS = {
    'lecture': {
        'room_types': ['lecture', 'seminar'],
        'equipment': ['projector', 'whiteboard'],
        'min_capacity_ratio': 0.8
    },
    'lab': {
        'room_types': ['lab'],
        'equipment': ['computers', 'lab_equipment'],
        'min_capacity_ratio': 1.0
    },
    'seminar': {
        'room_types': ['seminar', 'lecture'],
        'equipment': ['whiteboard', 'projector'],
        'min_capacity_ratio': 0.9
    }
}

# Validation Rules
VALIDATION_RULES = {
    'max_sessions_per_day': 6,
    'max_consecutive_hours': 4,
    'min_break_between_sessions': 15,  # minutes
    'max_daily_hours_student': 8,
    'max_daily_hours_instructor': 8,
    'min_lunch_break': 30,  # minutes
    'max_gap_between_sessions': 4,  # hours
}

# Export Configuration
EXPORT_CONFIG = {
    'formats': {
        'csv': {
            'delimiter': ',',
            'encoding': 'utf-8',
            'include_header': True
        },
        'excel': {
            'sheet_name': 'Timetable',
            'include_formatting': True
        },
        'json': {
            'indent': 2,
            'ensure_ascii': False
        }
    },
    
    'fields': {
        'basic': ['course_id', 'course_name', 'instructor_id', 'room_id', 'day', 'time_slot'],
        'detailed': ['course_id', 'course_name', 'instructor_id', 'instructor_name', 
                    'room_id', 'room_name', 'day', 'time_slot', 'duration', 'group_ids'],
        'summary': ['day', 'time_slot', 'room_utilization', 'instructor_workload']
    }
}

# Visualization Configuration
VISUALIZATION_CONFIG = {
    'colors': {
        'primary': '#1f77b4',
        'secondary': '#ff7f0e',
        'success': '#2ca02c',
        'warning': '#d62728',
        'info': '#9467bd'
    },
    
    'chart_types': {
        'fitness_evolution': 'line',
        'constraint_violations': 'bar',
        'room_utilization': 'heatmap',
        'instructor_workload': 'bar'
    },
    
    'figure_size': (12, 8),
    'dpi': 300,
    'save_format': 'png'
}


def get_config() -> Config:
    """Get the default configuration instance."""
    return Config()


def update_config(config_dict: Dict[str, Any]) -> None:
    """Update configuration with new values."""
    global GA_CONFIG, CONSTRAINT_WEIGHTS
    
    if 'ga' in config_dict:
        GA_CONFIG.update(config_dict['ga'])
    
    if 'constraints' in config_dict:
        CONSTRAINT_WEIGHTS.update(config_dict['constraints'])


def load_config_from_file(file_path: str) -> Dict[str, Any]:
    """Load configuration from a JSON file."""
    import json
    
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Configuration file {file_path} not found. Using defaults.")
        return {}
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}. Using defaults.")
        return {}


def save_config_to_file(file_path: str, config: Dict[str, Any]) -> None:
    """Save configuration to a JSON file."""
    import json
    
    try:
        with open(file_path, 'w') as f:
            json.dump(config, f, indent=2)
    except Exception as e:
        print(f"Error saving configuration: {e}")


# Default configuration instance
default_config = get_config()
