# DIAGNOSIS: room_type_mismatch Hard Constraint Not Decreasing

## Problem
`room_type_mismatch` hard constraint:
- Started at 168 violations
- Decreased to 167 after 1 generation
- **STUCK at 167** for 100+ generations
- Cannot improve further

## Root Cause: **ATTRIBUTE NAME MISMATCH BUG**

### The Bug

**Room Entity** uses: `room_features` (correct attribute name)
**Constraint Code** uses: `"features"` (WRONG - attribute doesn't exist!)
**Mutation Code** also uses: `"features"` (WRONG!)

### Location 1: Constraint Evaluation

**File**: `src/constraints/hard.py:70-94`

```python
def room_type_mismatch(sessions: List[CourseSession]) -> int:
    violations = 0
    for session in sessions:
        # BUG: Uses wrong attribute name "features"
        room_features = (
            set(session.room.room_features)  # ← This is CORRECT
            if isinstance(session.room.room_features, list)
            else {session.room.room_features}
        )
        # ... constraint check
```

**Wait, this looks correct!** Let me check CourseSession...

### Location 2: Mutation Code

**File**: `src/ga/operators/mutation.py:142-145`

```python
room_features = getattr(room, "features", [])  # ← BUG: should be "room_features"
```

**File**: `src/ga/population.py:612-616`

```python
room_features = getattr(room, "features", [])  # ← BUG: should be "room_features"
```

### What Happens

1. **Initial Population**: Rooms assigned randomly
   - 168 genes get rooms that don't match requirements
   - Constraint detects violations correctly (using `session.room.room_features`)

2. **Mutation Tries to Fix**:
   ```python
   room_features = getattr(room, "features", [])  # Returns [] (default)
   # Since room_features is ALWAYS empty [], mutation thinks NO room has features
   # Falls back to: list(context["rooms"].keys()) 
   # Assigns random room again → still violates!
   ```

3. **Why It Decreased by 1**:
   - One lucky mutation assigned a room that happened to match by chance
   - But mutation cannot intelligently select suitable rooms
   - Because it thinks ALL rooms have empty features!

4. **Why It's Stuck**:
   - Mutation logic believes no room has ANY features
   - Cannot distinguish between suitable and unsuitable rooms
   - Random selection keeps assigning wrong rooms
   - 167 violations remain FOREVER

## Data Reality Check

From actual data:
- **Total rooms**: 72
- **Rooms with features in JSON**: 72 (ALL have features!)
- **Rooms with features as seen by mutation**: 0 (NONE - due to wrong attribute!)

Example from `Rooms.json`:
```json
{
    "room_id": "A101",
    "features": ["Mechanics of Solids", "Mechanics of Machines and Mechanisms"]
}
```

Loaded as Room object:
```python
room.room_features = ["mechanics of solids", "mechanics of machines and mechanisms"]
room.features = AttributeError!  # This attribute doesn't exist
```

Mutation code:
```python
getattr(room, "features", [])  # Returns [] because attribute doesn't exist!
```

## Impact Analysis

### Why 168 Initial Violations?

- 171 practical courses exist
- Each needs specific room features
- Random assignment → most get wrong rooms
- 168 practical course genes get unsuitable rooms

### Why Only 1 Improvement?

- One mutation randomly picked a matching room (pure luck)
- Other 167 violations cannot be fixed
- Mutation thinks all rooms are identical (empty features)

### Constraint Evaluation vs Mutation

| Component | Attribute Used | Result |
|-----------|---------------|--------|
| Constraint evaluation | `session.room.room_features` ✅ | Works correctly, counts violations |
| Mutation (intelligent selection) | `getattr(room, "features", [])` ❌ | Always returns `[]`, thinks no rooms have features |
| Population initialization | Same bug ❌ | Cannot do intelligent room assignment |

## The Trap Mechanism

```
Course needs "computer" lab
    ↓
Mutation tries to find suitable room:
    1. Checks: getattr(room, "features", [])
    2. Gets: [] for EVERY room (attribute doesn't exist)
    3. Concludes: No rooms have features
    4. Falls back: random.choice(all_rooms)
    5. Assigns: Wrong room
    ↓
Evaluation: +1 violation (correctly detects mismatch)
    ↓
Selection: Individual survives
    ↓
Next mutation: SAME BUG, SAME RESULT
    ↓
LOOP FOREVER - stuck at 167 violations
```

## Solution

Fix the attribute name in TWO locations:

### Fix 1: Mutation operator

**File**: `src/ga/operators/mutation.py:142`

**Before**:
```python
room_features = getattr(room, "features", [])
```

**After**:
```python
room_features = getattr(room, "room_features", [])
```

### Fix 2: Population initialization

**File**: `src/ga/population.py:612`

**Before**:
```python
room_features = getattr(room, "features", [])
```

**After**:
```python
room_features = getattr(room, "room_features", [])
```

### Expected Result After Fix

- Mutation will see actual room features
- Can intelligently select matching rooms
- 167 violations should decrease steadily
- Eventually reach 0 (or very low if some mismatches are unavoidable)

## Why This Bug Wasn't Caught Earlier

1. **Silent failure**: `getattr(room, "features", [])` returns default `[]` without error
2. **Fallback masks issue**: Code falls back to random selection
3. **Partial functionality**: Constraint evaluation works (uses correct attribute)
4. **Small improvement**: 1 violation fixed by chance, looks like GA is "working"
