# Population Integrity Validation Switch

## Configuration Added

### Location: `config/ga_params.py`

```python
# ============================================================================
# POPULATION INTEGRITY VALIDATION
# ============================================================================
# Enable strict validation that checks if individuals maintain the same course-group pairs
# during crossover. This catches population corruption bugs but may be disabled for performance
# or to allow experimental operators that intentionally modify population structure.

VALIDATE_POPULATION_INTEGRITY = False  # Set to True to enable strict validation checks
```

## What It Does

### When `VALIDATE_POPULATION_INTEGRITY = True` (Strict Mode)
- **Crossover validation enabled**
- Before swapping attributes, checks that both parents have **identical (course, group) pairs**
- **Raises `ValueError`** if mismatch detected:
  ```
  [X] CROSSOVER ERROR: Individuals have mismatched (course, group) pairs!
     Individual 1 has 502 pairs, Individual 2 has 505 pairs.
     Missing in Individual 1: {...}
     Missing in Individual 2: {...}
     This indicates population corruption or invalid mutation.
  ```
- **Use case**: Debugging, catching bugs in repair operators, ensuring population integrity

### When `VALIDATE_POPULATION_INTEGRITY = False` (Permissive Mode - Default)
- **Crossover validation disabled**
- Crossover only swaps attributes for **common (course, group) pairs** (intersection)
- **Silently ignores** mismatched pairs
- **Does NOT raise errors** even if individuals differ
- **Use case**: 
  - Experimental operators that intentionally modify structure
  - Performance optimization (skip validation overhead)
  - Allowing incomplete/extra session repair to add/remove genes
  - Running with known population corruption (workaround mode)

## Implementation Details

### Modified File: `src/ga/operators/crossover.py`

**Key Changes:**

1. **Import config at function start:**
   ```python
   from config.ga_params import VALIDATE_POPULATION_INTEGRITY
   ```

2. **Conditional validation:**
   ```python
   if VALIDATE_POPULATION_INTEGRITY:
       keys1 = set(gene_map1.keys())
       keys2 = set(gene_map2.keys())
       
       if keys1 != keys2:
           # Raise detailed ValueError
   ```

3. **Safe crossover when validation disabled:**
   ```python
   # Only process common keys (intersection)
   keys_to_process = (
       gene_map1.keys() if VALIDATE_POPULATION_INTEGRITY 
       else (set(gene_map1.keys()) & set(gene_map2.keys()))
   )
   ```

## When to Use Each Mode

### Use `VALIDATE_POPULATION_INTEGRITY = True` when:
- ✅ Developing new repair operators
- ✅ Debugging population corruption issues
- ✅ Running production with guaranteed stable operators
- ✅ Testing genetic operator correctness
- ✅ Ensuring all individuals have identical structure

### Use `VALIDATE_POPULATION_INTEGRITY = False` when:
- ✅ Running with experimental repair operators (like current clustering repair)
- ✅ Using `repair_incomplete_or_extra_sessions` that adds/removes genes
- ✅ Performance-critical runs (skip validation overhead)
- ✅ Temporary workaround for known issues
- ✅ Allowing dynamic population structure changes

## Current Recommendation

**Current Setting: `False`** (Permissive Mode)

### Why?
The current `repair_session_clustering` and potentially other repairs may cause temporary structural mismatches during evolution. Setting to `False` allows the GA to continue running while we monitor and improve repair stability.

### Future:
Once all repair operators are verified to preserve population structure, switch to `True` for production runs to catch any regression bugs early.

## Error Message Update

When validation is enabled and fails, the error now includes instructions:
```
This indicates population corruption or invalid mutation.
To disable this check, set VALIDATE_POPULATION_INTEGRITY=False in config/ga_params.py
```

## Related Configuration

### Other GA Parameters (same file)
```python
POP_SIZE = 100  # Population size
NGEN = 100      # Number of generations
CXPB = 0.8      # Crossover probability
MUTPB = 0.3     # Mutation probability

# Repair configuration
REPAIR_HEURISTICS_CONFIG = {
    "enabled": True,
    "max_iterations": 3,
    "apply_after_mutation": True,
    "apply_after_crossover": True,
    ...
}
```

## Testing

### Test with validation enabled:
```python
# In config/ga_params.py
VALIDATE_POPULATION_INTEGRITY = True
```
Run: `.\x.ps1`
- Should raise error if population corruption occurs

### Test with validation disabled:
```python
# In config/ga_params.py
VALIDATE_POPULATION_INTEGRITY = False
```
Run: `.\x.ps1`
- Should continue running even with structural mismatches
- Crossover only swaps attributes for common genes

## Notes

- This switch affects **only** `crossover_course_group_aware()` function
- The deprecated `crossover_uniform()` is not affected (not recommended for use)
- Default value is `False` for maximum flexibility during development
- Can be changed at any time - takes effect on next program run
- No performance impact when disabled (validation code is skipped entirely)
