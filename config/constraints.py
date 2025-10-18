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
    "no_group_overlap": {"enabled": True, "weight": 2.0},
    "no_instructor_conflict": {"enabled": True, "weight": 2.0},
    "instructor_not_qualified": {"enabled": True, "weight": 2.0},
    "room_type_mismatch": {"enabled": True, "weight": 2.0},
    "availability_violations": {"enabled": True, "weight": 2.0},
    "incomplete_or_extra_sessions": {"enabled": True, "weight": 1.0},
}

# ============================================================================
# SOFT CONSTRAINTS CONFIGURATION
# ============================================================================
# Enable/disable individual soft constraints and set their weights
# Four soft constraints are used:
# 1. group_gaps_penalty - Minimize gaps in group schedules
# 2. instructor_gaps_penalty - Minimize gaps in instructor schedules
# 3. group_midday_break_violation - Avoid scheduling during midday break
# 4. session_block_clustering_penalty - Encourage 2-3 quantum session blocks
SOFT_CONSTRAINTS_CONFIG = {
    # Format: "constraint_name": {"enabled": bool, "weight": float}
    "group_gaps_penalty": {"enabled": True, "weight": 1.0},
    "instructor_gaps_penalty": {"enabled": True, "weight": 1.0},
    "group_midday_break_violation": {"enabled": True, "weight": 1.0},
    "session_block_clustering_penalty": {"enabled": True, "weight": 1.0},
}

# ============================================================================
# SOFT CONSTRAINTS NORMALIZATION PARAMETER
# ============================================================================
