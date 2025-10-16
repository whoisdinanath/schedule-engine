# Systematic Course Type Usage - Code Quality Improvement

## Problem

Previously, the codebase had **inconsistent practices** for determining course type:
- ❌ Some places checked `if course_id.endswith("-PR")` to determine if practical
- ❌ This was **name-based inference** rather than using the proper `course_type` attribute
- ❌ Violated the principle of using structured data attributes

## Solution

**Use `course.course_type` attribute everywhere** - never infer type from the course name/ID.

## Changes Made

### 1. **src/ga/population.py** (3 locations fixed)

#### Location 1: `generate_course_group_aware_population()` (line ~84)
**Before:**
```python
is_practical = course_id.endswith("-PR")
session_type = "practical" if is_practical else "theory"
```

**After:**
```python
# Get session type from Course object (not from name parsing)
session_type = course.course_type
```

#### Location 2: `create_course_component_sessions()` (line ~179)
**Before:**
```python
is_practical = course_id.endswith("-PR")
component_type = "practical" if is_practical else "theory"
```

**After:**
```python
# Get component type from Course object (not from name parsing)
component_type = course.course_type
```

#### Location 3: `create_course_component_sessions_with_conflict_avoidance()` (line ~235)
**Before:**
```python
is_practical = course_id.endswith("-PR")
component_type = "practical" if is_practical else "theory"
```

**After:**
```python
# Get component type from Course object (not from name parsing)
component_type = course.course_type
```

### 2. **src/ga/course_group_pairs.py** (complete refactor)

**Before:**
- Looped through course codes from group enrollments
- Manually constructed practical course ID with `course_id + "-PR"`
- Used L, T, P values to determine what to schedule

**After:**
- Finds ALL course objects matching the course_code
- Checks `course.course_type` to determine theory vs practical
- Uses `course.quanta_per_week` directly (already set correctly)

```python
for course_code in enrolled_courses:
    # Find all courses matching this course_code (theory and/or practical)
    matching_courses = [
        (cid, c) for cid, c in courses.items()
        if hasattr(c, 'course_code') and c.course_code == course_code
    ]
    
    for course_id, course in matching_courses:
        if course.course_type == "theory":
            # Handle theory scheduling
            ...
        elif course.course_type == "practical":
            # Handle practical scheduling
            ...
```

## Architecture Benefits

### Data Flow (Correct Pattern)
```
Course.json (raw data)
    ↓
load_courses() → sets course_type="theory" or "practical"
    ↓
Course entity → has course_type attribute
    ↓
Population generators → read course.course_type
    ↓
SessionGene → created with correct type
    ↓
CourseSession → inherits course.course_type
    ↓
Exporter → uses session.course_type for (TH)/(PR) tags
```

### Centralized Type Logic

**Single Source of Truth**: `src/encoder/input_encoder.py`
```python
# Theory course
if L + T > 0:
    course = Course(
        course_id=course_code,
        course_type="theory",  # ← Set once here
        ...
    )

# Practical course
if P > 0:
    course = Course(
        course_id=course_code + "-PR",
        course_type="practical",  # ← Set once here
        ...
    )
```

**Everywhere Else**: Just read `course.course_type`

## Verification Checklist

✅ No more `course_id.endswith("-PR")` checks  
✅ No more `if is_practical` based on name parsing  
✅ All type determination uses `course.course_type`  
✅ All component_type assignments use `course.course_type`  
✅ No syntax errors in modified files  
✅ Consistent with existing Course and CourseSession entities  

## Code Quality Improvements

1. **Type Safety**: Using structured attribute instead of string parsing
2. **Maintainability**: Change course ID convention without breaking logic
3. **Clarity**: Explicit `course.course_type` is self-documenting
4. **Single Source of Truth**: Type set once during load, read everywhere
5. **Robustness**: No risk of typos in suffix checks ("-PR" vs "-pr" vs "PR")

## Testing Notes

- Syntax validated with Pylance
- Logic unchanged - just using proper attribute
- No breaking changes to data format
- Compatible with existing Course.json structure

## Related Files (No Changes Needed)

These already use `course_type` correctly:
- `src/entities/course.py` - defines course_type attribute
- `src/entities/decoded_session.py` - has course_type field
- `src/decoder/individual_decoder.py` - propagates course.course_type
- `src/exporter/exporter.py` - uses session.course_type for tags
- `src/validation/input_validator.py` - validates using course.course_type
