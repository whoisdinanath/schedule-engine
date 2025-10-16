# COMPLETE FIX: room_type_mismatch Constraint Issues

## Problems Found and Fixed

### Problem 1: Wrong Attribute Name for Room Features ✅ FIXED
**Location**: `src/ga/operators/mutation.py:140` and `src/ga/population.py:609`

**Bug**: Code looked for `getattr(room, "features", [])` but Room objects have `room_features`
**Result**: Always returned empty list, mutation thought all rooms had no features

**Fix**: Changed to `getattr(room, "room_features", [])`

### Problem 2: Wrong Attribute Name for Course Requirements ✅ FIXED
**Location**: `src/ga/operators/mutation.py:131` and `src/ga/population.py:597`

**Bug**: Code looked for `getattr(course, "PracticalRoomFeatures", "")` but Course objects have `required_room_features`
**Result**: Always returned empty string, mutation thought courses had no requirements

**Fix**: Changed to `getattr(course, "required_room_features", [])`

### Problem 3: Wrong Matching Logic (Exact vs Substring) ✅ FIXED
**Location**: `src/ga/operators/mutation.py` and `src/ga/population.py` feature matching logic

**Bug**: Used exact set matching (`required_set.issubset(room_set)`)
- Course needs: `["computer"]`
- Room has: `["computer graphics", "computer network"]`
- Exact match fails because `"computer"` ≠ `"computer graphics"`

**Reality**: Room features are granular (e.g., "computer graphics"), course needs are general (e.g., "computer")

**Fix**: Implemented substring matching
```python
# Check if each required feature is substring of any room feature
all_matched = True
for req in req_list:
    req_lower = req.lower().strip()
    # Check if this requirement appears in ANY room feature
    matched = any(req_lower in room_feat.lower() for room_feat in room_list)
    if not matched:
        all_matched = False
        break
```

## Test Results

### Before All Fixes
- `"computer"` course → 0 matching rooms
- `"design studio"` course → 0 matching rooms (wrong attribute)
- Mutation was completely blind to room capabilities

### After All Fixes
- `"computer"` course → 4 matching rooms ✅
  - B304, D101, D104, D106
- `"design studio"` course → 4 matching rooms ✅
  - A202x, A203, A301x, etc.
- `"drawing"` course → 4 matching rooms ✅
  - A301x, A305, D111, etc.

## Files Modified

1. **`src/ga/operators/mutation.py`**
   - Line 131: `PracticalRoomFeatures` → `required_room_features`
   - Line 140: `"features"` → `"room_features"`
   - Lines 148-157: Exact set matching → Substring matching

2. **`src/ga/population.py`**
   - Line 597: `PracticalRoomFeatures` → `required_room_features`
   - Line 609: `"features"` → `"room_features"`
   - Lines 613-632: Exact set matching → Substring matching

## Expected Behavior After Fix

### Population Initialization
- Will intelligently assign rooms based on course requirements
- Theory courses can use any room
- Practical courses get rooms with matching features (using substring match)

### Mutation
- Can now see actual room features
- Intelligently selects rooms where requirements match (substring)
- Falls back to all rooms only when truly no match exists

### GA Evolution
- `room_type_mismatch` constraint should steadily DECREASE
- Violations that CAN be fixed (112/171 courses have matching rooms) will improve
- Some violations may persist if:
  - Course needs feature that exists in no room
  - Capacity constraints conflict with feature requirements
  - But these are genuine data limitations, not bugs!

## Why Three Bugs Existed

1. **Silent Failures**: `getattr(..., default)` returns default without error
2. **Similar Names**: `features` vs `room_features`, `PracticalRoomFeatures` vs `required_room_features`
3. **Data Granularity Mismatch**: Courses need "computer", rooms have "computer graphics"
4. **No Type Checking**: Python doesn't enforce attribute names at compile time

## Testing Recommendation

Run with only `room_type_mismatch` enabled:
```python
# config/constraints.py
HARD_CONSTRAINTS_CONFIG = {
    "room_type_mismatch": {"enabled": True, "weight": 1.0},
    # ... others disabled
}
```

Should see violations decrease from ~170 to ~59 (the 59 courses that truly have no matching room).
