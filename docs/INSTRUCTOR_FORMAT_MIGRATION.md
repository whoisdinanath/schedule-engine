# Instructor Format Migration

## Problem
Instructors.json format changed from simple course codes to structured objects with explicit course types:

**Old Format:**
```json
{
    "courses": ["ENSH 151", "ENSH 252", "ENSH 252-PR"]
}
```

**New Format:**
```json
{
    "courses": [
        {"coursecode": "ENSH 151", "coursetype": "Theory"},
        {"coursecode": "ENSH 252", "coursetype": "Theory"},
        {"coursecode": "ENSH 252", "coursetype": "Practical"}
    ]
}
```

Old format appended "-PR" suffix for practical courses; new format uses explicit `coursetype` field.

## Solution
Modified `src/encoder/input_encoder.py` to:
1. Parse both formats (backward compatible)
2. Link instructors to specific course types (Theory/Practical)

## Changes

### `load_instructors()`
- Parse `courses` as list of dicts with `coursecode`/`coursetype`
- Fallback to old format if string detected (auto-converts "-PR" suffix)
- Store structured qualification data for linking phase

### `link_courses_and_instructors()`
- Match instructors to courses by both `course_code` AND `course_type`
- Separate Theory/Practical linking (instructor qualifies for specific type)
- Convert structured qualifications to internal course IDs (list of strings)

## Validation
Existing validation in `src/validation/input_validator.py` works unchanged—operates on course IDs after linking.

## Testing
Test script: `test/test_instructor_format.py`
- Verifies new format parsing
- Confirms Theory/Practical separation
- Validates bidirectional linking

**Result:** Instructor I2 correctly linked to both "ENSH 252" (Theory) and "ENSH 252-PR" (Practical) based on coursetype specification.

## Impact
- **Entities:** No changes—`Instructor.qualified_courses` remains `List[str]` of course IDs
- **GA operators:** No changes—work with course IDs
- **Constraints:** No changes—use course IDs
- **Backward compatible:** Old format still supported

## Key Points
- New format enables precise instructor-to-course-type mapping
- Eliminates ambiguity (instructor can teach theory but not practical, or vice versa)
- Internal system unchanged—format difference isolated to loader/linker
