# BUGFIX: Practical Courses Not Being Scheduled

## Problem
Practical courses (with `-PR` suffix) were not appearing in generated schedules despite being correctly created by the loader.

## Root Cause
The population generator in `src/ga/population.py` only created session genes for courses explicitly listed in each group's `enrolled_courses` field. Since groups list base course codes (e.g., `"ENAR 151"`) without the `-PR` suffix, practical course variants (e.g., `"ENAR 151-PR"`) were never included in the population.

## Solution
Modified `generate_course_group_aware_population()` to automatically check for and include practical course variants when processing each group's enrolled courses.

### Changes Made

1. **src/ga/population.py** (lines 47-56)
   - Added logic to check for practical course variants (`course_id + "-PR"`)
   - Now creates genes for BOTH theory and practical courses when they exist

2. **src/encoder/input_encoder.py** (lines 152-174)
   - Added `int()` wrapper to `quanta_per_week` parameters
   - Prevents float-to-int type errors during quantum assignment

## Verification
After fix, schedules now include both theory and practical courses:
- Theory courses: Tagged with `(TH)` in exports
- Practical courses: Tagged with `(PR)` in exports
- Test run showed **168 practical course sessions** in output

## Architecture Notes
- Loader (`input_encoder.py`) splits L+T+P courses into separate theory/practical Course objects
- Linking (`link_courses_and_groups`) correctly links both variants to groups via shared `course_code`
- Population generator now aligns with this split-course architecture
