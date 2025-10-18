"""
Time Configuration for Schedule Engine

All time-related parameters derived from and aligned with QuantumTimeSystem.
These settings control soft constraint preferences for session scheduling.

IMPORTANT: This uses a CONTINUOUS quantum system where quantum indices
only cover operating hours. Do NOT use QUANTA_PER_DAY calculations.
Use QuantumTimeSystem methods for all time conversions.
"""

# ============================================================================
# QUANTUM TIME SYSTEM PARAMETERS
# ============================================================================
# These mirror the QuantumTimeSystem constants for reference and soft constraints

# Core quantum parameters (must match QuantumTimeSystem.QUANTUM_MINUTES)
QUANTUM_MINUTES = 60  # Duration of one quantum (also unit course duration)
QUANTA_PER_HOUR = 60 // QUANTUM_MINUTES  # Number of quanta per hour

# ============================================================================
# SOFT CONSTRAINT PREFERENCES
# ============================================================================

# Session Coalescence Settings
# -----------------------------
# Preferred minimum size for continuous session blocks
# Penalizes courses split into blocks smaller than this
MAX_SESSION_COALESCENCE = 3  # Max preferred quanta per continuous session block

# Preferred Operating Hours (Wall-Clock Time)
# -------------------------------------------
# Sessions outside these hours incur penalties (early_or_late_session_penalty)
EARLIEST_PREFERRED_TIME = "10:00"  # Earliest preferred start time
LATEST_PREFERRED_TIME = "17:00"  # Latest preferred end time

# Midday Break Settings (Wall-Clock Time)
# ----------------------------------------
# Expected break period for groups (group_midday_break_violation)
MIDDAY_BREAK_START_TIME = "12:00"  # Start of preferred lunch break
MIDDAY_BREAK_END_TIME = "14:00"  # End of preferred lunch break

# Session Distribution Limits
# ----------------------------
# Maximum number of sessions a group/instructor should have per day
MAX_SESSIONS_PER_DAY = 5  # Threshold for excessive daily load

# Session Block Clustering Settings
# ----------------------------------
# Encourage sessions to be clustered into preferred block sizes
# Example: 6 quanta course → [3,3] or [2,2,2] preferred over [1,1,1,1,1,1]
PREFERRED_BLOCK_SIZE_MIN = 2  # Minimum preferred block size (quanta)
PREFERRED_BLOCK_SIZE_MAX = 3  # Maximum preferred block size (quanta)
ISOLATED_SESSION_PENALTY = 5  # Heavy penalty for isolated 1-quantum sessions
OVERSIZED_BLOCK_PENALTY_PER_QUANTUM = (
    1  # Penalty per quantum beyond max (for 4+ blocks)
)

# ============================================================================
# HELPER FUNCTIONS FOR SOFT CONSTRAINTS
# ============================================================================


def get_preferred_time_range_quanta(qts):
    """
    Get quantum indices for preferred operating hours.

    Args:
        qts: QuantumTimeSystem instance

    Returns:
        Tuple of (earliest_allowed_quanta_dict, latest_allowed_quanta_dict)
        Each dict maps day_name -> quantum_index within that day
    """
    earliest_quanta = {}
    latest_quanta = {}

    for day in qts.DAY_NAMES:
        if not qts.is_operational(day):
            continue

        try:
            # Get quantum for earliest preferred time
            earliest_q = qts.time_to_quanta(day, EARLIEST_PREFERRED_TIME)
            # Convert to within-day index
            day_offset = qts.day_quanta_offset[day]
            earliest_quanta[day] = earliest_q - day_offset

            # Get quantum for latest preferred time
            latest_q = qts.time_to_quanta(day, LATEST_PREFERRED_TIME)
            latest_quanta[day] = latest_q - day_offset

        except ValueError:
            # Time outside operating hours for this day - skip
            continue

    return earliest_quanta, latest_quanta


def get_midday_break_quanta(qts):
    """
    Get quantum indices for midday break period.

    Args:
        qts: QuantumTimeSystem instance

    Returns:
        Dict mapping day_name -> set of quantum indices (within-day) for break period
    """
    break_quanta = {}

    for day in qts.DAY_NAMES:
        if not qts.is_operational(day):
            continue

        try:
            # Get quanta for break start and end
            break_start_q = qts.time_to_quanta(day, MIDDAY_BREAK_START_TIME)
            break_end_q = qts.time_to_quanta(day, MIDDAY_BREAK_END_TIME)

            # Convert to within-day indices
            day_offset = qts.day_quanta_offset[day]
            within_day_start = break_start_q - day_offset
            within_day_end = break_end_q - day_offset

            # Create set of break quanta (within-day indices)
            break_quanta[day] = set(range(within_day_start, within_day_end))

        except ValueError:
            # Break time outside operating hours for this day - skip
            continue

    return break_quanta


def quantum_to_day_and_within_day(quantum, qts):
    """
    Convert continuous quantum to (day_name, within_day_quantum).

    Args:
        quantum: Continuous quantum index
        qts: QuantumTimeSystem instance

    Returns:
        Tuple of (day_name, within_day_quantum_index)

    Example:
        If Sunday has 12 quanta and Monday has 12 quanta:
        quantum 0 -> ('Sunday', 0)
        quantum 11 -> ('Sunday', 11)
        quantum 12 -> ('Monday', 0)
    """
    for day in qts.DAY_NAMES:
        if qts.day_quanta_offset[day] is None:
            continue

        day_offset = qts.day_quanta_offset[day]
        day_count = qts.day_quanta_count[day]

        if day_offset <= quantum < day_offset + day_count:
            within_day = quantum - day_offset
            return day, within_day

    raise ValueError(f"Quantum {quantum} out of valid range")


# ============================================================================
# USAGE NOTES
# ============================================================================
"""
To use in soft constraints:

1. Import QuantumTimeSystem and this config:
   from src.encoder.quantum_time_system import QuantumTimeSystem
   from config.time_config import get_midday_break_quanta, quantum_to_day_and_within_day

2. Create QTS instance (should be passed from evaluator context):
   qts = QuantumTimeSystem()

3. Get time-based constraint parameters:
   break_quanta = get_midday_break_quanta(qts)
   
4. Convert continuous quanta to day-relative indices:
   day, within_day_q = quantum_to_day_and_within_day(quantum, qts)

5. NEVER use QUANTA_PER_DAY or modulo arithmetic directly!
   OLD: day = q // QUANTA_PER_DAY  # WRONG - doesn't work with continuous system
   NEW: day, _ = quantum_to_day_and_within_day(q, qts)  # CORRECT
"""
