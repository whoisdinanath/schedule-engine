"""
UCTP Constraint Configuration

This file contains constraint enable/disable flags and weights.
For time-related parameters (break times, preferred hours, etc.),
see config/time_config.py which derives values from QuantumTimeSystem.
"""

# ============================================================================
# HARD CONSTRAINTS CONFIGURATION
# ============================================================================
# Enable/disable individual hard constraints and set their weights
HARD_CONSTRAINTS_CONFIG = {
    # Format: "constraint_name": {"enabled": bool, "weight": float}
    "no_group_overlap": {"enabled": False, "weight": 1.0},
    "no_instructor_conflict": {"enabled": False, "weight": 1.0},
    "instructor_not_qualified": {"enabled": False, "weight": 1.0},
    "room_type_mismatch": {"enabled": False, "weight": 1.0},
    "availability_violations": {"enabled": False, "weight": 1.0},
    "incomplete_or_extra_sessions": {"enabled": True, "weight": 1.0},
}

# ============================================================================
# SOFT CONSTRAINTS CONFIGURATION
# ============================================================================
# Enable/disable individual soft constraints and set their weights
SOFT_CONSTRAINTS_CONFIG = {
    # Format: "constraint_name": {"enabled": bool, "weight": float}
    # Compactness constraints (minimize gaps in schedules)
    "group_gaps_penalty": {"enabled": True, "weight": 1.0},
    "instructor_gaps_penalty": {"enabled": False, "weight": 1.0},
    # Time preference constraints (see config/time_config.py for time parameters)
    "group_midday_break_violation": {"enabled": False, "weight": 1.0},
    "early_or_late_session_penalty": {"enabled": False, "weight": 1.0},
    # Session structure constraints
    "course_split_penalty": {"enabled": False, "weight": 1.0},
}

# ============================================================================
# SOFT CONSTRAINTS NORMALIZATION PARAMETER
# ============================================================================
