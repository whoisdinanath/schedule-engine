# Session Block Clustering Soft Constraint

**Date:** October 19, 2025  
**Status:** ✅ Implemented

---

## Overview

A new soft constraint that encourages course sessions to be clustered into blocks of **2-3 consecutive quanta** rather than being fragmented into isolated single quanta or oversized blocks.

**Goal:** Better learning continuity by having sessions in meaningful blocks (e.g., 2-hour or 3-hour sessions) instead of scattered 1-hour sessions.

---

## Configuration

### Time Config (`config/time_config.py`)

```python
# Session Block Clustering Settings
PREFERRED_BLOCK_SIZE_MIN = 2  # Minimum preferred block size (quanta)
PREFERRED_BLOCK_SIZE_MAX = 3  # Maximum preferred block size (quanta)
ISOLATED_SESSION_PENALTY = 5  # Heavy penalty for isolated 1-quantum sessions
OVERSIZED_BLOCK_PENALTY_PER_QUANTUM = 1  # Penalty per quantum beyond max
```

### Constraint Config (`config/constraints.py`)

```python
SOFT_CONSTRAINTS_CONFIG = {
    "session_block_clustering_penalty": {"enabled": True, "weight": 1.0},
}
```

---

## Penalty Logic

### Block Size Penalties

| Block Size | Penalty | Example |
|------------|---------|---------|
| 1 quantum | `ISOLATED_SESSION_PENALTY` (5) | Isolated 1-hour session |
| 2 quanta | **0** (preferred) | 2-hour continuous session |
| 3 quanta | **0** (preferred) | 3-hour continuous session |
| 4+ quanta | `(size - 3) × OVERSIZED_BLOCK_PENALTY_PER_QUANTUM` | 4-hour → penalty 1 |

### Examples

#### ✅ **Good Clustering** (6 quanta course)

**Pattern [3, 3]:** Two 3-quantum blocks
```
Monday:    [10:00-13:00] ✓ (3 quanta)
Wednesday: [10:00-13:00] ✓ (3 quanta)
Penalty: 0
```

**Pattern [2, 2, 2]:** Three 2-quantum blocks
```
Monday:    [10:00-12:00] ✓ (2 quanta)
Wednesday: [10:00-12:00] ✓ (2 quanta)
Friday:    [10:00-12:00] ✓ (2 quanta)
Penalty: 0
```

#### ⚠️ **Acceptable** (5 quanta course)

**Pattern [3, 2]:**
```
Monday:    [10:00-13:00] ✓ (3 quanta)
Wednesday: [10:00-12:00] ✓ (2 quanta)
Penalty: 0
```

**Pattern [2, 2, 1]:**
```
Monday:    [10:00-12:00] ✓ (2 quanta)
Wednesday: [10:00-12:00] ✓ (2 quanta)
Friday:    [10:00-11:00] ✗ (1 quantum - isolated)
Penalty: 5
```

#### ❌ **Bad Clustering** (6 quanta course)

**Pattern [1, 1, 1, 1, 1, 1]:** Six isolated sessions
```
Monday:    [10:00-11:00] ✗ (1 quantum)
Monday:    [14:00-15:00] ✗ (1 quantum)
Wednesday: [10:00-11:00] ✗ (1 quantum)
Wednesday: [14:00-15:00] ✗ (1 quantum)
Friday:    [10:00-11:00] ✗ (1 quantum)
Friday:    [14:00-15:00] ✗ (1 quantum)
Penalty: 6 × 5 = 30 (very high!)
```

**Pattern [6]:** One oversized block
```
Monday: [10:00-16:00] ✗ (6 quanta - too long)
Penalty: (6 - 3) × 1 = 3
```

---

## Implementation Details

### How It Works

1. **Group by Course & Day**
   - Sessions are grouped by `(course_id, course_type, day)`
   - Example: `(CE707, practical, Monday)`

2. **Find Consecutive Blocks**
   - Within each day, sort quanta and identify consecutive runs
   - Example: `[2, 3, 4, 7, 8]` → blocks `[3, 2]` (sizes)

3. **Apply Penalties**
   - Block size 1: Heavy penalty (`ISOLATED_SESSION_PENALTY`)
   - Block size 2-3: No penalty (ideal)
   - Block size 4+: Light penalty for excess

4. **Aggregate**
   - Sum all penalties across all courses and days

### Function Signature

```python
def session_block_clustering_penalty(sessions: List[CourseSession]) -> int:
    """
    Penalizes course sessions fragmented into undesirable block sizes.
    
    Returns:
        Total penalty for non-preferred block sizes.
    """
```

---

## Tuning Guide

### Adjust Penalty Weights

**More aggressive against isolated sessions:**
```python
ISOLATED_SESSION_PENALTY = 10  # Was 5
```

**Allow larger blocks:**
```python
PREFERRED_BLOCK_SIZE_MAX = 4  # Was 3
```

**Stricter on oversized blocks:**
```python
OVERSIZED_BLOCK_PENALTY_PER_QUANTUM = 2  # Was 1
```

### Constraint Weight

**High priority (force clustering):**
```python
"session_block_clustering_penalty": {"enabled": True, "weight": 2.0}
```

**Low priority (gentle preference):**
```python
"session_block_clustering_penalty": {"enabled": True, "weight": 0.5}
```

---

## Why This Matters

### **Without Clustering:**
- Students get fragmented 1-hour sessions scattered throughout the week
- Difficult to maintain focus and continuity
- More context-switching overhead

### **With Clustering:**
- Sessions grouped into 2-3 hour blocks
- Better learning continuity (complete topics in one sitting)
- More efficient use of time (less setup/teardown)
- Natural break points between topics

---

## Testing Recommendations

1. **Check block distributions:**
   ```python
   # After GA run, analyze session patterns
   for session in best_schedule:
       print(f"{session.course_id}: {session.session_quanta}")
   ```

2. **Monitor penalty values:**
   - Check soft constraint scores
   - Compare before/after enabling this constraint

3. **Validate with stakeholders:**
   - Show example schedules
   - Confirm 2-3 hour blocks are acceptable

---

## Repair Heuristic

### **What It Does**

A companion repair heuristic actively improves session clustering by:
1. **Identifying** isolated 1-quantum sessions
2. **Attempting to merge** them with adjacent quanta to form 2-3 quantum blocks
3. **Avoiding conflicts** with other scheduled resources

### **How It Works**

**Strategy:**
1. Find all isolated 1-quantum sessions for each course
2. For each isolated session:
   - Try to expand by 1 quantum (before or after) to create 2-quantum block
   - Check if adjacent quantum is free (no group/instructor/room conflicts)
   - If free, merge into 2-quantum block
3. Track successful clustering improvements

**Example:**

Before repair:
```
Monday:    [10:00-11:00] ✗ Isolated 1-quantum
Wednesday: [14:00-15:00] ✗ Isolated 1-quantum  
Friday:    [10:00-11:00] ✗ Isolated 1-quantum
```

After repair (if 11:00-12:00 slots are free):
```
Monday:    [10:00-12:00] ✓ 2-quantum block
Wednesday: [14:00-16:00] ✓ 2-quantum block
Friday:    [10:00-12:00] ✓ 2-quantum block
```

### **Configuration**

**Repair Registry (`src/ga/operators/repair_registry.py`):**
```python
"repair_session_clustering": {
    "function": repair_session_clustering,
    "priority": 7,  # Runs after hard constraint repairs
    "description": "Improve session clustering",
    "modifies_length": False,
}
```

**GA Params (`config/ga_params.py`):**
```python
"repair_session_clustering": {
    "enabled": True,
    "priority": 7,
    "description": "Improve session block clustering",
}
```

### **When It Runs**

- **Priority 7** - After all hard constraint repairs (priorities 1-6)
- Before session count repairs (priority 8)
- Runs during mutation/crossover offspring repair
- Only if enabled in configuration

### **Limitations**

Current implementation:
- ✅ Can expand isolated sessions by 1 quantum (create 2-quantum blocks)
- ✅ Checks all resource conflicts (groups, instructors, rooms)
- ✅ Respects instructor availability
- ⚠️ Does not move sessions across days (future enhancement)
- ⚠️ Does not split large blocks (focuses on fixing isolated ones)

### **Statistics Tracking**

Tracked in `ga_scheduler.py`:
```python
generation_repair_stats = {
    "clustering_fixes": 0,  # Number of isolated sessions merged
    ...
}
```

Progress bar display:
```
Repairs: 15 fixes (cluster:5, group:3, room:2, ...)
                    ^^^^^^^^
                    Clustering improvements
```

---

## Files Modified

| File | Changes |
|------|---------|
| `src/constraints/soft.py` | Added `session_block_clustering_penalty()` soft constraint |
| `src/ga/operators/repair.py` | Added `repair_session_clustering()` repair heuristic |
| `src/ga/operators/repair_registry.py` | Registered new repair with priority 7 |
| `config/time_config.py` | Added clustering configuration parameters |
| `config/constraints.py` | Enabled clustering soft constraint |
| `config/ga_params.py` | Enabled clustering repair heuristic |
| `src/core/ga_scheduler.py` | Added clustering stats tracking and display |
| `docs/SESSION_BLOCK_CLUSTERING_CONSTRAINT.md` | This documentation |

---

## Related Constraints

| Constraint | Purpose | Interaction |
|------------|---------|-------------|
| `group_gaps_penalty` | Minimize idle time between sessions | Complementary - both encourage compactness |
| `instructor_gaps_penalty` | Minimize instructor idle time | Independent |
| `group_midday_break_violation` | Respect lunch breaks | Independent |

---

## Future Enhancements

1. **Per-Course Configuration**
   - Allow different block sizes for different course types
   - Example: Labs prefer 3 quanta, lectures prefer 2

2. **Day-Specific Preferences**
   - Different clustering rules for different days
   - Example: Fridays prefer smaller blocks

3. **Student Attention Spans**
   - Consider cognitive load limits
   - Maximum 3 quanta without break

---

## Summary

✅ **Implemented:** Session block clustering soft constraint  
✅ **Implemented:** Session clustering repair heuristic  
✅ **Configurable:** Min/max block sizes and penalties  
✅ **Integrated:** Registered in constraint and repair systems  
✅ **Tracked:** Statistics displayed in progress bar  
✅ **Documented:** Complete usage guide

The GA will now:
1. **Penalize** fragmented sessions via soft constraint
2. **Actively fix** isolated sessions via repair heuristic
3. **Prefer** schedules with 2-3 quantum session blocks!

### **End-to-End Workflow**

```
Mutation/Crossover
       ↓
Repair Heuristic (Priority 7)
  - Finds isolated 1-quantum sessions
  - Merges with adjacent free quantum
  - Creates 2-quantum blocks
       ↓
Fitness Evaluation
  - Soft constraint checks clustering
  - Penalizes remaining isolated sessions
       ↓
Selection
  - Favors individuals with better clustering
       ↓
Next Generation (improved clustering!)
```
