# Flexible Constraint System - Complete Implementation

## Overview

**Registry-based architecture** for both hard and soft constraints. Enable/disable/weight any constraint via `config/constraints.py` without touching evaluator code.

## Architecture

### Hard Constraints (Feasibility)
- **Purpose**: Ensure schedule validity (no conflicts, qualifications met, etc.)
- **Default**: All enabled with weight 1.0
- **Impact**: Must reach zero for feasible solution

### Soft Constraints (Quality)
- **Purpose**: Improve schedule quality (compactness, breaks, timing)
- **Default**: Configurable (some enabled, some disabled)
- **Impact**: Lower is better, but non-zero is acceptable

## Configuration

**File:** `config/constraints.py`

```python
HARD_CONSTRAINTS_CONFIG = {
    "no_group_overlap": {"enabled": True, "weight": 1.0},
    "no_instructor_conflict": {"enabled": True, "weight": 1.0},
    "instructor_not_qualified": {"enabled": True, "weight": 1.0},
    "room_type_mismatch": {"enabled": True, "weight": 1.0},
    "availability_violations": {"enabled": True, "weight": 1.0},
    "incomplete_or_extra_sessions": {"enabled": True, "weight": 1.0},
}

SOFT_CONSTRAINTS_CONFIG = {
    "group_gaps_penalty": {"enabled": True, "weight": 1.0},
    "instructor_gaps_penalty": {"enabled": False, "weight": 1.0},
    "group_midday_break_violation": {"enabled": False, "weight": 1.0},
    "course_split_penalty": {"enabled": False, "weight": 1.0},
    "early_or_late_session_penalty": {"enabled": False, "weight": 1.0},
}
```

## Available Constraints

### Hard Constraints (6 total)
1. **`no_group_overlap`** – Prevents students from being in two places at once
2. **`no_instructor_conflict`** – Prevents instructor double-booking
3. **`instructor_not_qualified`** – Ensures instructors are qualified for courses
4. **`room_type_mismatch`** – Matches room features to course requirements
5. **`availability_violations`** – Respects group/instructor/room availability
6. **`incomplete_or_extra_sessions`** – Ensures correct quanta per course per group

### Soft Constraints (5 total)
1. **`group_gaps_penalty`** – Minimizes idle gaps in student schedules
2. **`instructor_gaps_penalty`** – Minimizes gaps in instructor schedules
3. **`group_midday_break_violation`** – Ensures lunch breaks for students
4. **`course_split_penalty`** – Prefers continuous session blocks
5. **`early_or_late_session_penalty`** – Avoids very early/late sessions

## Usage

### View Current Configuration
```bash
python scripts/show_config.py
```

### Enable/Disable Constraints
Edit `config/constraints.py`:
```python
"instructor_gaps_penalty": {"enabled": True, "weight": 3.0}  # Enable with 3x weight
```

### Run GA with Current Config
```bash
python main.py
```
The system automatically uses only enabled constraints!

## Adding New Constraints

### Hard Constraint Example
1. **Define function in `src/constraints/hard.py`:**
```python
def my_hard_constraint(sessions: List[CourseSession], courses: Dict[str, Course] = None) -> int:
    violations = 0
    # ... your logic
    return violations
```

2. **Register in `get_all_hard_constraints()`:**
```python
def get_all_hard_constraints():
    return {
        # ... existing
        "my_hard_constraint": my_hard_constraint,
    }
```

3. **Add to config:**
```python
HARD_CONSTRAINTS_CONFIG = {
    # ... existing
    "my_hard_constraint": {"enabled": True, "weight": 1.0},
}
```

4. **If it needs courses parameter, update evaluators:**
   Add constraint name to the list in `fitness.py` and `detailed_fitness.py`:
```python
if constraint_name in ["instructor_not_qualified", "incomplete_or_extra_sessions", "my_hard_constraint"]:
    penalty = constraint_func(sessions, courses)
```

### Soft Constraint Example
Same process, but in `soft.py` and `SOFT_CONSTRAINTS_CONFIG`. Soft constraints never need extra parameters.

## Weight Tuning Guidelines

### Hard Constraints
- **Default 1.0** – All violations equally bad
- **Increase weight** (2.0-10.0) to prioritize eliminating specific violation types
- **Use case**: If room mismatches are more critical than instructor conflicts

### Soft Constraints
- **0.5** = Low priority
- **1.0** = Normal priority (default)
- **3.0** = Important
- **5.0** = Very important
- **10.0** = Critical

## Benefits

✅ **Zero-code toggling** – Change config, not evaluators  
✅ **Weight tuning** – Fine-tune constraint importance  
✅ **Automatic integration** – Plots/tracking use enabled lists  
✅ **Type-safe** – Only registered constraints can run  
✅ **Extensible** – Add constraints in 3-4 steps  
✅ **Uniform architecture** – Same pattern for hard and soft  

## Testing

```bash
# Test both hard and soft registries
python test/test_constraint_registry.py

# Test only soft constraints (legacy)
python test/test_soft_constraints_registry.py
```

All tests passing ✓

## Documentation Files

- **`docs/flexible-constraints-system.md`** – This file (complete reference)
- **`docs/flexible-soft-constraints.md`** – Soft constraints only (legacy)
- **`docs/soft-constraint-examples.md`** – Configuration examples
- **`docs/FLEXIBLE_CONSTRAINTS_SUMMARY.md`** – Implementation summary
- **`docs/SOFT_CONSTRAINTS_QUICK_REF.txt`** – Quick reference card

## Scripts

- **`scripts/show_config.py`** – View all constraints (hard + soft)
- **`scripts/show_soft_config.py`** – View soft constraints only (legacy)

## Current Default State

**Hard Constraints:** 6/6 enabled (all must be satisfied)  
**Soft Constraints:** 1/5 enabled (group_gaps_penalty only)

Easily customize by editing `config/constraints.py`!

## Migration Notes

- All constraint functions active and registered
- Old hardcoded imports replaced with dynamic registries
- Backward compatible – existing behavior preserved
- No changes needed to data files or other modules
- Main.py automatically tracks enabled constraints for plotting
