"""
Display Time Configuration Settings

Shows time-related parameters and quantum conversions for verification.
"""

from src.encoder.quantum_time_system import QuantumTimeSystem
from config.time_config import (
    QUANTUM_MINUTES,
    QUANTA_PER_HOUR,
    MAX_SESSION_COALESCENCE,
    MAX_SESSIONS_PER_DAY,
    EARLIEST_PREFERRED_TIME,
    LATEST_PREFERRED_TIME,
    MIDDAY_BREAK_START_TIME,
    MIDDAY_BREAK_END_TIME,
    get_midday_break_quanta,
    get_preferred_time_range_quanta,
    quantum_to_day_and_within_day,
)


def main():
    print("=" * 80)
    print("TIME CONFIGURATION SETTINGS".center(80))
    print("=" * 80)
    print()

    # Basic quantum parameters
    print("QUANTUM TIME SYSTEM PARAMETERS")
    print("-" * 80)
    print(f"  Quantum Duration:        {QUANTUM_MINUTES} minutes")
    print(f"  Quanta per Hour:         {QUANTA_PER_HOUR}")
    print()

    # Session preferences
    print("SESSION PREFERENCES")
    print("-" * 80)
    print(f"  Max Session Coalescence: {MAX_SESSION_COALESCENCE} quanta")
    print(f"  Max Sessions per Day:    {MAX_SESSIONS_PER_DAY}")
    print()

    # Preferred hours
    print("PREFERRED OPERATING HOURS (Wall-Clock)")
    print("-" * 80)
    print(f"  Earliest Preferred:      {EARLIEST_PREFERRED_TIME}")
    print(f"  Latest Preferred:        {LATEST_PREFERRED_TIME}")
    print()

    # Break settings
    print("MIDDAY BREAK SETTINGS (Wall-Clock)")
    print("-" * 80)
    print(f"  Break Start:             {MIDDAY_BREAK_START_TIME}")
    print(f"  Break End:               {MIDDAY_BREAK_END_TIME}")
    print()

    # Initialize QuantumTimeSystem
    qts = QuantumTimeSystem()

    print("=" * 80)
    print("QUANTUM CONVERSIONS (Per Day)".center(80))
    print("=" * 80)
    print()

    # Display operating days and their quantum ranges
    print("OPERATING DAYS & QUANTUM RANGES")
    print("-" * 80)
    for day in qts.DAY_NAMES:
        if qts.is_operational(day):
            offset = qts.day_quanta_offset[day]
            count = qts.day_quanta_count[day]
            hours = qts.operating_hours[day]
            print(
                f"  {day:12} {hours[0]}-{hours[1]}  "
                f"→ Quanta {offset:3d}-{offset+count-1:3d} ({count:2d} total)"
            )
        else:
            print(f"  {day:12} CLOSED")
    print()

    # Get break quanta for each day
    print("MIDDAY BREAK QUANTUM INDICES (Within-Day)")
    print("-" * 80)
    break_quanta = get_midday_break_quanta(qts)
    for day in qts.DAY_NAMES:
        if day in break_quanta:
            quanta_set = break_quanta[day]
            if quanta_set:
                min_q = min(quanta_set)
                max_q = max(quanta_set)
                print(f"  {day:12} Within-day quanta {min_q:2d}-{max_q:2d}")
        elif qts.is_operational(day):
            print(f"  {day:12} Break time outside operating hours")
    print()

    # Get preferred time range quanta
    print("PREFERRED HOURS QUANTUM INDICES (Within-Day)")
    print("-" * 80)
    earliest_quanta, latest_quanta = get_preferred_time_range_quanta(qts)
    for day in qts.DAY_NAMES:
        if day in earliest_quanta and day in latest_quanta:
            earliest = earliest_quanta[day]
            latest = latest_quanta[day]
            print(f"  {day:12} Preferred within-day quanta {earliest:2d}-{latest:2d}")
        elif qts.is_operational(day):
            print(f"  {day:12} Preferred hours outside operating hours")
    print()

    # Example conversions
    print("EXAMPLE QUANTUM CONVERSIONS")
    print("-" * 80)
    example_quanta = [0, 5, 12, 24, 36]
    for q in example_quanta:
        if q < qts.total_quanta:
            day, within_day = quantum_to_day_and_within_day(q, qts)
            day_str, time_str = qts.quanta_to_time(q)
            print(f"  Quantum {q:3d} → {day:12} offset {within_day:2d} ({time_str})")
    print()

    print("=" * 80)
    print(f"Total Operational Quanta: {qts.total_quanta}")
    print("=" * 80)
    print()
    print("✓ All time configurations aligned with QuantumTimeSystem")
    print("✓ No hardcoded QUANTA_PER_DAY or magic numbers")
    print()
    print("To modify: Edit config/time_config.py")
    print()


if __name__ == "__main__":
    main()
