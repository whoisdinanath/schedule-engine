# Constraint Evaluation Bug Fixes

## Issues Identified

### 1. Instructor Not Qualified (Stuck at ~100%)

**Root Cause**: Practical courses (`*-PR`) never matched to qualified instructors during linking phase.

**Problem Flow**:
- Instructors list qualified courses: `"ENSH 151"`
- System splits into theory (`ENSH 151`) + practical (`ENSH 151-PR`)
- Theory course sets `course_code = "ENSH 151"` ✓
- Practical course sets `course_code = "ENSH 151-PR"` ❌
- `link_courses_and_instructors` creates mapping: `course_code → course_id`
- Practical courses not in mapping → no instructor match
- Population seeding falls back to random instructors
- Result: 100% unqualified assignments for practicals

**Fix**: Practical courses now use base `course_code` (without `-PR`) for instructor matching while keeping unique `course_id`.

### 2. Room Type Mismatch (Starts ~0, rises to ~100)

**Root Cause**: Exact list equality instead of subset checking.

**Problem**:
```python
# Before (wrong)
if session.room.room_features != session.required_room_features:
    violations += 1
```

**Issues**:
- Required: `["mechanics of solids"]`
- Room has: `["mechanics of solids", "other features"]`
- Lists not equal → violation ❌
- Should pass: room HAS required feature ✓

Initial low violations due to lucky exact matches in seeding. Mutations broke these, causing violations to climb.

**Fix**: Use set subset comparison:
```python
required = set(session.required_room_features)
available = set(session.room.room_features)
if not required.issubset(available):
    violations += 1
```

## Impact

- **Instructor qualification**: Now properly tracks qualified assignments from start
- **Room matching**: Correctly validates feature requirements while allowing extra features
- **GA convergence**: Both constraints now properly guide evolution toward valid solutions
