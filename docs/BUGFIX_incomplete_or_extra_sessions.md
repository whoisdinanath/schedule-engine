# BUGFIX: incomplete_or_extra_sessions Stuck at 168 Violations

**Date:** October 15, 2025  
**Issue:** After fixing instructor qualification bugs, `incomplete_or_extra_sessions` became stuck at 168 violations.

## Root Cause

The instructor/group linking fixes correctly linked practical courses (ending in "-PR") to groups and instructors. This created **NEW (course, group) combinations** that needed to be scheduled:

- **Before fix:** Only theory courses linked to groups → ~224 combinations
- **After fix:** Theory AND practical courses linked → 392 combinations (+168!)

However, the population initializer (`extract_course_group_relationships`) was not updated to handle practical courses. It only looked for direct course_id matches in the courses dict, missing all the "-PR" variants.

## The Problem

```python
# OLD CODE in extract_course_group_relationships
for course_code in enrolled_courses:
    if course_id in context["courses"]:  # ❌ Only finds theory courses!
        course_group_pairs.append((course_id, group_id))
```

**What Happened:**
1. Groups have `enrolled_courses = ["ENSH 252"]` (course codes)
2. Courses dict has keys: `"ENSH 252"` (theory) AND `"ENSH 252-PR"` (practical)
3. Old code only checked if `"ENSH 252"` exists → found theory, missed practical
4. Initializer created 224 genes (theory only)
5. Constraint expected 392 combinations (theory + practical)
6. **Result: 168 missing combinations = 168 violations**

## The Fix

Updated `extract_course_group_relationships` in `src/ga/population.py` to find ALL courses with matching course_code (same pattern as the linking functions):

```python
def extract_course_group_relationships(context: Dict) -> List[Tuple[str, str]]:
    """
    Extract valid course-group enrollment pairs from the context.
    
    IMPORTANT: When a course has both theory and practical components
    (e.g., "ENSH 252" and "ENSH 252-PR"), we need to create genes for BOTH.
    """
    course_group_pairs = []

    for group_id, group in context["groups"].items():
        enrolled_courses = getattr(group, "enrolled_courses", [])

        for course_code in enrolled_courses:
            # Find ALL courses with this course_code (theory AND practical)
            matching_courses = [
                c for c in context["courses"].values()
                if hasattr(c, 'course_code') and c.course_code == course_code
            ]
            
            # If no match found by course_code, try direct lookup
            if not matching_courses and course_code in context["courses"]:
                matching_courses = [context["courses"][course_code]]
            
            # Add ALL matching courses to the pairs
            for course in matching_courses:
                course_group_pairs.append((course.course_id, group_id))

    return course_group_pairs
```

## Results

### Before Fix:
- Initializer created: **224 genes** (theory only)
- Constraint expected: **392 combinations** (theory + practical)
- Violations: **168** (stuck at every generation)

### After Fix:
- Initializer creates: **392 genes** (224 theory + 168 practical)
- Constraint expects: **392 combinations**
- Violations: **0** ✅

## Sample Output

```
=== Population Initialization Analysis ===
Total (course, group) pairs: 392
  Theory course pairs: 224
  Practical course pairs: 168

=== Sample Pairs ===
  1. (ENSH 151, BAE2A) - 5 quanta
  2. (ENSH 153, BAE2A) - 4 quanta
  3. (ENSH 153-PR, BAE2A) - 3 quanta    ← Practical course now included!
  4. (ENME 151, BAE2A) - 4 quanta
  5. (ENME 151-PR, BAE2A) - 1.5 quanta  ← Practical course now included!

=== Constraint Expectation ===
Total (course, group) combinations with enrollments: 392
Match: YES - Will have 0 violations!
```

## Important Notes

✅ **Your initializer is NOT broken** - it creates the EXACT number of sessions required  
✅ **No changes to mutation/crossover needed** - they already handle any course_id  
✅ **The fix maintains consistency** - same pattern used in all three locations:
   1. `link_courses_and_instructors`
   2. `link_courses_and_groups`
   3. `extract_course_group_relationships`

The root issue was the mismatch between:
- **Data model:** Groups store course_codes ("ENSH 252")
- **Runtime model:** Courses dict has course_ids ("ENSH 252" AND "ENSH 252-PR")

All three functions now correctly bridge this gap by finding ALL courses matching a course_code.
