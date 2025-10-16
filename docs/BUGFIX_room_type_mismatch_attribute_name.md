# BUG FIX: room_type_mismatch Constraint - Attribute Name Mismatch

## Issue Fixed
`room_type_mismatch` hard constraint was stuck at 167 violations due to mutation code looking for wrong attribute name.

## Root Cause
- Room objects have attribute: `room_features` (list of features)
- Mutation and population code looked for: `"features"` (doesn't exist!)
- Result: `getattr(room, "features", [])` always returned empty list `[]`
- Mutation thought ALL rooms had NO features → couldn't intelligently select rooms

## Changes Made

### File 1: `src/ga/operators/mutation.py:140`

**Before**:
```python
room_features = getattr(room, "features", [])
```

**After**:
```python
room_features = getattr(room, "room_features", [])
```

### File 2: `src/ga/population.py:609`

**Before**:
```python
room_features = getattr(room, "features", [])
```

**After**:
```python
room_features = getattr(room, "room_features", [])
```

## Verification

**Before fix**:
- `getattr(room, "features", [])` → returns `[]` (empty)
- Length: 0
- Mutation: blind to room capabilities

**After fix**:
- `getattr(room, "room_features", [])` → returns actual features
- Example: `['mechanics of solids', 'mechanics of machines and mechanisms']`
- Length: 2
- Mutation: can see and select suitable rooms

## Expected Impact

### Before Fix
- 168 initial violations
- 167 after gen 1 (one lucky random match)
- STUCK at 167 forever (mutation blind)

### After Fix
- Mutation can now intelligently select rooms with matching features
- Should see steady decrease in violations
- Will still have some violations if:
  - Some courses need features that don't exist in any room
  - Room capacity constraints conflict with feature requirements
  
But GA can now **actively optimize** room assignments instead of random guessing!

## Related Issue
The `instructor_not_qualified` constraint has similar issue but with data completeness:
- 214 courses have NO qualified instructors in the data
- See: `docs/DIAGNOSIS_instructor_qualification_not_improving.md`
- Needs data fix OR temporary constraint disable

## Testing
Run main.py with only `room_type_mismatch` enabled to verify improvement over generations.
