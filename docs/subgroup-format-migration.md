# Subgroup Format Migration

## Overview
Updated the Groups.json structure to support detailed subgroup information with individual student counts, treating subgroups as independent Group entities rather than creating a separate Subgroup class.

## JSON Format Change

### Old Format (List of Strings)
```json
{
    "group_id": "BAE2",
    "name": "Automobile Engineering Semester 2",
    "student_count": 47,
    "courses": ["ENSH 151", "ENSH 153", ...],
    "subgroups": ["BAE2A", "BAE2B"]
}
```

### New Format (List of Objects)
```json
{
    "group_id": "BAE2",
    "name": "Automobile Engineering Semester 2",
    "student_count": 47,
    "courses": ["ENSH 151", "ENSH 153", ...],
    "subgroups": [
        {
            "id": "BAE2A",
            "student_count": 24
        },
        {
            "id": "BAE2B",
            "student_count": 23
        }
    ]
}
```

## Design Decision: No Separate Subgroup Entity

**Rationale**: Subgroups are essentially groups themselves. Instead of creating a separate `Subgroup` dataclass, we:
1. Parse subgroup data from JSON
2. Create independent `Group` entities for each subgroup
3. Inherit courses and availability from parent group

This approach:
- ✅ Keeps the data model simple (single Group entity)
- ✅ Allows subgroups to be used anywhere groups are used
- ✅ Maintains backward compatibility with old string-based format
- ✅ No special handling needed in GA, constraints, or exporters

## Code Changes

### 1. Input Encoder (`src/encoder/input_encoder.py`)
**Enhanced `load_groups()` function:**
- Parses both old format (string) and new format (dict with `id` and `student_count`)
- Creates separate `Group` objects for each subgroup
- Subgroups inherit:
  - `enrolled_courses` from parent
  - `available_quanta` from parent
  - Name format: `"{Parent Name} - {Subgroup ID}"`

```python
# Parent group
groups["BAE2"] = Group(
    group_id="BAE2",
    name="Automobile Engineering Semester 2",
    student_count=47,
    enrolled_courses=["ENSH 151", ...],
    available_quanta={...}
)

# Subgroups created as independent Group entities
groups["BAE2A"] = Group(
    group_id="BAE2A",
    name="Automobile Engineering Semester 2 - BAE2A",
    student_count=24,
    enrolled_courses=["ENSH 151", ...],  # Inherited
    available_quanta={...}               # Inherited
)
```

### 2. Test Updates (`test/test_subgroup_behavior.py`)
Updated to extract subgroup IDs from new dict format:
```python
# Handle both formats
for sg in group["subgroups"]:
    if isinstance(sg, dict):
        subgroups.add(sg["id"])  # New format
    else:
        subgroups.add(sg)        # Old format (backward compat)
```

### 3. Group Entity (`src/entities/group.py`)
**No changes needed** - remains simple dataclass without subgroup field

## Backward Compatibility

The encoder supports **both** old and new formats:
- **Old**: `"subgroups": ["BAE2A", "BAE2B"]` (strings)
- **New**: `"subgroups": [{"id": "BAE2A", "student_count": 24}, ...]` (objects)

Student counts fallback:
- New format: Uses explicit `student_count` from JSON
- Old format: Divides parent count equally among subgroups

## Impact on Existing Code

✅ **No changes needed in:**
- `SessionGene` (already uses `group_ids: List[str]`)
- GA operators (work with any group ID)
- Constraints (work with any group ID)
- Exporters (work with any group ID)
- Decoder (works with any group ID)

**Why?** Because subgroups are now just regular `Group` objects in the groups dictionary.

## Usage Examples

### Creating Sessions for Subgroups
```python
# Theory session for entire class (parent group)
SessionGene(
    course_id="ENME 151",
    instructor_id="INS001",
    group_ids=["BAE2"],  # Parent group
    room_id="ROOM101",
    quanta=[32, 33, 34, 35]
)

# Practical session for subgroup
SessionGene(
    course_id="ENME 151-PR",
    instructor_id="INS001",
    group_ids=["BAE2A"],  # Subgroup
    room_id="LAB101",
    quanta=[40, 41, 42, 43]
)
```

### Accessing Subgroups in Code
```python
groups = load_groups("data/Groups.json", qts)

# Both parent and subgroups are in the same dictionary
parent = groups["BAE2"]        # Group object
subgroup_a = groups["BAE2A"]   # Group object (same type)
subgroup_b = groups["BAE2B"]   # Group object (same type)

# Subgroups inherit courses
assert set(subgroup_a.enrolled_courses) == set(parent.enrolled_courses)
```

## Validation

Created `test/test_new_subgroup_format.py` that verifies:
- ✅ Parent groups loaded correctly
- ✅ Subgroups created as separate Group entities
- ✅ Subgroups inherit courses from parent
- ✅ Student counts match between parent and subgroups
- ✅ Total: 50 groups loaded (14 parents + 36 subgroups)

## Migration Checklist

- [x] Update `load_groups()` to parse new subgroup format
- [x] Maintain backward compatibility with old string format
- [x] Update `test_subgroup_behavior.py` for new format
- [x] Create validation test
- [x] Verify no changes needed in GA/constraints/exporters
- [x] Document the changes

## Benefits

1. **Explicit Student Counts**: Each subgroup has precise enrollment data
2. **Simple Design**: No separate Subgroup class needed
3. **Backward Compatible**: Old JSON files still work
4. **Type Consistency**: Subgroups are Groups, reducing special cases
5. **GA Compatibility**: Works seamlessly with multi-group session support
