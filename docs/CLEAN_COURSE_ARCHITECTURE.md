# Clean Course Architecture - No Suffix Overhead

## Problem
Previously used `-PR` suffix or `_theory`/`_practical` suffixes in `course_id`, creating redundancy with the `course_type` attribute.

## Solution
**Use `course_type` attribute exclusively. No suffixes in `course_id`.**

### Architecture

**Course Object:**
- `course_id` = plain course code (e.g., `"ENME 103"`)
- `course_code` = same as course_id (e.g., `"ENME 103"`)  
- `course_type` = `"theory"` or `"practical"` ← **This does ALL the work**

**Dictionary Storage:**
- Keyed by `(course_code, course_type)` tuple
- Example keys: `("ENME 103", "theory")`, `("ENME 103", "practical")`

### Why Tuples?
Courses with same code but different types coexist:
```python
courses[("ENME 103", "theory")]     # Theory course
courses[("ENME 103", "practical")]  # Practical course

# Both have course_id = "ENME 103"
# Differentiated by course_type attribute
```

## Implementation

### `load_courses()`
```python
courses[(course_code, "theory")] = Course(
    course_id=course_code,  # No suffix!
    course_type="theory"
)

courses[(course_code, "practical")] = Course(
    course_id=course_code,  # Same ID!
    course_type="practical"
)
```

### Linking Functions
Direct tuple lookups:
```python
theory_key = (course_code, "theory")
practical_key = (course_code, "practical")

if theory_key in courses:
    # Link theory course
if practical_key in courses:
    # Link practical course
```

### Instructor Qualifications
Stored as tuples:
```python
instructor.qualified_courses = [
    ("ENME 103", "theory"),
    ("ENME 103", "practical")
]
```

## Benefits

1. **Zero Redundancy**: `course_type` is single source of truth
2. **Clean IDs**: `course_id` is just the course code
3. **Type Safety**: Tuple keys prevent accidental overwrites
4. **No String Manipulation**: No parsing suffixes
5. **Clear Intent**: `course.course_type == "practical"` vs parsing strings

## Migration Impact

### Changed Signatures
- `load_courses()` returns `Dict[tuple, Course]`
- `link_courses_and_groups()` accepts `Dict[tuple, Course]`
- `link_courses_and_instructors()` accepts `Dict[tuple, Course]`

### Accessing Courses
Old:
```python
theory_course = courses["ENME 103"]
practical_course = courses["ENME 103-PR"]
```

New:
```python
theory_course = courses[("ENME 103", "theory")]
practical_course = courses[("ENME 103", "practical")]

# Or iterate:
for (code, ctype), course in courses.items():
    if course.course_type == "practical":
        # Handle practical
```

### Gene Storage
`SessionGene.course_id` remains simple:
- Just stores `"ENME 103"`  
- Type determined by looking up course object and checking `course_type`

## Testing
Verify:
- Course creation works for L+T and P combinations
- Group linking finds both theory/practical
- Instructor linking matches coursetype correctly
- GA can access courses by tuple keys
