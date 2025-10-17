# BUGFIX: Room Type Mismatch Stagnation

**Issue**: Room type mismatch violations stuck at ~150-167, not improving despite repair heuristics running.

**Date**: October 17, 2025

---

## Root Cause

**Data Type Mismatch** between constraint checking and repair logic:

### The Problem

1. **JSON Data Structure**:
   - `Rooms.json` has `"type": "Practical"` or `"Lecture"` AND `"features": [...]`
   - `Course.json` courses need generic types (lecture/practical)

2. **Encoder Bug** (`input_encoder.py`):
   - ❌ Used `room_features = [list of specific features]` (e.g., `["Fluid Engineering", "Water Supply"]`)
   - ❌ Used `required_room_features = ["lecture room"]` or `["lab"]` as lists
   - **Result**: Incompatible data types (specific features vs. generic types)

3. **Constraint Check** (`hard.py::room_type_mismatch`):
   - Converted to sets and checked: `required_features.issubset(room_features)`
   - `{"lecture room"}.issubset({"Fluid Engineering", "Water Supply"})` = **FALSE**
   - **Result**: Almost ALL sessions flagged as violations

4. **Repair Logic** (`repair.py`):
   - Tried string equality: `room_type == "lab"`
   - But rooms had arrays: `["Fluid Engineering"]`
   - **Result**: NO rooms matched, repairs failed

---

## Solution

**Normalize to Simple Strings** using the `"type"` field:

### Changes Made

#### 1. `src/encoder/input_encoder.py`

**`load_rooms()`**:
```python
# Before:
room_features = [f.strip().lower() for f in item.get("features", [])]

# After:
room_type = item.get("type", "Lecture").strip().lower()  # "practical" or "lecture"
```

**`load_courses()`**:
```python
# Before:
required_room_features=["lecture room"]  # Theory
required_room_features=practical_features or ["lab"]  # Practical

# After:
required_room_features="lecture"  # Theory (simple string)
required_room_features="practical"  # Practical (simple string)
```

#### 2. `src/constraints/hard.py`

**Rewrote `room_type_mismatch()`**:
- Uses simple string matching with flexible compatibility rules
- Exact match: `"lecture" == "lecture"`
- Flexible: `"lecture"` accepts `["lecture", "classroom", "auditorium"]`
- Flexible: `"practical"` accepts `["practical", "lab", "laboratory"]`

**Added `_room_type_matches()` helper**:
- Handles compatibility mapping
- Consistent with repair logic in `repair.py`

---

## Impact

### Before Fix:
- Violations: ~160-167 (stuck)
- Repair fixes: Thousands reported, but violations unchanged
- **Reason**: Repair couldn't find matching rooms due to data type mismatch

### After Fix:
- Data types consistent: strings throughout
- Constraint check and repair use same logic
- Flexible matching allows compatible room types
- **Expected**: Violations should decrease with each generation

---

## Testing

```python
# Verify data loading
rooms = load_rooms('data/Rooms.json', qts)
# A101: type='practical', A201: type='lecture' ✓

courses = load_courses('data/Course.json')
# ('ENSH 101', 'theory'): required='lecture' ✓
# ('ENAR 101', 'practical'): required='practical' ✓

# Test constraint logic
_room_type_matches('lecture', 'lecture')      # True ✓
_room_type_matches('lecture', 'auditorium')   # True (flexible) ✓
_room_type_matches('practical', 'lecture')    # False ✓
```

---

## Related Files

- `src/encoder/input_encoder.py`: Data loading fix
- `src/constraints/hard.py`: Constraint logic rewrite
- `src/ga/operators/repair.py`: Already had correct logic (string matching)
- `src/ga/population.py`: Already had correct logic (updated earlier)

---

## Notes

- The `"features"` array in rooms (specific capabilities like "Fluid Engineering") is NOT used for general room type matching
- Future enhancement: Could use `"features"` for course-specific requirements (e.g., "needs computer graphics lab")
- Current fix prioritizes correct type matching over feature-specific matching
