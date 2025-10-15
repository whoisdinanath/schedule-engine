# Configuration System Organization

## Overview

The Schedule Engine uses a centralized, modular configuration system aligned with the continuous QuantumTimeSystem. All configurations are located in the `config/` folder.

## Configuration Files

### 1. `config/time_config.py` - Time & Quantum Parameters
**Purpose**: All time-related parameters derived from and aligned with QuantumTimeSystem.

**Contains**:
- Quantum duration settings (QUANTUM_MINUTES, QUANTA_PER_HOUR)
- Session coalescence preferences (MAX_SESSION_COALESCENCE)
- Preferred operating hours (EARLIEST_PREFERRED_TIME, LATEST_PREFERRED_TIME)
- Midday break settings (MIDDAY_BREAK_START_TIME, MIDDAY_BREAK_END_TIME)
- Daily session limits (MAX_SESSIONS_PER_DAY)
- Helper functions for converting times to quantum indices

**Key Functions**:
- `get_preferred_time_range_quanta(qts)` - Get preferred hours as quantum indices
- `get_midday_break_quanta(qts)` - Get break period as quantum indices
- `quantum_to_day_and_within_day(quantum, qts)` - Convert continuous quantum to day+offset

**Usage**:
```python
from src.encoder.quantum_time_system import QuantumTimeSystem
from config.time_config import get_midday_break_quanta, MAX_SESSION_COALESCENCE

qts = QuantumTimeSystem()
break_quanta = get_midday_break_quanta(qts)
```

---

### 2. `config/constraints.py` - Constraint Enable/Disable & Weights
**Purpose**: Control which constraints are active and their relative importance.

**Contains**:
- `HARD_CONSTRAINTS_CONFIG` - Hard constraint flags and weights
- `SOFT_CONSTRAINTS_CONFIG` - Soft constraint flags and weights

**Structure**:
```python
SOFT_CONSTRAINTS_CONFIG = {
    "constraint_name": {"enabled": bool, "weight": float},
}
```

**Usage**:
```python
from config.constraints import SOFT_CONSTRAINTS_CONFIG

if SOFT_CONSTRAINTS_CONFIG["group_gaps_penalty"]["enabled"]:
    weight = SOFT_CONSTRAINTS_CONFIG["group_gaps_penalty"]["weight"]
```

---

### 3. `config/ga_params.py` - Genetic Algorithm Parameters
**Purpose**: GA hyperparameters (population size, generations, crossover/mutation rates).

**Contains**:
- `POP_SIZE` - Population size
- `NGEN` - Number of generations
- `CXPB` - Crossover probability
- `MUTPB` - Mutation probability

---

### 4. `config/calendar_config.py` - Export/Display Settings
**Purpose**: Visual calendar export settings (PDF, display format).

**Contains**:
- `EXCAL_QUANTUM_MINUTES` - Quantum duration for calendar display
- `EXCAL_START_HOUR` - Calendar start hour
- `EXCAL_END_HOUR` - Calendar end hour
- `EXCAL_DEFAULT_OUTPUT_PDF` - Default PDF filename

---

### 5. `config/color_palette.py` - Visualization Colors
**Purpose**: Color schemes for reports, plots, and calendar exports.

---

### 6. `config/io_paths.py` - Input/Output Paths
**Purpose**: File paths for data inputs and outputs.

---

## Key Design Principles

### ✅ DO:
1. **Use QuantumTimeSystem for all time operations** - Never hardcode QUANTA_PER_DAY
2. **Import from config modules** - Never define magic numbers in constraint files
3. **Keep concerns separated**:
   - Time parameters → `time_config.py`
   - Constraint toggles → `constraints.py`
   - GA settings → `ga_params.py`
4. **Use helper functions** - e.g., `quantum_to_day_and_within_day()` instead of modulo arithmetic

### ❌ DON'T:
1. **Never use `day = q // QUANTA_PER_DAY`** - Breaks with continuous quantum system
2. **Never use `q % QUANTA_PER_DAY`** - Assumes fixed quanta per day (wrong!)
3. **Never hardcode time values in constraint functions** - Use config/time_config.py
4. **Never mix configuration types** - Keep time params separate from constraint weights

## Migration from Old System

### Old (WRONG):
```python
# DON'T DO THIS!
QUANTA_PER_DAY = 96
MIDDAY_BREAK_START_QUANTA = 48
day = q // QUANTA_PER_DAY
within_day = q % QUANTA_PER_DAY
```

### New (CORRECT):
```python
# DO THIS!
from config.time_config import quantum_to_day_and_within_day, get_midday_break_quanta
from src.encoder.quantum_time_system import QuantumTimeSystem

qts = QuantumTimeSystem()
day, within_day = quantum_to_day_and_within_day(q, qts)
break_quanta = get_midday_break_quanta(qts)
```

## Continuous Quantum System Notes

The system uses **continuous quantum indexing** where:
- Only operating hours get quantum indices
- Quantum 0, 1, 2, ... N-1 cover ALL operational time across the week
- No indices for non-operating times (nights, closed days)
- Different days may have different numbers of quanta

**Example**:
```
Sunday: 08:00-20:00 (12 hours = 12 quanta)
Monday: 08:00-20:00 (12 hours = 12 quanta)

Quantum indices:
0-11: Sunday 08:00-19:00
12-23: Monday 08:00-19:00
(No indices for Sunday 20:00-23:59, Monday 00:00-07:59, etc.)
```

## Testing Configuration Changes

After modifying configs:
1. Run `python scripts/show_config.py` to verify settings
2. Run `python main.py` with reduced NGEN for smoke test
3. Check `output/evaluation_*/` for constraint violation reports
4. Verify time-based constraints use correct quantum ranges
