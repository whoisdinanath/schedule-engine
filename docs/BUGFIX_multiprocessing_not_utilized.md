# BUGFIX: Multiprocessing Pool Not Utilized

## Problem
Despite `USE_MULTIPROCESSING=True` and a Pool being created, **ALL CPU cores are NOT being utilized**. The GA runs single-threaded even with multiprocessing enabled.

## Root Cause
**Two critical bugs prevent DEAP's parallel map from being used:**

### Bug #1: Initial Population Evaluation (Line 207-209)
```python
# WRONG - Uses sequential for-loop instead of toolbox.map
fitness_values = []
for ind in self.population:
    fitness_values.append(self.toolbox.evaluate(ind))
```

**Should be:**
```python
fitness_values = self.toolbox.map(self.toolbox.evaluate, self.population)
```

### Bug #2: Generation Evolution Evaluation (Line 367)
```python
# WRONG - Uses Python's built-in map (sequential) instead of toolbox.map
fitness_values = list(map(self.toolbox.evaluate, invalid))
```

**Should be:**
```python
fitness_values = list(self.toolbox.map(self.toolbox.evaluate, invalid))
```

### Bug #3: Elite Evaluation in Memetic Mode (Line 401)
```python
# WRONG - Uses Python's built-in map (sequential)
fitness_values = list(map(self.toolbox.evaluate, elite_individuals))
```

**Should be:**
```python
fitness_values = list(self.toolbox.map(self.toolbox.evaluate, elite_individuals))
```

## Why This Matters
- **Current behavior**: Python's built-in `map()` is sequential, runs on single core
- **Expected behavior**: `toolbox.map()` uses Pool.map() when registered, distributes work across all cores
- **Performance impact**: 3-6× speedup lost

## How DEAP Parallelization Works
1. When `pool` is provided, `toolbox.register("map", pool.map)` is called (Line 142)
2. `toolbox.map()` becomes `pool.map()` which parallelizes across workers
3. MUST use `toolbox.map()` instead of built-in `map()` for parallelization
4. Each worker evaluates a subset of individuals independently

## Current State
```python
# Setup is CORRECT (Line 141-142)
if self.pool is not None:
    self.toolbox.register("map", self.pool.map)

# But USAGE is WRONG (using built-in map instead of toolbox.map)
```

## Fix Required
Replace all `map(self.toolbox.evaluate, ...)` with `self.toolbox.map(self.toolbox.evaluate, ...)` in 3 locations.

## Performance Expectations After Fix
- **Single-core**: 100% usage on 1 core
- **Multi-core (8 cores)**: ~80-90% usage on all 8 cores (some overhead for process communication)
- **Speedup**: 3-6× faster depending on CPU cores and evaluation complexity
- **Best for**: Large populations (50+), complex constraint evaluation

## Additional Optimization Opportunities
1. **Increase population size** when multiprocessing is enabled (current: 10 → recommended: 50-100)
2. **Use chunk size** for better load balancing: `pool.map(func, data, chunksize=2)`
3. **Profile evaluation time** to ensure it's worth parallelizing (>10ms per individual)
4. **Consider ProcessPoolExecutor** from concurrent.futures for better Windows compatibility

## Files Modified
- `src/core/ga_scheduler.py` (3 locations)

## Testing
After fix, verify with:
1. Task Manager / htop: Should see all CPU cores active during GA run
2. Time comparison: Run with `USE_MULTIPROCESSING=False` vs `True`, expect 3-6× speedup
3. Results validation: Ensure same quality solutions (multiprocessing shouldn't change GA behavior)
