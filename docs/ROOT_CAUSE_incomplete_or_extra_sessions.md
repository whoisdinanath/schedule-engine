# ROOT CAUSE: incomplete_or_extra_sessions Mismatch

**Date:** October 16, 2025  
**Status:** ✅ FIXED

## Problem

The `incomplete_or_extra_sessions` constraint was showing violations even though the population generator was creating the correct number of genes for all course-group pairs.

## Root Cause

**KEY MISMATCH: Course ID representation in sessions vs. course_map keys**

1. **Courses dictionary** uses **tuple keys**: `(course_code, course_type)` 
   - Example: `("ENME 151", "theory")`, `("ENME 151", "practical")`

2. **CourseSession.course_id** stores only **string** (course_code)
   - Example: `"ENME 151"`

3. **Constraint counting** used `(session.course_id, group_id)` as key
   - Result: `("ENME 151", "BAE2A")` ← string key

4. **Constraint checking** iterated over `course_map.items()` where keys are **tuples**
   - Result: `(("ENME 151", "theory"), "BAE2A")` ← tuple key

5. **Keys never matched!** All 392 combinations appeared to have 0 scheduled quanta.

## The Fix

Updated `incomplete_or_extra_sessions` constraint to:

1. **When counting:** Use `(course_code, course_type)` tuple from session:
   ```python
   course_code = session.course_id  # string
   course_type = session.course_type  # "theory" or "practical"
   key = ((course_code, course_type), group_id)  # matches course_map structure
   ```

2. **When checking:** Use course_key directly from course_map iteration:
   ```python
   for course_key, course in course_map.items():
       # course_key is already (course_code, course_type) tuple
       key = (course_key, group_id)
   ```

## Files Changed

1. `src/constraints/hard.py`
   - Fixed `incomplete_or_extra_sessions()` to properly construct keys using both course_code and course_type
   - Updated type hint: `course_map: Dict[tuple, Course]`

2. `src/core/types.py`
   - Fixed type annotation: `courses: Dict[tuple, Course]`

3. `src/ga/evaluator/fitness.py`
   - Fixed type hint: `courses: Dict[tuple, Course]`

4. `src/ga/evaluator/detailed_fitness.py`
   - Fixed type hint: `courses: Dict[tuple, Course]`

5. `src/decoder/individual_decoder.py`
   - Fixed type hint: `courses: Dict[tuple, Course]`

## Result

✅ **Hard constraint violations: 0** (from 392)  
✅ Population generator and constraint checker now aligned  
✅ All 392 course-group combinations properly recognized

## Key Insight

**When courses are keyed by tuples, ALL parts of the system must use the same key structure consistently.** The mismatch between string course_id in sessions and tuple keys in course_map caused the constraint to fail silently (all lookups returned 0).

## Prevention

- Keep type annotations accurate
- Document key structures clearly
- Use diagnostic scripts to verify alignment between generators and checkers
- Test constraints with small datasets to catch mismatches early
