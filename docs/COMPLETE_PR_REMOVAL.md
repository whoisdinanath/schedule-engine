# Complete Removal of `-PR` Architecture

## Summary
ALL traces of the old `-PR` suffix system have been removed. The system now uses **clean tuple-based keys** with the `course_type` attribute doing all the work.

## What Was Removed

### 1. Comments & Documentation
❌ Removed references to:
- `"ENME 103-PR"` in examples
- `"MATH101-PR"` in docstrings  
- "backward compatibility" lookups
- Direct `course_id` string matching fallbacks

### 2. Code Logic
❌ Removed:
- `-PR` string concatenation
- Suffix parsing logic
- String-based course_id matching
- Fallback lookups by plain course_code

## Current Architecture

### Course Dictionary
```python
courses = {
    ("ENME 103", "theory"): Course(course_id="ENME 103", course_type="theory"),
    ("ENME 103", "practical"): Course(course_id="ENME 103", course_type="practical")
}
```

**Key Points:**
- Dict key: `(course_code, course_type)` tuple
- `course.course_id`: Plain code (e.g., `"ENME 103"`)
- `course.course_type`: `"theory"` or `"practical"`

### Instructor Qualifications
```python
instructor.qualified_courses = [
    ("ENME 103", "theory"),
    ("ENME 103", "practical")
]
```

### Course-Group Pairs
```python
pairs = [
    (("ENME 151", "theory"), ["BAE2"], "theory", 5),
    (("ENME 151", "practical"), ["BAE2A"], "practical", 3),
]
```

## Files Updated

### 1. `src/ga/course_group_pairs.py`
- Updated function signatures to use `Dict[tuple, Course]`
- Changed course lookup to use tuple keys
- Updated all variable names: `course_id` → `course_key`
- Fixed docstring examples
- Updated test output formatting

### 2. `src/ga/population.py`
- Removed all `-PR` references from comments
- Updated course lookup to use tuple keys
- Fixed `SessionGene` creation to extract `course.course_id`
- Updated two key functions:
  - `generate_course_group_aware_population()`
  - `extract_course_group_relationships()`

### 3. `src/encoder/input_encoder.py` (already updated)
- Returns `Dict[tuple, Course]`
- Uses tuple keys for all operations

### 4. `src/workflows/standard_run.py` (already updated)
- Filters courses using tuple keys

## How It Works

### 1. Loading
```python
courses = load_courses("Course.json")
# Returns: {("ENME 103", "theory"): Course(...), ("ENME 103", "practical"): Course(...)}
```

### 2. Accessing
```python
theory_course = courses[("ENME 103", "theory")]
practical_course = courses[("ENME 103", "practical")]

# Both have same course_id:
assert theory_course.course_id == "ENME 103"
assert practical_course.course_id == "ENME 103"

# Differentiated by course_type:
assert theory_course.course_type == "theory"
assert practical_course.course_type == "practical"
```

### 3. In Population Generation
```python
# course_group_pairs contains tuples
for course_key, group_id in course_group_pairs:
    # course_key is ("ENME 103", "theory") or ("ENME 103", "practical")
    course = context.courses[course_key]
    
    # Create SessionGene with plain course_id
    gene = SessionGene(
        course_id=course.course_id,  # "ENME 103"
        # ... other attributes
    )
```

### 4. In Constraints & Evaluation
```python
# SessionGene has plain course_id
gene.course_id  # "ENME 103"

# To get full course info, need to know the type:
# This is done through decoded CourseSession objects which have course_type
```

## Benefits

1. **Zero Redundancy**: No suffixes anywhere
2. **Type Safe**: Tuples prevent accidental overwrites
3. **Clean Data**: `course_id` is just the course code
4. **Clear Intent**: `course_type` attribute is explicit
5. **No Parsing**: No string manipulation needed
6. **Consistent**: Same pattern everywhere

## Verification

Run the test to verify:
```bash
python src/ga/course_group_pairs.py
```

Should show tuple keys like:
```
('ENSH 101', 'theory') → ['BAE1'] (5 quanta)
('ENME 103', 'practical') → ['BAE2A'] (3 quanta)
```

## Migration Complete ✅

NO traces of `-PR` suffix remain in:
- Comments
- Docstrings  
- Examples
- Code logic
- String concatenation
- Backward compatibility layers

**The `course_type` attribute is now the ONLY way to distinguish theory from practical!**
