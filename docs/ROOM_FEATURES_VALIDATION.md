# Room Features Validation

## Overview
Validates that rooms have required features to accommodate enrolled courses.

## Problem
Groups enroll in courses requiring specific room features (e.g., lab equipment, computer facilities). If no rooms have those features, scheduling becomes impossible.

## Solution
Two-level validation:

### 1. Global Check
- Collect all required features from courses
- Verify at least one room exists per feature
- Reports missing features as ERRORS

### 2. Group-Specific Check  
- For each group's enrolled courses:
  - Extract required features
  - Find rooms matching features + capacity ≥ group size
  - Reports unsuitable course-group pairings as WARNINGS

## Usage

### Automatic (in main workflow)
```python
from src.validation import validate_input

validate_input(context)  # Includes room features check
```

### Standalone Test
```bash
python test/test_room_features_validation.py
```

Generates detailed report:
- Feature coverage (required vs available)
- Rooms per feature type
- Group-by-group suitability analysis
- Problem courses flagged

## Implementation
- `InputValidator._validate_room_features_for_enrolled_courses()` in `src/validation/input_validator.py`
- `test/test_room_features_validation.py` for standalone analysis

## Key Checks
1. Required features exist in room inventory
2. Sufficient capacity for group sizes
3. Feature-type matching considers flexible alternatives (e.g., auditorium can substitute for lecture room)
