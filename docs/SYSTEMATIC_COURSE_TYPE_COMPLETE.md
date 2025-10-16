# Code Quality Improvement: Systematic Course Type Usage

## ✅ COMPLETED - All Name-Based Type Inference Removed

## Summary of Changes

Eliminated all instances of determining course type by parsing course names/IDs. Now **exclusively uses the `course.course_type` attribute** throughout the entire codebase.

---

## Modified Files

### 1. **src/ga/population.py** (4 fixes)

#### Fix 1: Course-Group Pair Extraction (lines ~48-61)
**Removed**: `practical_id = course_id + "-PR"` string manipulation  
**Added**: Systematic lookup using `course.course_code` matching

```python
# Now finds ALL courses matching the course_code
matching_courses = [
    course_id for course_id, course in context.courses.items()
    if hasattr(course, 'course_code') and course.course_code == course_code
]
```

#### Fix 2-4: Session Gene Creation (lines ~84, ~179, ~235)
**Removed**: `is_practical = course_id.endswith("-PR")`  
**Replaced**: Direct use of `course.course_type`

```python
# Before (BAD):
is_practical = course_id.endswith("-PR")
session_type = "practical" if is_practical else "theory"

# After (GOOD):
session_type = course.course_type
```

---

### 2. **src/ga/course_group_pairs.py** (complete refactor)

**Removed**: Manual construction of practical IDs  
**Removed**: Inferring type from L, T, P values  
**Added**: Course object iteration with type checking

```python
# Before (BAD):
practical_course_id = course_id + "-PR" if not course_id.endswith("-PR") else course_id

# After (GOOD):
for course_id, course in matching_courses:
    if course.course_type == "theory":
        # Handle theory
    elif course.course_type == "practical":
        # Handle practical
```

---

## Architecture Pattern

### ✅ Correct Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Data Loading (SINGLE SOURCE OF TRUTH)                    │
│    src/encoder/input_encoder.py                             │
│    ├─ load_courses() sets course_type="theory"/"practical"  │
│    └─ Course objects have course_type attribute             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Population Generation                                     │
│    src/ga/population.py, src/ga/course_group_pairs.py       │
│    ├─ Read course.course_type (NEVER parse name)            │
│    └─ Create SessionGene with correct type                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Decoding                                                  │
│    src/decoder/individual_decoder.py                         │
│    └─ Propagate course.course_type to CourseSession         │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Export                                                    │
│    src/exporter/exporter.py                                  │
│    └─ Use session.course_type for (TH)/(PR) tags            │
└─────────────────────────────────────────────────────────────┘
```

---

## Code Quality Principles Applied

### 1. **Single Source of Truth**
- Type is set **once** during course loading
- All other code **reads** the attribute
- No redundant type determination logic

### 2. **Don't Repeat Yourself (DRY)**
- Type logic centralized in `load_courses()`
- Eliminated duplicate type-checking code

### 3. **Use Structured Data**
- Attributes over string parsing
- `course.course_type` over `course_id.endswith("-PR")`

### 4. **Maintainability**
- Can change ID convention without breaking logic
- Type information explicit and self-documenting

### 5. **Type Safety**
- Structured attribute access
- No risk of parsing errors or typos

---

## Verification

### ✅ Syntax Checks
- All modified files pass Python syntax validation
- No import errors
- No attribute errors

### ✅ Pattern Elimination
```bash
# No more bad patterns found:
grep -r "endswith.*-PR" src/   # Only in comments/strings
grep -r "course_id.*-PR" src/  # Only creating IDs, not checking
```

### ✅ Consistent Usage
All course type checks now use:
- `course.course_type == "theory"`
- `course.course_type == "practical"`
- `session_type = course.course_type`
- `component_type = course.course_type`

---

## Files With NO Changes Needed

These already used `course_type` correctly:
- ✅ `src/entities/course.py` - Defines course_type attribute
- ✅ `src/entities/decoded_session.py` - Has course_type field
- ✅ `src/decoder/individual_decoder.py` - Propagates course.course_type
- ✅ `src/exporter/exporter.py` - Uses session.course_type
- ✅ `src/validation/input_validator.py` - Validates using course.course_type
- ✅ `src/encoder/input_encoder.py` - Sets course_type correctly

---

## Impact

### Before
- 🔴 4 locations checking `course_id.endswith("-PR")`
- 🔴 String manipulation to construct practical IDs
- 🔴 Type inferred from name patterns
- 🔴 Scattered type-checking logic

### After
- ✅ 0 name-based type inference
- ✅ All type checks use `course.course_type`
- ✅ Systematic course lookup by `course_code`
- ✅ Clean, maintainable, self-documenting code

---

## Related Documentation
- `docs/REFACTOR_SYSTEMATIC_COURSE_TYPE.md` - Detailed change log
- `docs/COURSE_TYPE_TAGS_IMPLEMENTATION.md` - Original feature implementation
- `docs/COURSE_FILTERING_BY_ENROLLMENT.md` - Course loading process
