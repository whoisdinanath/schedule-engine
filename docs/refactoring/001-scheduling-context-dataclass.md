# Refactoring 001: SchedulingContext Dataclass

**Date:** October 16, 2025  
**Type:** Type Safety Improvement  
**Risk:** LOW  
**Status:** ✅ COMPLETED

---

## Problem

The codebase passed a generic `Dict[str, Any]` called `context` to 20+ functions, making it:
- **Type-unsafe** - No IDE autocomplete, typos not caught
- **Unclear** - What keys are required? What are their types?
- **Error-prone** - Runtime KeyErrors instead of compile-time checks

Example from old code:
```python
def mutate_gene(gene: SessionGene, context) -> SessionGene:
    # What's in context? Must read docs or guess
    course = context["courses"].get(gene.course_id)  # KeyError risk
```

---

## Solution

Created `src/core/types.py` with type-safe `SchedulingContext` dataclass:

```python
@dataclass
class SchedulingContext:
    """Type-safe container for scheduling context."""
    courses: Dict[str, Course]
    groups: Dict[str, Group]
    instructors: Dict[str, Instructor]
    rooms: Dict[str, Room]
    available_quanta: List[int]
```

### Benefits:
1. **Type checking** - mypy/IDE catches errors
2. **Autocomplete** - IDE suggests available fields
3. **Documentation** - Clear API contract
4. **Validation** - Built-in `.validate()` method

---

## Changes Made

### New Files:
- `src/core/types.py` - Core type definitions
- `src/core/__init__.py` - Package init

### Migration Strategy:
Backward compatibility provided via:
- `context_from_dict()` - Convert old dict → new type
- `context_to_dict()` - Convert new type → old dict

This allows gradual migration without breaking existing code.

---

## Usage Example

### Before (Dict):
```python
def some_function(context: Dict):
    courses = context["courses"]  # No type hints
    groups = context["groups"]    # Typos not caught
```

### After (Dataclass):
```python
from src.core.types import SchedulingContext

def some_function(context: SchedulingContext):
    courses = context.courses  # Type-safe, autocomplete works
    groups = context.groups    # Typos caught by IDE
```

---

## Migration Path

### Phase 1: Backward Compatible (Current)
```python
# In main.py
context_dict = {
    "courses": courses,
    "groups": groups,
    # ...
}

# Convert for new functions
from src.core.types import context_from_dict
context = context_from_dict(context_dict)
```

### Phase 2: Update Function Signatures (Future)
Gradually update functions to accept `SchedulingContext` instead of `Dict`:
```python
# Old signature
def mutate_gene(gene: SessionGene, context: Dict) -> SessionGene:

# New signature
def mutate_gene(gene: SessionGene, context: SchedulingContext) -> SessionGene:
```

### Phase 3: Remove Compatibility Layer (Future)
Once all functions migrated, remove `context_from_dict()` and `context_to_dict()`.

---

## Testing

### Validation:
```python
from src.core.types import SchedulingContext

# Valid context
ctx = SchedulingContext(
    courses={...},
    groups={...},
    instructors={...},
    rooms={...},
    available_quanta=[1, 2, 3]
)
errors = ctx.validate()
assert errors == []

# Invalid context
ctx_bad = SchedulingContext(
    courses={},  # Empty!
    groups={},
    instructors={},
    rooms={},
    available_quanta=[]
)
errors = ctx_bad.validate()
assert "No courses loaded" in errors
```

### Backward Compatibility:
```python
from src.core.types import context_from_dict, context_to_dict

# Convert dict → dataclass
old_dict = {"courses": {...}, "groups": {...}, ...}
new_ctx = context_from_dict(old_dict)
assert isinstance(new_ctx, SchedulingContext)

# Convert dataclass → dict
recovered_dict = context_to_dict(new_ctx)
assert recovered_dict.keys() == old_dict.keys()
```

---

## Impact Analysis

### Files Affected:
- ✅ `src/core/types.py` (NEW)
- 🔄 Functions using context (migration needed):
  - `src/ga/population.py` - 5 functions
  - `src/ga/operators/mutation.py` - 3 functions
  - `src/ga/operators/crossover.py` - 1 function

### Breaking Changes:
**NONE** - Backward compatibility maintained.

---

## Next Steps

1. **Update main.py** to create `SchedulingContext` instead of dict
2. **Gradually migrate** GA functions to use new type
3. **Add type hints** to all function signatures
4. **Remove compatibility** layer once migration complete

---

## Rollback

If this causes issues:
```bash
git revert <commit-hash>
# Or simply delete src/core/types.py
```

Since backward compatibility is maintained, reverting is safe.

---

## Lessons Learned

- **Type hints matter** - Catch bugs before runtime
- **Gradual migration** - Don't break existing code
- **Validation built-in** - Fail fast with clear errors
- **Documentation** - Dataclass is self-documenting

---

## References

- Python dataclasses: https://docs.python.org/3/library/dataclasses.html
- Type hints PEP 484: https://peps.python.org/pep-0484/
- Refactoring book: "Replace Data Value with Object"
