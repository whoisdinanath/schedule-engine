# Course Filtering by Group Enrollment

## Problem

The university Course.json contains **all courses** (392 courses) offered across all programs and semesters. However, for scheduling, we only need courses that are **actually enrolled** by groups in Groups.json (57 course codes = ~96 course objects after splitting theory/practical).

Previously, the system would:
- Load all 392 courses
- Show 296 irrelevant warnings about courses with no enrolled groups
- Show 214+ warnings about courses with no qualified instructors (for non-enrolled courses)

## Solution

**Filter courses during data loading** to only include those enrolled by at least one group.

### Implementation

**File**: `src/workflows/standard_run.py`

```
load_input_data():
  1. Load groups first
  2. Extract enrolled course codes
  3. Load ALL courses from database
  4. Filter: keep only courses where course.course_code is in enrolled set
  5. Link relationships with filtered courses
```

### Key Design Points

- **Course Code vs Course ID**: Groups reference course *codes* (e.g., "MATH101"), but our system creates course *objects* with IDs:
  - Theory: "MATH101" (if L+T > 0)
  - Practical: "MATH101-PR" (if P > 0)
  - Pure practical: Only "MATH101-PR" (if L=T=0, P>0)

- **Filtering Logic**: Match by `course.course_code` attribute, not `course_id`

- **Validation**: Updated to check group enrollments by course_code, with helpful error messages

## Results

**Before filtering:**
- Loaded: 392 courses
- Warnings: 296 unassigned + 214 no instructors = 510 warnings

**After filtering:**
- Loaded: 96 courses (from 57 enrolled course codes)
- Excluded: 296 courses (not enrolled by any group)
- Warnings: ~148 (only for enrolled courses with no qualified instructors)

## Data Quality Issues Found

The filtering exposed **legitimate data errors** where groups are enrolled in courses that don't exist:

| Course Code | Issue | Groups Affected |
|------------|-------|-----------------|
| ENCE 256 | L=T=P=0 (no hours defined) | BCE4A-F (6 groups) |
| ENIE 254 | L=T=P=0 (no hours defined) | BIE4A-B (2 groups) |

These must be fixed in Course.json or Groups.json.

## Files Modified

- `src/workflows/standard_run.py`: Added filtering logic in `load_input_data()`
- `src/encoder/input_encoder.py`: Removed redundant warning about unassigned courses
- `src/validation/input_validator.py`: Updated group-course validation to check by course_code with better error messages

## Usage

No changes needed - filtering happens automatically during data load. Validation will show clear errors for any data integrity issues.
