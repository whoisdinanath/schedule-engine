# Parallelization Implementation Guide

## Quick Start: 3-Step Implementation

### Step 1: Modify `main.py`

**Current**:
```python
def main():
    result = run_standard_workflow(...)
    # print results

if __name__ == "__main__":
    main()
```

**New**:
```python
def main():
    import multiprocessing
    
    # Create process pool
    pool = multiprocessing.Pool()
    
    try:
        result = run_standard_workflow(
            pop_size=POP_SIZE,
            generations=NGEN,
            crossover_prob=CXPB,
            mutation_prob=MUTPB,
            validate=True,
            pool=pool,  # Pass pool to workflow
        )
        # print results (same as before)
    finally:
        pool.close()
        pool.join()

if __name__ == "__main__":
    main()
```

### Step 2: Modify `src/workflows/standard_run.py`

**In `run_standard_workflow()` signature**:
```python
def run_standard_workflow(
    pop_size: int,
    generations: int,
    crossover_prob: float = 0.7,
    mutation_prob: float = 0.2,
    data_dir: str = "data",
    output_dir: Optional[str] = None,
    seed: int = 69,
    validate: bool = True,
    pool = None,  # NEW: Add pool parameter
) -> Dict:
```

**Pass pool to scheduler** (find where GAScheduler is created):
```python
scheduler = GAScheduler(ga_config, context, hard_names, soft_names, pool=pool)
```

### Step 3: Modify `src/core/ga_scheduler.py`

**In `GAScheduler.__init__()`**:
```python
def __init__(
    self,
    config: GAConfig,
    context: SchedulingContext,
    hard_constraint_names: List[str],
    soft_constraint_names: List[str],
    pool = None,  # NEW: Add pool parameter
):
    self.config = config
    self.context = context
    self.hard_constraint_names = hard_constraint_names
    self.soft_constraint_names = soft_constraint_names
    self.pool = pool  # NEW: Store pool
    
    # ... rest of init
```

**In `GAScheduler.setup_toolbox()`**, after creating toolbox:
```python
def setup_toolbox(self):
    self.toolbox = base.Toolbox()
    
    # NEW: Register parallel map if pool provided
    if self.pool is not None:
        self.toolbox.register("map", self.pool.map)
    
    # Selection operator (no change)
    self.toolbox.register("select", tools.selNSGA2)
    
    # ... rest of setup
```

**That's it!** DEAP automatically uses `toolbox.map()` for evaluations.

## Advanced: Configuration Toggle

**Add to `config/ga_params.py`**:
```python
# Parallelization Settings
USE_MULTIPROCESSING = True  # Set to False for debugging
NUM_WORKERS = None  # None = use all CPUs, or specify (e.g., 4)
```

**Update `main.py`**:
```python
from config.ga_params import USE_MULTIPROCESSING, NUM_WORKERS

def main():
    pool = None
    
    if USE_MULTIPROCESSING:
        import multiprocessing
        pool = multiprocessing.Pool(processes=NUM_WORKERS)
    
    try:
        result = run_standard_workflow(..., pool=pool)
        # ...
    finally:
        if pool:
            pool.close()
            pool.join()
```

## Testing & Validation

### Test 1: Smoke Test (Fast)
```powershell
# Edit config/ga_params.py:
# POP_SIZE = 20
# NGEN = 10

python main.py
# Should complete in ~10-30 seconds
```

### Test 2: Correctness Test
```powershell
# Run with and without parallelization, compare outputs

# Disable parallelization
# In config/ga_params.py: USE_MULTIPROCESSING = False
python main.py  # Note hard/soft violations

# Enable parallelization  
# In config/ga_params.py: USE_MULTIPROCESSING = True
python main.py  # Should get similar (not identical) results

# Results should be close (within 10% due to randomness)
```

### Test 3: Performance Benchmark
```powershell
# Time sequential version
# In config/ga_params.py: USE_MULTIPROCESSING = False
Measure-Command { python main.py }

# Time parallel version
# In config/ga_params.py: USE_MULTIPROCESSING = True  
Measure-Command { python main.py }

# Compare TotalSeconds
```

### Test 4: Stress Test
```powershell
# Larger population to stress-test memory
# In config/ga_params.py:
# POP_SIZE = 200
# NGEN = 100

python main.py
# Monitor RAM usage in Task Manager
```

## Troubleshooting

### Issue: "RuntimeError: can't pickle lambda"

**Cause**: Lambda functions can't be pickled
**Fix**: Ensure all registered functions are module-level

### Issue: "EOFError" or "PicklingError"

**Cause**: Trying to pickle unpicklable objects
**Solution**: Check that `evaluate()` and all constraint functions:
- Are defined at module level (not inside other functions)
- Don't reference global state (except through arguments)
- Don't use lambda/partial functions

### Issue: Slower with multiprocessing

**Causes**:
1. **Small population**: Overhead > benefit (need POP_SIZE ≥ 50)
2. **Fast evaluation**: If each evaluation < 1ms, overhead dominates
3. **Windows spawning**: Slower process creation than Unix

**Solutions**:
- Increase POP_SIZE
- Use chunksize: `pool.map(func, items, chunksize=10)`
- Profile to confirm evaluation is the bottleneck

### Issue: Different results each run

**Expected**: GAs are stochastic, some variation is normal
**If too different**: Ensure same seed, check for race conditions
**Acceptable**: ±10-20% variation in soft penalties

### Issue: No speedup

**Check**:
1. Are evaluations actually parallel? Add print in `evaluate()` to confirm
2. CPU usage: Should see 100% across all cores
3. Population size: Too small means insufficient work to parallelize
4. Profiling: Use `cProfile` to identify true bottleneck

## Performance Expectations

### Theoretical Speedup
- **4 cores**: 3-3.5× faster
- **8 cores**: 4-6× faster  
- **16 cores**: 5-8× faster (diminishing returns due to overhead)

### Actual Speedup (Measured)
Depends on:
- Evaluation time (longer = better parallelization)
- Population size (larger = better parallelization)
- Memory bandwidth (can become bottleneck)

### When Speedup is Good
- POP_SIZE ≥ 100
- Evaluation time ≥ 10ms per individual
- CPU-bound (not I/O or memory bound)

### When Speedup is Poor
- POP_SIZE < 50 (overhead dominates)
- Fast evaluations < 1ms (pickling overhead)
- Memory constrained (thrashing)

## Debugging Tips

### Enable/Disable Parallelization
```python
# config/ga_params.py
USE_MULTIPROCESSING = False  # Easy toggle for debugging
```

### Add Logging to Evaluation
```python
# src/ga/evaluator/fitness.py
import os

def evaluate(individual, courses, instructors, groups, rooms):
    pid = os.getpid()
    print(f"[PID {pid}] Evaluating individual...")
    # ... rest of function
```
Run with parallelization → should see multiple PIDs

### Profile Performance
```powershell
python -m cProfile -o profile.stats main.py
python -m pstats profile.stats
# > sort cumtime
# > stats 20
```
Look for `evaluate` in top entries → confirms it's the bottleneck

## Best Practices

1. **Always use `if __name__ == "__main__"`** on Windows
2. **Keep functions at module level** (not nested)
3. **Avoid global state** in parallel code
4. **Test with small runs first** before full GA
5. **Monitor resource usage** (CPU, RAM) during runs
6. **Use configuration flags** for easy debugging
7. **Benchmark before/after** to confirm speedup

## Next Steps After Implementation

1. **Profile**: Identify next bottleneck (likely won't be evaluation anymore)
2. **Optimize constraints**: If still slow, optimize hot constraint functions
3. **Tune GA params**: May be able to reduce NGEN with parallel speedup
4. **Consider SCOOP**: For distributed computing across machines (advanced)

## Code Review Checklist

Before committing:
- [ ] All functions are module-level (no lambdas/partials)
- [ ] `if __name__ == "__main__"` guard in main.py
- [ ] Pool properly closed in finally block
- [ ] Configuration toggle works
- [ ] Tested with/without parallelization
- [ ] Performance improvement documented
- [ ] No regression in solution quality

## References

- **DEAP Parallel**: https://deap.readthedocs.io/en/master/tutorials/basic/part4.html
- **Multiprocessing**: https://docs.python.org/3/library/multiprocessing.html
- **Windows specifics**: https://docs.python.org/3/library/multiprocessing.html#multiprocessing-programming
