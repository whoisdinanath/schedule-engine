# Course Type Tags Implementation

## Overview
Added `course_type` field to distinguish theory and practical courses throughout the system, with (TH) and (PR) tags displayed in exported schedules.

## Changes Made

### 1. Course Entity (`src/entities/course.py`)
- Added `course_type: str` field (default: "theory")
- Values: "theory" or "practical"

### 2. Input Encoder (`src/encoder/input_encoder.py`)
- `load_courses()` sets `course_type="theory"` for theory courses (L+T)
- `load_courses()` sets `course_type="practical"` for practical courses (P, ID ends with "-PR")

### 3. CourseSession Entity (`src/entities/decoded_session.py`)
- Added `course_type: str` field (default: "theory")
- Propagated from Course during decoding

### 4. Individual Decoder (`src/decoder/individual_decoder.py`)
- `decode_individual()` copies `course_type` from Course to CourseSession

### 5. Exporter (`src/exporter/exporter.py`)
- **Helper Function**: `_format_course_name_with_type()` appends (TH)/(PR) tags
- **JSON Export**: 
  - `course_id` field contains formatted name with tag
  - `original_course_id` field preserves original ID
  - `course_type` field explicitly included
- **PDF Calendar**: Automatically uses formatted names from JSON (displays tags)

## Data Flow

```
Course.json (L, T, P values)
    ↓
load_courses() → Course objects with course_type
    ↓
SessionGene creation (uses Course)
    ↓
decode_individual() → CourseSession with course_type
    ↓
export_everything()
    ↓
JSON: {"course_id": "ENME 103 (TH)", "course_type": "theory", ...}
PDF: Calendar shows "ENME 103 (TH)" labels
```

## Output Examples

### JSON Export (`schedule.json`)
```json
{
  "course_id": "ENME 103 (TH)",
  "original_course_id": "ENME 103",
  "course_type": "theory",
  "instructor_id": "INS001",
  "group_ids": ["BAE2"],
  "room_id": "ROOM101",
  "time": {...}
}
```

```json
{
  "course_id": "ENME 103-PR (PR)",
  "original_course_id": "ENME 103-PR",
  "course_type": "practical",
  "instructor_id": "INS002",
  "group_ids": ["BAE2A"],
  "room_id": "LAB101",
  "time": {...}
}
```

### PDF Calendar
- Theory classes display: **ENME 103 (TH)**
- Practical classes display: **ENME 103-PR (PR)**

## Backward Compatibility
- Original `course_id` preserved in JSON as `original_course_id`
- Internal GA operations unchanged (use original IDs)
- Display-only modification (no constraint logic affected)

## Notes
- Course type determined at load time based on L/T/P values
- Theory: L + T > 0
- Practical: P > 0, course_id ends with "-PR"
- Tags only appear in exports, not in internal processing
- Consistent with thesis ASCII-only style requirements
