# Violation Report - Quick Reference

## Output Location
```
output/evaluation_<timestamp>/violation_report.txt
```

## Violation Types & Format

### 1. Group Overlaps
```
⚠️  Group [ID] has [N] overlapping sessions at [DAY TIME]:
    - [COURSE] @ [ROOM] with [INSTRUCTOR]
```

### 2. Instructor Conflicts
```
⚠️  Instructor [NAME] has [N] overlapping sessions at [DAY TIME]:
    - [COURSE] with [GROUPS] @ [ROOM]
```

### 3. Room Conflicts
```
⚠️  Room [NAME] has [N] overlapping sessions at [DAY TIME]:
    - [COURSE] with [GROUPS] by [INSTRUCTOR]
```

### 4. Instructor Not Qualified
```
⚠️  Instructor [NAME] is NOT qualified for [COURSE] ([TYPE])
    Groups: [GROUPS]
    Room: [ROOM]
```

### 5. Room Type Mismatch
```
⚠️  Course [ID] requires features not in room [NAME]
    Groups: [GROUPS]
    Required: [FEATURES]
    Room has: [FEATURES]
    Missing: [FEATURES]
```

### 6. Availability Violations
```
⚠️  [ENTITY] unavailable at [DAY TIME]
    Course: [COURSE]
    [Additional context]
```

### 7. Schedule Completeness
```
⚠️  [COURSE] for group [GROUP]: Expected [N] quanta, got [M]
```

## Running

### Automatic
```bash
python main.py
# Report automatically generated
```

### Test Only
```bash
python test/test_violation_report.py
# Report in: test_output/violation_report.txt
```

## Key Files
- Generator: `src/exporter/violation_reporter.py`
- Integration: `src/workflows/reporting.py`
- Test: `test/test_violation_report.py`
- Docs: `docs/VIOLATION_REPORT_GENERATOR.md`
