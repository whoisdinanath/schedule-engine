# Repair Heuristics Registry System

## Overview

Configurable repair heuristics system following the registry pattern (similar to constraints). Allows enable/disable and priority control of individual repair functions via configuration.

## Architecture

### Registry Pattern
```
config/ga_params.py::REPAIR_HEURISTICS_CONFIG
    ↓
src/ga/operators/repair_registry.py
    ↓ (loads enabled repairs)
src/ga/operators/repair.py::repair_individual()
    ↓ (applies in priority order)
Individual repairs
```

## Key Components

### 1. Configuration (`config/ga_params.py`)
```python
REPAIR_HEURISTICS_CONFIG = {
    "enabled": True,              # Master switch
    "max_iterations": 3,          # Global iteration limit
    "apply_after_mutation": True,
    "apply_after_crossover": False,
    
    "heuristics": {
        "repair_availability_violations": {
            "enabled": True,
            "priority": 1,
        },
        # ... more repairs
    }
}
```

### 2. Registry (`src/ga/operators/repair_registry.py`)
- `get_all_repair_heuristics()`: Returns all available repairs
- `get_enabled_repair_heuristics()`: Returns only enabled repairs (sorted by priority)
- `get_repair_statistics_template()`: Returns stats template for tracking

### 3. Orchestrator (`src/ga/operators/repair.py`)
- `repair_individual()`: Dynamically applies enabled repairs from registry

## Usage

### View Current Configuration
```bash
python scripts/show_repair_config.py
```

### Enable/Disable Individual Repairs
```python
# config/ga_params.py
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_room_conflicts"]["enabled"] = False
```

### Change Priority Order
```python
# Execute group overlaps before availability
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_group_overlaps"]["priority"] = 1
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_availability_violations"]["priority"] = 2
```

### Disable All Repairs
```python
REPAIR_HEURISTICS_CONFIG["enabled"] = False
```

## Available Repair Heuristics

| Priority | Heuristic                              | Modifies Length | Description                          |
|----------|----------------------------------------|-----------------|--------------------------------------|
| 1        | repair_availability_violations         | No              | Fix availability violations          |
| 2        | repair_group_overlaps                  | No              | Fix group schedule overlaps          |
| 3        | repair_room_conflicts                  | No              | Fix room double-bookings             |
| 4        | repair_instructor_conflicts            | No              | Fix instructor double-bookings       |
| 5        | repair_instructor_qualifications       | No              | Reassign unqualified instructors     |
| 6        | repair_room_type_mismatches            | No              | Fix room type mismatches             |
| 7        | repair_incomplete_or_extra_sessions    | ⚠️ YES          | Add/remove sessions (changes length) |

## Experimental Use Cases

### 1. Ablation Study
Test impact of each repair individually:
```python
# Disable all except one to test its isolated effect
for name in REPAIR_HEURISTICS_CONFIG["heuristics"]:
    REPAIR_HEURISTICS_CONFIG["heuristics"][name]["enabled"] = False
    
# Enable only the repair being tested
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_group_overlaps"]["enabled"] = True
```

### 2. Performance Tuning
Disable expensive repairs for faster experimentation:
```python
# Disable the most expensive repair (session count adjustment)
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_incomplete_or_extra_sessions"]["enabled"] = False
```

### 3. Priority Optimization
Test different repair orders to find optimal sequence:
```python
# Test hypothesis: room repairs before group repairs
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_room_conflicts"]["priority"] = 1
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_group_overlaps"]["priority"] = 2
```

### 4. Debugging Specific Constraint
Isolate constraint violations by disabling their repairs:
```python
# Disable availability repair to see raw violations
REPAIR_HEURISTICS_CONFIG["heuristics"]["repair_availability_violations"]["enabled"] = False
```

## Statistics Tracking

`repair_individual()` returns detailed statistics:
```python
{
    "iterations": 2,
    "availability_violations_fixes": 45,
    "group_overlaps_fixes": 12,
    "room_conflicts_fixes": 8,
    "instructor_conflicts_fixes": 5,
    "instructor_qualifications_fixes": 0,
    "room_type_mismatches_fixes": 3,
    "incomplete_or_extra_sessions_fixes": 0,
    "total_fixes": 73
}
```

## Implementation Benefits

1. **Research**: Easy ablation studies and comparative analysis
2. **Performance**: Disable expensive repairs when not needed
3. **Debugging**: Isolate specific violations for analysis
4. **Experimentation**: Test different repair strategies without code changes
5. **Maintainability**: Centralized configuration, clean separation of concerns

## Design Philosophy

Follows schedule-engine patterns:
- ✅ Configuration over code
- ✅ Registry pattern (like constraints)
- ✅ Separation of concerns
- ✅ Extensible and testable
- ✅ Concise documentation

## Future Extensions

Potential enhancements:
- Per-repair iteration limits
- Adaptive priority based on violation counts
- Repair-specific parameters (e.g., search depth)
- Statistical reporting per repair
- Conditional repairs based on thresholds
