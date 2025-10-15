# Flexible Soft Constraint System

## Overview

Registry-based architecture for soft constraints. Enable/disable/weight constraints via `config/constraints.py` without touching evaluator code.

## Configuration

**File:** `config/constraints.py`

```python
SOFT_CONSTRAINTS_CONFIG = {
    "group_gaps_penalty": {"enabled": True, "weight": 1.0},
    "instructor_gaps_penalty": {"enabled": False, "weight": 1.0},
    # ... more constraints
}
```

- `enabled`: Toggle constraint on/off
- `weight`: Multiplier for penalty (higher = more important)

## Available Constraints

1. **`group_gaps_penalty`** – Penalizes idle gaps in daily group schedules
2. **`instructor_gaps_penalty`** – Penalizes instructor schedule gaps
3. **`group_midday_break_violation`** – Ensures midday break for groups
4. **`course_split_penalty`** – Discourages fragmented sessions
5. **`early_or_late_session_penalty`** – Avoids early/late hours

## Adding New Constraints

1. **Define function in `src/constraints/soft.py`:**
   ```python
   def my_custom_penalty(sessions: List[CourseSession]) -> int:
       """Calculate custom penalty."""
       penalty = 0
       # ... your logic
       return penalty
   ```

2. **Register in `get_all_soft_constraints()`:**
   ```python
   def get_all_soft_constraints():
       return {
           # ... existing
           "my_custom_penalty": my_custom_penalty,
       }
   ```

3. **Add to config (`config/constraints.py`):**
   ```python
   SOFT_CONSTRAINTS_CONFIG = {
       # ... existing
       "my_custom_penalty": {"enabled": True, "weight": 2.0},
   }
   ```

## Usage in Evaluators

Evaluators (`fitness.py`, `detailed_fitness.py`) automatically use registry:

```python
enabled = get_enabled_soft_constraints()
for name, info in enabled.items():
    penalty = info["weight"] * info["function"](sessions)
```

## Benefits

- **Zero code edits** to enable/disable constraints
- **Weight tuning** without touching evaluators
- **Automatic tracking** in `main.py` (plots use enabled list)
- **Type-safe** – only registered constraints are callable

## Testing

Run: `python test/test_soft_constraints_registry.py`

Verifies registry integrity, config filtering, weight application.
