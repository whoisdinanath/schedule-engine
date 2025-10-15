# Flexible Soft Constraint System - Summary

## What Was Implemented

A **registry-based architecture** that makes soft constraints fully configurable without editing evaluator code.

## Key Changes

### 1. Configuration File (`config/constraints.py`)
```python
SOFT_CONSTRAINTS_CONFIG = {
    "constraint_name": {"enabled": bool, "weight": float},
    # ...
}
```

### 2. Registry Functions (`src/constraints/soft.py`)
- `get_all_soft_constraints()` – Returns all available constraint functions
- `get_enabled_soft_constraints()` – Filters by config, includes weights

### 3. Updated Evaluators
- `src/ga/evaluator/fitness.py` – Uses registry dynamically
- `src/ga/evaluator/detailed_fitness.py` – Same approach

### 4. Dynamic Tracking (`main.py`)
- Reads enabled constraints from config
- Only tracks/plots active constraints

## How to Use

### View Current Configuration
```bash
python scripts/show_soft_config.py
```

### Enable/Disable Constraints
Edit `config/constraints.py`:
```python
"instructor_gaps_penalty": {"enabled": True, "weight": 3.0}  # Enable with 3x weight
```

### Add New Constraint

1. Write function in `soft.py`:
```python
def my_penalty(sessions: List[CourseSession]) -> int:
    return penalty_value
```

2. Register it:
```python
def get_all_soft_constraints():
    return {
        # ... existing
        "my_penalty": my_penalty,
    }
```

3. Configure it:
```python
SOFT_CONSTRAINTS_CONFIG = {
    # ... existing
    "my_penalty": {"enabled": True, "weight": 1.0},
}
```

That's it! No changes to evaluators or main.py needed.

## Benefits

✅ **Zero-code toggling** – Change config, not code  
✅ **Weight tuning** – Fine-tune importance without touching evaluators  
✅ **Automatic integration** – Plots/tracking use enabled list  
✅ **Type-safe** – Only registered constraints can be called  
✅ **Extensible** – Add new constraints in 3 steps  

## Testing

```bash
python test/test_soft_constraints_registry.py
```

All tests passing ✓

## Documentation

- **`docs/flexible-soft-constraints.md`** – Technical details
- **`docs/soft-constraint-examples.md`** – Configuration examples
- **`scripts/show_soft_config.py`** – View current setup

## Current State

**Enabled:** 1/5 constraints  
- ✓ `group_gaps_penalty` (weight=1.0)

**Disabled:** 4 constraints (easily enable via config)

## Migration Notes

- All soft constraint functions uncommented and active
- Old hardcoded lists replaced with dynamic registry
- Backward compatible – existing behavior preserved
- No changes needed to existing data files
