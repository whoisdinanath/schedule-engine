# ============================================================================
# DEPRECATED - DO NOT USE
# ============================================================================
# This file was created as a reference during multiprocessing optimization.
# The optimized values have been merged into ga_params.py (the active config).
# You can safely DELETE this file.
# ============================================================================

# Optimized GA Parameters for Multiprocessing

# RECOMMENDED CONFIGURATION FOR MAXIMUM PERFORMANCE
# After fixing multiprocessing bug, these settings maximize CPU utilization

# Population size - INCREASED for better parallelization
# Small populations (10) waste parallel potential
# Larger populations (100) keep all cores busy
POP_SIZE = 100  # Changed from 10

# Number of generations - adjusted for larger population
# Larger populations converge faster, need fewer generations
NGEN = 100  # Changed from 50

# Crossover and mutation probabilities - unchanged
CXPB, MUTPB = 0.8, 0.3

# Parallelization Settings
USE_MULTIPROCESSING = True
NUM_WORKERS = None  # None = use all available CPU cores

# REPAIR HEURISTICS CONFIGURATION
# (unchanged - this is already optimal)
REPAIR_HEURISTICS_CONFIG = {
    "enabled": True,
    "max_iterations": 3,
    "apply_after_mutation": True,
    "apply_after_crossover": False,
    "memetic_mode": False,
    "elite_percentage": 0.2,
    "memetic_iterations": 5,
    "violation_threshold": None,
    "heuristics": {
        "repair_availability_violations": {
            "enabled": True,
            "priority": 1,
            "description": "Fix instructor/group/room availability violations",
        },
        "repair_group_overlaps": {
            "enabled": True,
            "priority": 2,
            "description": "Fix group schedule overlaps",
        },
        "repair_room_conflicts": {
            "enabled": True,
            "priority": 3,
            "description": "Fix room double-booking conflicts",
        },
        "repair_instructor_conflicts": {
            "enabled": True,
            "priority": 4,
            "description": "Fix instructor double-booking conflicts",
        },
        "repair_instructor_qualifications": {
            "enabled": True,
            "priority": 5,
            "description": "Reassign unqualified instructors",
        },
        "repair_room_type_mismatches": {
            "enabled": True,
            "priority": 6,
            "description": "Fix room type mismatches (lab/lecture)",
        },
        "repair_incomplete_or_extra_sessions": {
            "enabled": True,
            "priority": 7,
            "description": "Add missing or remove extra sessions",
            "warning": "Can modify individual length - use with caution",
        },
    },
}

# NOTES:
# - POP_SIZE=100 provides ~5-7× speedup on 8-core CPU vs POP_SIZE=10
# - Total time may increase slightly due to more evaluations, but quality improves
# - For quick tests, use POP_SIZE=50, NGEN=50
# - For production, use POP_SIZE=200, NGEN=150 for best quality
