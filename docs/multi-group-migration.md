# Multi-Group Session Support Migration

## Overview
Modified the schedule engine to support multiple groups per session gene, enabling a single course session to be scheduled for multiple groups simultaneously (e.g., BAE2 and BAE4 attending the same lecture).

## Core Changes

### 1. SessionGene (`src/ga/sessiongene.py`)
- **Changed**: `group_id: str` → `group_ids: List[str]`
- Enables single sessions to serve multiple groups
- Example: One lecture in Room-101 can now serve [BAE2, BAE4] simultaneously

### 2. Decoder (`src/decoder/individual_decoder.py`)
- Updated to handle `group_ids` list from genes
- Maintains primary group reference (first in list) for backward compatibility
- Propagates full `group_ids` list to `CourseSession`

### 3. Population Generation (`src/ga/population.py`)
- All `SessionGene()` instantiations updated to use `group_ids=[group_id]`
- Three creation points modified:
  - `create_component_session_with_conflict_avoidance`
  - `create_component_session` 
  - `generate_random_session_gene`

### 4. Mutation Operators (`src/ga/operators/mutation.py`)
- Updated group mutation logic to handle lists
- 90% probability: preserve existing valid groups
- 70% probability: keep single group
- 30% probability: potentially create multi-group sessions
- Smart room selection uses primary group for capacity checks

### 5. Diversity Metrics (`src/metrics/diversity.py`)
- `gene_distance()` now compares `group_ids` as sets
- Order-independent comparison (e.g., [BAE2, BAE4] equals [BAE4, BAE2])

### 6. Hard Constraints (`src/constraints/hard.py`)
- `no_group_overlap()`: Already handles multiple groups via `session.group_ids`
- `availability_violations()`: Enhanced to check primary group availability properly

### 7. Soft Constraints (`src/constraints/soft.py`)
- All functions already iterate over `session.group_ids`
- No changes needed (already multi-group compatible)

### 8. JSON Exporter (`src/exporter/exporter.py`)
- JSON export now outputs `"group_ids": [...]` as list
- PDF generation updated to handle both old (`group_id`) and new (`group_ids`) formats
- Sessions appear on all assigned groups' calendars

## Backward Compatibility
- Old JSON files with `group_id` still supported in PDF generation
- Primary group concept maintained in decoder
- Single-group sessions remain default (mutation biased toward single groups)

## Usage Examples

### Creating Multi-Group Sessions Manually
```python
# In custom population or mutation logic
session = SessionGene(
    course_id="CS101",
    instructor_id="INS001",
    group_ids=["BAE2", "BAE4"],  # Multi-group session
    room_id="ROOM101",
    quanta=[32, 33, 34, 35]
)
```

### JSON Output Format
```json
{
  "course_id": "CS101",
  "instructor_id": "INS001",
  "group_ids": ["BAE2", "BAE4"],
  "room_id": "ROOM101",
  "time": {
    "Monday": [{"start": "08:00", "end": "09:00"}]
  }
}
```

## Impact on Constraints
- **Group overlap detection**: Automatically counts each group separately
- **Availability checks**: Validates primary group availability
- **Compactness penalties**: Sessions appear in all groups' schedules
- **Room capacity**: Checked against primary (first) group size

## Migration Notes
- Existing chromosomes with old structure incompatible (regenerate population)
- No data file changes needed (Groups.json unchanged)
- Mutation operator biased toward single groups (70%) to maintain stability
- Multi-group sessions more likely when enrolled groups overlap courses
