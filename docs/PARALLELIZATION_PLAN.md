# Parallelization Plan for Schedule Engine

## Current State Analysis

**Problem**: Single-threaded GA runs slowly (POP_SIZE=100, NGEN=1000)
- Bottleneck: Fitness evaluation (~100-200 individuals/generation × 1000 generations)
- Each evaluation: decode individual → check all constraints (hard + soft)
- Sequential processing leaves CPU cores idle

## Parallelization Strategy

### Target: Fitness Evaluation (Highest Impact)

**Why**: 
- Evaluations are embarrassingly parallel (independent computations)
- Dominates runtime (happens every generation for invalid individuals)
- DEAP natively supports parallel map via `toolbox.register("map", pool.map)`

**Not parallelized** (low/negative ROI):
- Mutation: Fast, requires shared state
- Crossover: Fast, sequential dependencies
- Selection: Fast algorithm, minimal gain
- Population initialization: One-time cost

## Implementation Plan

### Phase 1: Multiprocessing Setup (PRIORITY)

**Changes Required**:

1. **Main entry point** (`main.py`)
   - Add Windows-safe `if __name__ == "__main__"` guard
   - Create multiprocessing Pool
   - Pass Pool to workflow

2. **GA Scheduler** (`src/core/ga_scheduler.py`)
   - Accept optional `map_func` parameter in constructor
   - Register custom map in `setup_toolbox()`: `toolbox.register("map", map_func)`
   - Use `toolbox.map()` consistently (already done via DEAP)

3. **Workflow** (`src/workflows/standard_run.py`)
   - Accept optional Pool parameter
   - Pass to GAScheduler

4. **Evaluation Functions** (CRITICAL)
   - Ensure `evaluate()` and `evaluate_detailed()` are module-level (not nested)
   - All dependencies (courses, instructors, groups, rooms) passed as arguments
   - Already picklable ✓

**Code Pattern**:
```python
# main.py
if __name__ == "__main__":
    import multiprocessing
    pool = multiprocessing.Pool()
    try:
        result = run_standard_workflow(..., pool=pool)
    finally:
        pool.close()
        pool.join()
```

### Phase 2: Performance Optimization

**Tuning**:
- Pool size: Default = CPU count, tune based on profiling
- Chunk size: `toolbox.register("map", pool.map, chunksize=5)` for load balancing
- Monitor overhead (pickling/unpickling individuals)

**Expected Speedup**:
- **4-8 cores**: 3-5× faster (accounting for overhead)
- **Bottleneck shifts to**: Selection/mutation/crossover (but these are fast)

### Phase 3: Advanced Optimizations (Optional)

**If still too slow**:

1. **Reduce constraint computation**
   - Cache decoded sessions (memoization with individual hash)
   - Early termination in constraints (stop counting after threshold)

2. **Smarter population size**
   - Adaptive population (start large, shrink when converging)
   - Island model (multiple sub-populations, periodic migration)

3. **SCOOP for distributed computing**
   - Cross-machine parallelization
   - Requires `python -m scoop main.py` invocation
   - More setup overhead, use only if single machine insufficient

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Windows spawning overhead | Slower startup | Use `if __name__` guard, benchmark |
| Pickling failures | Crashes | Test all functions are module-level, no lambdas |
| Memory overhead | OOM on large populations | Monitor RAM, reduce POP_SIZE if needed |
| Non-determinism | Different results per run | Set seed in Pool worker init function |
| Debugging harder | Dev slowdown | Toggle parallelization via flag |

## Testing Strategy

1. **Correctness**: Run with/without parallelization, compare results (same seed)
2. **Performance**: Benchmark with `time` command, track speedup vs cores
3. **Stability**: Stress test with NGEN=100, POP_SIZE=200
4. **Profiling**: Use `cProfile` to identify remaining bottlenecks

## Configuration Changes

**Add to `config/ga_params.py`**:
```python
# Parallelization settings
USE_MULTIPROCESSING = True  # Toggle for debugging
NUM_WORKERS = None  # None = CPU count, or specify manually
```

## Implementation Checklist

- [ ] Add `if __name__ == "__main__"` to main.py
- [ ] Create multiprocessing Pool in main.py
- [ ] Pass Pool through workflow → GAScheduler
- [ ] Register pool.map in GAScheduler.setup_toolbox()
- [ ] Test on small run (NGEN=10, POP_SIZE=20)
- [ ] Verify same results with/without parallelization
- [ ] Benchmark speedup on full run
- [ ] Add USE_MULTIPROCESSING config flag
- [ ] Document in README.md
- [ ] Update requirements.txt (no new deps needed)

## Performance Targets

| Configuration | Current (est.) | Target (parallel) | Speedup |
|---------------|----------------|-------------------|---------|
| Small (N=10, P=20) | ~30s | ~10s | 3× |
| Medium (N=100, P=50) | ~5min | ~1.5min | 3-4× |
| Full (N=1000, P=100) | ~50min | ~12min | 4-5× |

*Assumes 8-core CPU, actual varies by hardware*

## Why NOT Full Parallelization

**Mutation/Crossover**: Too fast, overhead > gain
**Selection**: Algorithm inherently sequential (sorting)
**Population init**: One-time cost, not worth complexity

**Key Insight**: GA evaluation is 80-90% of runtime → focus there.

## Future Considerations

- If evaluation still slow: Profile constraint functions, optimize hotspots
- If need distributed: SCOOP for cluster computing
- If memory constrained: Batch evaluation, process subsets
- GPU acceleration: Unlikely to help (constraint logic not vectorizable)

## References

- DEAP Parallelization: https://deap.readthedocs.io/en/master/tutorials/basic/part4.html
- Python multiprocessing: https://docs.python.org/3/library/multiprocessing.html
- Pickling limitations: https://docs.python.org/3/library/pickle.html#what-can-be-pickled-and-unpickled
