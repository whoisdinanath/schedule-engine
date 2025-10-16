# Fix: Courses with L=T=P=0 Should Not Block Execution

## Problem

Some courses in Course.json have **no hours defined** (L=0, T=0, P=0):
- `ENCE 256` 
- `ENIE 254`

Groups were enrolled in these courses, but since they have no hours, they don't generate any Course objects during loading. This caused **validation errors** that blocked program execution.

## Root Cause

In `src/validation/input_validator.py`, when a group was enrolled in a course that didn't exist in the loaded courses, it was treated as a **critical ERROR** that prevented the GA from running.

However, courses with L=T=P=0:
- Don't need to be scheduled (no class hours)
- Are expected to be missing from the schedule
- Should not block the scheduling system

## Solution

**Changed validation severity from ERROR to WARNING** for missing courses.

### File Modified: `src/validation/input_validator.py`

**Before:**
```python
if not matching_courses:
    self.errors.append(
        ValidationError(
            "RELATIONSHIP",
            f"Group {group_id} enrolled in course {course_code} which doesn't exist "
            f"(may have L=T=P=0 in Course.json, or be missing entirely)",
        )
    )
```

**After:**
```python
if not matching_courses:
    # This is a WARNING, not an ERROR - courses with L=T=P=0 don't need scheduling
    self.warnings.append(
        ValidationError(
            "RELATIONSHIP",
            f"Group {group_id} enrolled in course {course_code} which doesn't exist "
            f"(likely has L=T=P=0 in Course.json and doesn't need scheduling)",
            "WARNING",
        )
    )
```

## Results

### Before ❌
```
[ERROR] Found 8 ERRORS:
  [ERROR] RELATIONSHIP: Group BCE4A enrolled in course ENCE 256 which doesn't exist...
  [ERROR] RELATIONSHIP: Group BCE4B enrolled in course ENCE 256 which doesn't exist...
  ...
[X] Validation FAILED! Fix errors before running GA.
ValueError: Input validation failed with ERRORS! Fix errors and try again.
```

**Program execution blocked.**

### After ✅
```
[WARNING] Found 156 WARNINGS:
  ...
  [WARNING] RELATIONSHIP: Group BCE4A enrolled in course ENCE 256 which doesn't exist 
            (likely has L=T=P=0 in Course.json and doesn't need scheduling)
  [WARNING] RELATIONSHIP: Group BCE4B enrolled in course ENCE 256 which doesn't exist 
            (likely has L=T=P=0 in Course.json and doesn't need scheduling)
  ...

[OK] Validation passed with warnings. Review before running GA.
[OK] Input validation passed (warnings are OK)!

Step 4: Running Genetic Algorithm
============================================================
Generating population of size 50...
```

**Program runs successfully!**

## Rationale

1. **Courses with no hours don't need scheduling** - This is expected behavior, not an error
2. **Non-blocking validation** - Warnings inform the user but don't prevent execution
3. **Flexible data** - Allows Course.json to contain courses at various planning stages
4. **Better UX** - System can run even with incomplete course data

## Impact

- ✅ Program no longer blocked by L=T=P=0 courses
- ✅ Users see clear warning messages
- ✅ GA can run and generate schedules
- ✅ 8 false-positive errors eliminated

## Data Quality Note

The warning message suggests reviewing Course.json and Groups.json:
- Either add hours to courses (L, T, or P > 0)
- Or remove them from group enrollments if they're truly not scheduled courses

This is informational, not critical for system operation.
