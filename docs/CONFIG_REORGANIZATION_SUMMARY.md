# Configuration Reorganization Summary

## Changes Made

### 1. Created `config/time_config.py` ✅
**New centralized time configuration** aligned with QuantumTimeSystem:

- **Quantum parameters**: `QUANTUM_MINUTES`, `QUANTA_PER_HOUR`
- **Session preferences**: `MAX_SESSION_COALESCENCE`, `MAX_SESSIONS_PER_DAY`
- **Preferred hours**: `EARLIEST_PREFERRED_TIME`, `LATEST_PREFERRED_TIME` (wall-clock)
- **Break settings**: `MIDDAY_BREAK_START_TIME`, `MIDDAY_BREAK_END_TIME` (wall-clock)

**Helper functions**:
- `get_preferred_time_range_quanta(qts)` - Convert wall-clock to quantum indices
- `get_midday_break_quanta(qts)` - Get break period as quantum sets per day
- `quantum_to_day_and_within_day(quantum, qts)` - Convert continuous quantum to (day, offset)

### 2. Updated `src/constraints/soft.py` ✅
**Removed ALL magic numbers**, replaced with:
- Import from `config.time_config`
- Uses `QuantumTimeSystem` for all time conversions
- **Eliminated broken QUANTA_PER_DAY calculations**

**Changed approach**:
```python
# OLD (WRONG - assumes fixed quanta per day):
day = q // QUANTA_PER_DAY
within_day = q % QUANTA_PER_DAY

# NEW (CORRECT - works with continuous quantum system):
day, within_day = quantum_to_day_and_within_day(q, _QTS)
```

**Functions updated**:
1. `group_gaps_penalty()` - Uses quantum_to_day_and_within_day
2. `instructor_gaps_penalty()` - Uses quantum_to_day_and_within_day
3. `group_midday_break_violation()` - Uses get_midday_break_quanta
4. `course_split_penalty()` - Uses quantum_to_day_and_within_day
5. `early_or_late_session_penalty()` - Uses get_preferred_time_range_quanta

### 3. Updated `config/constraints.py` ✅
**Clarified separation of concerns**:
- Added documentation header explaining purpose
- Organized constraints into logical groups (compactness, time preferences, structure)
- Added reference to `config/time_config.py` for time parameters
- Kept only enable/disable flags and weights (no time parameters)

### 4. Created Documentation ✅
**New files**:
- `docs/CONFIG_SYSTEM.md` - Comprehensive config organization guide
  - Overview of each config file
  - Usage examples
  - Design principles (DO/DON'T)
  - Migration guide from old system
  - Continuous quantum system explanation

## Problem Solved

### Before:
❌ Magic numbers scattered in `soft.py`:
```python
QUANTA_PER_DAY = 96  # WRONG - assumes 15-min quanta, fixed day structure
MIDDAY_BREAK_START_QUANTA = 48  # Hardcoded absolute index
EARLIEST_ALLOWED_QUANTA = 32  # Meaningless with continuous system
```

❌ Broken calculations:
```python
day = q // QUANTA_PER_DAY  # FAILS with continuous quantum system
within_day = q % QUANTA_PER_DAY  # WRONG - days have variable quanta
```

### After:
✅ Centralized configuration in `config/time_config.py`:
```python
MIDDAY_BREAK_START_TIME = "12:00"  # Wall-clock time (universal)
EARLIEST_PREFERRED_TIME = "08:00"  # Clear, understandable
```

✅ Correct quantum conversion:
```python
day, within_day = quantum_to_day_and_within_day(q, qts)
break_quanta = get_midday_break_quanta(qts)  # Per-day quantum sets
```

## Testing Results

All validations passed ✅:

```
✓ time_config.py loaded
✓ Break quanta computed: 5 days configured
✓ Preferred hours: 5 days configured
✓ All time_config functions working

✓ Total soft constraints: 5
✓ Enabled soft constraints: 1
✓ Constraints: group_gaps_penalty, instructor_gaps_penalty, 
  group_midday_break_violation, course_split_penalty, 
  early_or_late_session_penalty

✓ Hard constraints: 6 defined
✓ Soft constraints: 5 defined
✓ Enabled: 6 hard, 1 soft
```

## Configuration File Structure

```
config/
├── __init__.py
├── constraints.py         # Constraint enable/disable flags & weights
├── time_config.py         # NEW: Time parameters aligned with QuantumTimeSystem
├── ga_params.py           # GA hyperparameters
├── calendar_config.py     # Export display settings
├── color_palette.py       # Visualization colors
└── io_paths.py            # Input/output paths
```

## Impact on Codebase

### Files Modified:
1. `config/time_config.py` - **CREATED**
2. `config/constraints.py` - Updated with documentation
3. `src/constraints/soft.py` - Removed magic numbers, fixed quantum calculations
4. `docs/CONFIG_SYSTEM.md` - **CREATED**
5. `docs/CONFIG_REORGANIZATION_SUMMARY.md` - **THIS FILE**

### Files Validated (no changes needed):
- `src/ga/evaluator/fitness.py` - Already uses constraint registry ✅
- `src/ga/evaluator/detailed_fitness.py` - Already uses constraint registry ✅
- `src/constraints/hard.py` - No magic numbers ✅
- `src/encoder/quantum_time_system.py` - Source of truth ✅

## Usage Instructions

### To modify time preferences:
Edit `config/time_config.py`:
```python
EARLIEST_PREFERRED_TIME = "07:00"  # Start earlier
MIDDAY_BREAK_START_TIME = "12:30"  # Later lunch
MAX_SESSION_COALESCENCE = 4  # Prefer 4-quantum blocks
```

### To enable/disable constraints:
Edit `config/constraints.py`:
```python
SOFT_CONSTRAINTS_CONFIG = {
    "group_midday_break_violation": {"enabled": True, "weight": 2.0},
}
```

### To verify configuration:
```bash
python scripts/show_config.py
python scripts/show_soft_config.py
```

## Design Principles Enforced

1. **Single Source of Truth**: QuantumTimeSystem defines time structure
2. **No Magic Numbers**: All parameters come from config files
3. **Separation of Concerns**: Time params ≠ constraint weights ≠ GA params
4. **Continuous Quantum Support**: All time operations work with variable quanta per day
5. **Wall-Clock Configuration**: Users configure in HH:MM format (intuitive)

## Backward Compatibility

✅ **Fully compatible** - No breaking changes to:
- Constraint function signatures
- Evaluator interface
- Constraint registry system
- Input data formats

Only internal implementations updated to use centralized config.
