# BUGFIX: Population Generator Room Assignment Issue

**Issue**: Population generator (`find_suitable_rooms`) was assigning wrong room types when courses had no enrolled groups.

**Date**: October 17, 2025  
**Status**: ✅ FIXED

---

## Root Cause

**Two cascading issues** in `find_suitable_rooms()`:

### Issue 1: Overly High Default Capacity
```python
# OLD CODE:
max_group_size = 30  # default

# Problem: All practical rooms have capacity 24
# Result: ALL practical rooms filtered out!
```

When a course has **no enrolled groups** (data issue with ENAR 101), the code used a default `max_group_size = 30`. Since all practical rooms have capacity 24, they were ALL rejected by the capacity filter.

### Issue 2: Fallback Ignored Room Type
```python
# OLD CODE:
if not result:
    result = [r for r in context.rooms.values() if capacity >= max_group_size]
    # Returns ALL rooms, ignoring type!
```

When exact/flexible matches returned empty (due to Issue 1), the fallback returned ALL rooms with sufficient capacity, **completely ignoring room type requirements**.

**Result**: Practical courses got lecture rooms!

---

## Solution

### Fix 1: Smart Default Capacity

```python
# NEW CODE:
max_group_size = 0  # Start at 0
for group in context.groups.values():
    if course_id in getattr(group, "enrolled_courses", []):
        group_size = getattr(group, "student_count", 30)
        max_group_size = max(max_group_size, group_size)

# If no enrolled groups, use minimal default
if max_group_size == 0:
    max_group_size = 1  # Accept any room with capacity >= 1
```

**Rationale**: When no groups are enrolled, don't artificially filter out small rooms. Let room type matching be the primary filter.

### Fix 2: Type-Aware Fallback

```python
# NEW CODE:
if not result:
    fallback_exact = []
    fallback_any = []
    
    for r in context.rooms.values():
        if getattr(r, "capacity", 50) >= max_group_size:
            room_str = getattr(r, "room_features", "").lower().strip()
            # Match course_type even in fallback
            if (component_type == "practical" and "practical" in room_str) or \
               (component_type in ["theory", "lecture"] and "lecture" in room_str):
                fallback_exact.append(r)
            else:
                fallback_any.append(r)
    
    result = fallback_exact + fallback_any
```

**Rationale**: Even in fallback, prioritize rooms matching the course type.

---

## Impact

### Before Fix:
- ENAR 101 (practical, no enrolled groups) → 36 **lecture** rooms ✗
- Capacity filter eliminated all practical rooms (24 < 30)
- Fallback returned lecture rooms (capacity 48 > 30)

### After Fix:
- ENAR 101 (practical, no enrolled groups) → 35 **practical** rooms ✓
- Capacity filter accepts all rooms (24 >= 1)  
- Exact match finds all practical rooms
- Prioritization works correctly

---

## Test Results

```
Test 1: Theory course "ENSH 101"
  Required: lecture
  Found 37 suitable rooms
  First 3 rooms: ['A201(lecture)', 'A202(lecture)', 'A204(lecture)']
  ✓ PASS: Exact match prioritized

Test 2: Practical course "ENAR 101"
  Required: practical
  Found 35 suitable rooms
  Room type distribution: {'practical': 35}
  First 3 rooms: ['A101(practical)', 'A102(practical)', 'A103(practical)']
  ✓ PASS: Exact match prioritized
```

---

## Files Modified

1. `src/ga/population.py::find_suitable_rooms()` - Fixed capacity default and fallback logic
2. `test/test_population_rooms.py` - Validation test
3. `docs/BUGFIX_population_room_capacity.md` - This document

---

## Related Issues

- This was discovered while investigating the main room type mismatch stagnation issue
- The root cause there was data format mismatch (lists vs. strings)
- This is a separate but related issue affecting edge cases (courses with no groups)

---

## Key Takeaway

**Edge cases matter!** A reasonable default (30 students) became problematic when:
1. Course data had no enrolled groups
2. Room sizes were smaller than expected (24 vs. 30)

The fix ensures graceful degradation: when group data is missing, prioritize room type matching over capacity filtering.
