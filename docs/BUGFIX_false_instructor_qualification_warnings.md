# BUGFIX: False Warnings for Instructor Qualifications

## Problem
Instructors I23, I28, I30, I36, I38, I41, I42, I43, I45, I47, I48, I50, I51, I52, I53, I55 triggered warnings:
```
[WARNING] INSTRUCTOR: Instructor I23 has no qualified courses
```

Despite having qualified courses in `Instructors.json`.

## Root Cause
**Execution Order Issue**: Course filtering happens before instructor linking.

### Workflow
1. Load all courses from `Course.json` (392 courses)
2. Filter to only enrolled courses (96 courses remain)
3. **Link instructors to filtered courses** ← Problem occurs here
4. Validate instructors

### What Happened
- Instructors qualified for courses NOT enrolled by any group (e.g., `ENCT 411`, `ENCT 201`)
- These courses filtered out in Step 2 (not in enrolled set)
- Step 3 linking finds NO matching courses for these instructors
- `instructor.qualified_courses` becomes empty list
- Validation sees empty list and warns (false positive)

### Example
Instructor I23 qualified for `ENCT 411` (Theory + Practical):
- JSON: Correct qualification exists
- Enrollment: No group enrolled in `ENCT 411`
- Filter: `ENCT 411` removed from courses dict
- Link: No match found → `qualified_courses = []`
- Validation: Empty list → warning triggered

## Solution
**Preserve Original Qualifications**: Distinguish between:
1. **JSON data issue**: Instructor has NO courses in JSON → **WARN**
2. **Enrollment mismatch**: Instructor qualified for non-enrolled courses → **SILENT**

### Changes

#### `src/encoder/input_encoder.py`
```python
# Store original qualifications before linking
instructor.original_qualified_courses = instructor.qualified_courses[:]
```
Preserves raw JSON data for validation.

#### `src/validation/input_validator.py`
```python
# Check original JSON data, not filtered result
original_courses = getattr(instructor, 'original_qualified_courses', None)

if not original_courses:
    # Truly empty in JSON - warn
    self.warnings.append(...)
elif not instructor.qualified_courses:
    # Has qualifications but none match enrolled courses - silent
    pass
```

## Verification
Created test `test/test_instructor_qualification_validation.py` covering:
- Empty JSON qualifications → triggers warning ✓
- Unmatched qualifications → no warning ✓  
- Matched qualifications → links correctly ✓

## Impact
- **False positives eliminated**: 16 spurious warnings removed
- **Real issues still caught**: Empty JSON qualifications still warned
- **Informational clarity**: Validation reflects actual data issues, not workflow artifacts

## Related
- See `docs/BUGFIX_instructor_not_qualified.md` for instructor qualification constraint issues
- Enrollment filtering logic in `src/workflows/standard_run.py` lines 250-270
