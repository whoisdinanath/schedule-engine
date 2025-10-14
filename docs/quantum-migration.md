# Migration Guide: Continuous Quantum System

## Breaking Changes

Quantum indices now continuous (only operational hours). All quantum-dependent code requires updates.

## Files Requiring Changes

### 1. `src/entities/instructor.py` (Line 63)
```python
# OLD: if not 0 <= quanta < time_system.TOTAL_WEEKLY_QUANTA:
# NEW:
if not 0 <= quanta < time_system.total_quanta:
```

### 2. `src/constraints/soft.py` ⚠️ CRITICAL
**Problem**: Hardcoded `QUANTA_PER_DAY = 96`, uses modulo arithmetic for day determination.

**Solution**: Pass `time_system` to penalty functions, use `quanta_to_time()` for day lookup:
```python
# OLD: day = q // QUANTA_PER_DAY
# NEW: day, _ = time_system.quanta_to_time(q)
```

Update signatures: `group_gaps_penalty(sessions, time_system)`, etc.

**Midday break**: Calculate dynamically per day, not with hardcoded quantum ranges.

### 3. `src/encoder/input_encoder.py`
Likely OK (already uses instance methods). Watch for boundary conditions with end times.

## Migration Steps

1. Fix `instructor.py` constant
2. Rewrite `soft.py` day-grouping logic (highest risk)
3. Update all soft constraint callers to pass `time_system`
4. Test GA operators for quantum assumptions
5. Full integration test

## Impact Assessment
- **High risk**: soft.py (complete rewrite needed)
- **Medium risk**: instructor.py, GA operators
- **Low risk**: input_encoder.py

**DO NOT run main GA until soft.py is fixed** - will produce incorrect penalties.

## Testing
Run `test_continuous_quanta.py` to verify quantum system. Regenerate all schedules after migration (old quantum values invalid).
