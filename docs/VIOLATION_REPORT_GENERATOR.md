# Constraint Violation Report Generator

## Overview
Automatically generates detailed human-readable reports of all constraint violations in the final schedule.

## Output Location
`output/evaluation_<timestamp>/violation_report.txt`

## Report Sections

### 1. Group Overlap Violations
Shows when a student group is scheduled in multiple sessions at the same time.

**Format:**
```
⚠️  Group [GROUP_ID] has [N] overlapping sessions at [DAY TIME]:
    - [COURSE] @ [ROOM] with [INSTRUCTOR]
    - [COURSE] @ [ROOM] with [INSTRUCTOR]
```

**Example:**
```
⚠️  Group BAE4A has 2 overlapping sessions at Friday 17:00:
    - ENEE 254 @ Seminar Room E-104 with Madhusudan Nyaupane
    - ENME 256 @ Seminar Room E-405 with Sajendra Man Bajracharya
```

### 2. Instructor Conflict Violations
Shows when an instructor is assigned to teach multiple sessions simultaneously.

**Format:**
```
⚠️  Instructor [NAME] has [N] overlapping sessions at [DAY TIME]:
    - [COURSE] with [GROUPS] @ [ROOM]
    - [COURSE] with [GROUPS] @ [ROOM]
```

**Example:**
```
⚠️  Instructor Hari Bahadur has 5 overlapping sessions at Sunday 08:00:
    - ENAR 151 with BARCH2A, BARCH2B @ Classroom A-201
    - ENAR 152 with BARCH2A @ Classroom E-403
```

### 3. Room Conflict Violations
Shows when a room is double-booked for multiple sessions.

**Format:**
```
⚠️  Room [ROOM_NAME] has [N] overlapping sessions at [DAY TIME]:
    - [COURSE] with [GROUPS] by [INSTRUCTOR]
    - [COURSE] with [GROUPS] by [INSTRUCTOR]
```

**Example:**
```
⚠️  Room Classroom B-311 has 2 overlapping sessions at Sunday 08:00:
    - ENSH 153 with BAE2A, BAE2B by Dinesh Shah
    - ENAR 155 with BARCH2A, BARCH2B by Sita Sharma
```

### 4. Instructor Qualification Violations
Lists courses taught by unqualified instructors.

**Format:**
```
⚠️  Instructor [NAME] is NOT qualified for [COURSE] ([TYPE])
    Groups: [GROUP_LIST]
    Room: [ROOM_NAME]
```

### 5. Room Type Mismatch Violations
Shows courses scheduled in rooms lacking required features.

**Format:**
```
⚠️  Course [COURSE_ID] requires features not in room [ROOM_NAME]
    Groups: [GROUP_LIST]
    Required: [FEATURE_LIST]
    Room has: [AVAILABLE_FEATURES]
    Missing: [MISSING_FEATURES]
```

### 6. Availability Violations
Three sub-categories:
- **Instructor Unavailable**: Instructor scheduled during unavailable time
- **Room Unavailable**: Room scheduled outside operating hours
- **Group Unavailable**: Group scheduled during unavailable time

**Format:**
```
⚠️  [ENTITY] unavailable at [DAY TIME]
    Course: [COURSE_ID]
    Groups/Room/Instructor: [DETAILS]
```

### 7. Schedule Completeness Violations
Shows courses with incorrect number of scheduled sessions.

**Format:**
```
⚠️  [COURSE] for group [GROUP]: Expected [N] quanta, got [M]
```

## Implementation

### Module Location
`src/exporter/violation_reporter.py`

### Integration
Called automatically from `generate_reports()` in `src/workflows/reporting.py`:

```python
generate_violation_report(decoded_schedule, course_map, qts, output_dir)
```

### Key Functions
- `generate_violation_report()`: Main entry point
- `_check_group_overlaps()`: Detects group conflicts
- `_check_instructor_conflicts()`: Detects instructor conflicts  
- `_check_room_conflicts()`: Detects room conflicts
- `_check_instructor_qualifications()`: Validates instructor qualifications
- `_check_room_type_mismatches()`: Validates room features
- `_check_availability_violations()`: Validates time availability
- `_check_incomplete_schedules()`: Validates session completeness

### Output Format
- Plain text UTF-8 file
- 80-character width for readability
- Grouped by violation type
- Sorted and formatted for easy scanning
- Total violation count at top

## Usage

### Automatic Generation
Runs automatically when executing the standard workflow:
```bash
python main.py
```

Report appears in: `output/evaluation_<timestamp>/violation_report.txt`

### Manual Testing
```bash
python test/test_violation_report.py
```

Creates report in: `test_output/violation_report.txt`

## Benefits
- **Quick Problem Identification**: Immediately see what's wrong with schedule
- **Human-Readable**: Clear natural language descriptions
- **Actionable**: Shows exact courses, groups, rooms, times involved
- **Comprehensive**: Covers all hard constraint types
- **Time-Stamped**: Each run creates new timestamped output

## Use Cases
1. **Debugging**: Understand why GA fitness isn't zero
2. **Manual Review**: Verify schedule correctness before deployment
3. **Reporting**: Share constraint issues with stakeholders
4. **Optimization**: Identify which constraints need attention
