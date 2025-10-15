# Soft Constraint Configuration Examples

## Example 1: Enable All Constraints with Equal Weight

```python
# config/constraints.py
SOFT_CONSTRAINTS_CONFIG = {
    "group_gaps_penalty": {"enabled": True, "weight": 1.0},
    "instructor_gaps_penalty": {"enabled": True, "weight": 1.0},
    "group_midday_break_violation": {"enabled": True, "weight": 1.0},
    "course_split_penalty": {"enabled": True, "weight": 1.0},
    "early_or_late_session_penalty": {"enabled": True, "weight": 1.0},
}
```

## Example 2: Prioritize Group Compactness Only

```python
SOFT_CONSTRAINTS_CONFIG = {
    "group_gaps_penalty": {"enabled": True, "weight": 10.0},  # High priority
    "instructor_gaps_penalty": {"enabled": False, "weight": 1.0},
    "group_midday_break_violation": {"enabled": False, "weight": 1.0},
    "course_split_penalty": {"enabled": False, "weight": 1.0},
    "early_or_late_session_penalty": {"enabled": False, "weight": 1.0},
}
```

## Example 3: Balance Multiple Objectives

```python
SOFT_CONSTRAINTS_CONFIG = {
    "group_gaps_penalty": {"enabled": True, "weight": 5.0},      # Very important
    "instructor_gaps_penalty": {"enabled": True, "weight": 3.0},  # Important
    "group_midday_break_violation": {"enabled": True, "weight": 2.0},  # Moderate
    "course_split_penalty": {"enabled": False, "weight": 1.0},   # Disabled
    "early_or_late_session_penalty": {"enabled": True, "weight": 1.0},  # Low priority
}
```

## Example 4: Disable All Soft Constraints (Hard Constraints Only)

```python
SOFT_CONSTRAINTS_CONFIG = {
    "group_gaps_penalty": {"enabled": False, "weight": 1.0},
    "instructor_gaps_penalty": {"enabled": False, "weight": 1.0},
    "group_midday_break_violation": {"enabled": False, "weight": 1.0},
    "course_split_penalty": {"enabled": False, "weight": 1.0},
    "early_or_late_session_penalty": {"enabled": False, "weight": 1.0},
}
```

## Tips for Weight Tuning

1. **Start with 1.0** for all enabled constraints
2. **Increase weights** (2x-10x) for critical requirements
3. **Compare runs** with different weights to find optimal balance
4. **Monitor plots** in `output/evaluation_*/soft/` to see impact
5. **Use powers of 2** (0.5, 1.0, 2.0, 4.0, 8.0) for easier comparison

## Workflow

1. Edit `config/constraints.py`
2. Run `python main.py`
3. Check `output/evaluation_*/soft/` plots
4. Adjust weights and re-run
5. No code changes needed!
