# BUGFIX: instructor_not_qualified Constraint Not Decreasing

**Date:** October 15, 2025  
**Issue:** Hard constraint `instructor_not_qualified` remained at constant high value across all GA generations, preventing evolution of better solutions.

## Root Cause Analysis

### Primary Bug: Empty List Iteration in `link_courses_and_instructors`

**Location:** `src/encoder/input_encoder.py` lines 337-343

**The Bug:**
```python
# Line 337: Clears the qualified courses list
for instructor in instructors.values():
    instructor.qualified_courses = []  # ❌ CLEARS THE LIST!

# Line 343: Tries to iterate over the ALREADY-CLEARED list  
for instructor_id, instructor in instructors.items():
    for course_code in instructor.qualified_courses[:]:  # ❌ EMPTY LIST!
        # Loop body NEVER EXECUTES!
```

**What Happened:**
1. Line 337 set `instructor.qualified_courses = []` (cleared it completely)
2. Line 343 tried to iterate over `instructor.qualified_courses[:]`
3. The `[:]` slice notation copied the **already-cleared** empty list
4. Loop never executed → **NO instructors were linked to ANY courses**
5. All courses ended up with `qualified_instructor_ids = []`
6. GA could never reduce "instructor_not_qualified" violations

**Impact:**
- 100% of instructor qualification data was lost
- All 392 courses had empty `qualified_instructor_ids` lists
- Constraint remained stuck at ~200 violations across all generations
- Mutations couldn't select qualified instructors (lists were empty)

### Secondary Bug: course_code Collision in Dictionary

**Location:** `src/encoder/input_encoder.py` line 332

**The Bug:**
```python
course_code_to_ids = {
    c.course_code: cid for cid, c in courses.items()
}
```

When a course has both theory and practical components:
- Theory: `course_id='ENSH 252'`, `course_code='ENSH 252'`
- Practical: `course_id='ENSH 252-PR'`, `course_code='ENSH 252'`

The dict can only hold ONE value per key, so:
- `'ENSH 252' -> 'ENSH 252-PR'` (practical wins, theory lost!)

**Impact:**
- Even if the primary bug was fixed, instructors would only link to practical OR theory, not both
- Approximately 50% of qualification links would be missing

### Tertiary Bug: Same Issue in `link_courses_and_groups`

**Location:** `src/encoder/input_encoder.py` lines 312-317

**The Bug:**
```python
for group_id, group in groups.items():
    for course_code in group.enrolled_courses:
        if course_code in courses:  # ❌ Only matches theory course directly
            if group_id not in courses[course_code].enrolled_group_ids:
                courses[course_code].enrolled_group_ids.append(group_id)
```

**Impact:**
- Practical courses (`ENSH 252-PR`) didn't get linked to groups
- Only theory courses had `enrolled_group_ids` populated
- 171 practical courses missing group enrollments

## The Fix

### Fix 1: Save Original Courses Before Clearing

```python
def link_courses_and_instructors(courses, instructors):
    # BUGFIX: Store original qualified courses BEFORE clearing
    instructor_original_courses = {}
    for instructor_id, instructor in instructors.items():
        instructor_original_courses[instructor_id] = instructor.qualified_courses[:]
        instructor.qualified_courses = []
    
    for course in courses.values():
        course.qualified_instructor_ids = []
    
    # BUGFIX: Use the SAVED original courses, not the cleared ones
    for instructor_id, instructor in instructors.items():
        for course_code in instructor_original_courses[instructor_id]:
            # Find ALL courses with this course_code (theory AND practical)
            matching_courses = [
                c for c in courses.values() 
                if hasattr(c, 'course_code') and c.course_code == course_code
            ]
            
            # Link instructor to ALL matching courses
            for course in matching_courses:
                if instructor_id not in course.qualified_instructor_ids:
                    course.qualified_instructor_ids.append(instructor_id)
                if course.course_id not in instructor.qualified_courses:
                    instructor.qualified_courses.append(course.course_id)
```

### Fix 2: Link Groups to Both Theory and Practical

```python
def link_courses_and_groups(courses, groups):
    for course in courses.values():
        course.enrolled_group_ids = []
    
    # BUGFIX: Link groups to ALL courses with matching course_code
    for group_id, group in groups.items():
        for course_code in group.enrolled_courses:
            # Find ALL courses with this course_code
            matching_courses = [
                c for c in courses.values() 
                if hasattr(c, 'course_code') and c.course_code == course_code
            ]
            
            # Link group to ALL matching courses
            for course in matching_courses:
                if group_id not in course.enrolled_group_ids:
                    course.enrolled_group_ids.append(group_id)
```

## Results After Fix

### Before Fix:
- Courses with qualified instructors: **0**
- Courses with enrolled groups: **54** (theory only)
- `instructor_not_qualified` violations: **~200** (stuck)
- Practical courses with groups: **0**

### After Fix:
- Courses with qualified instructors: **178** ✅
- Courses with enrolled groups: **96** (theory + practical) ✅
- Practical courses with instructors: **83** ✅
- Practical courses with groups: **42** ✅
- Total instructor-course qualifications: **477** ✅

### Constraint Verification:
```
Test 1: ENSH 151 with qualified instructor (I1)
  Violations: 0 ✅

Test 2: ENSH 151 with UNqualified instructor (I99)
  Violations: 1 ✅

Test 3: Course with no qualified instructors (ENSH 101)
  Violations: 1 ✅
```

## Expected Behavior Now

1. **Population Seeding:** Will correctly assign qualified instructors to courses that have them
2. **Mutation:** Will prefer qualified instructors (70% retention rate when qualified)
3. **Constraint Evaluation:** Correctly identifies violations
4. **GA Evolution:** Can now reduce `instructor_not_qualified` violations over generations

## Notes

- 214 courses legitimately have no qualified instructors in the data (expected)
- 296 courses have no enrolled groups (semester/department filtering)
- These courses will be assigned random instructors/groups during GA initialization
- The GA can still evolve to optimize these assignments based on other constraints
