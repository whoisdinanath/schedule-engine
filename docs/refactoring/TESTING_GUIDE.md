# Testing Guide for Refactored Code

**Purpose:** Verify refactored code works correctly  
**Time Required:** 10-15 minutes

---

## Quick Test Checklist

### ✅ 1. Import Test (Already Done)
```bash
python -c "from src.core.types import SchedulingContext; from src.core.ga_scheduler import GAScheduler; from src.validation import InputValidator; from src.workflows import run_standard_workflow; print('✅ All imports successful!')"
```

**Expected:** ✅ All imports successful!  
**Status:** ✅ PASSED

---

### ✅ 2. Run New Version (Quick Test)
```bash
# Test with small parameters for speed
python -c "
from src.workflows import run_standard_workflow

# Quick test run (small population, few generations)
result = run_standard_workflow(
    pop_size=10,
    generations=5,
    validate=True,
    output_dir='output/test_refactored'
)

print('\n✅ Test completed successfully!')
print(f'Best fitness: {result[\"best_individual\"].fitness.values}')
"
```

**Expected:**
- No errors
- Output directory created
- Schedule generated
- Plots created

---

### ✅ 3. Compare with Original (Side-by-Side)

```bash
# Run original version
python main.py
# Output: output/evaluation_YYYYMMDD_HHMMSS/

# Note the output directory name, then run new version
python main_refactored.py
# Output: output/evaluation_YYYYMMDD_HHMMSS/

# Both should produce similar results
```

**What to Compare:**
- Both complete without errors ✅
- Similar fitness values ✅
- Similar number of sessions ✅
- Similar output structure ✅

---

### ✅ 4. Test Input Validation

```bash
python -c "
from src.core.types import SchedulingContext
from src.validation import validate_input

# Test with empty context (should fail)
empty_context = SchedulingContext(
    courses={},
    groups={},
    instructors={},
    rooms={},
    available_quanta=[]
)

print('Testing validation with empty data...')
result = validate_input(empty_context)
print(f'Validation failed as expected: {not result}')
"
```

**Expected:**
- Validation errors printed
- Function returns False

---

### ✅ 5. Test Type Safety

```bash
python -c "
from src.core.types import SchedulingContext

# Type hints should provide autocomplete
context = SchedulingContext(
    courses={},
    groups={},
    instructors={},
    rooms={},
    available_quanta=[]
)

# Access with autocomplete
print(f'Courses type: {type(context.courses)}')
print(f'Groups type: {type(context.groups)}')
print('✅ Type safety works!')
"
```

**Expected:**
- No errors
- Type information available

---

### ✅ 6. Test GAScheduler Independently

```bash
python -c "
from src.core.ga_scheduler import GAScheduler, GAConfig
from src.workflows import load_input_data

# Load data
qts, context = load_input_data('data/')

# Create scheduler
config = GAConfig(
    pop_size=10,
    generations=3,
    crossover_prob=0.7,
    mutation_prob=0.2
)

scheduler = GAScheduler(config, context, [], [])
scheduler.setup_toolbox()

print('✅ GAScheduler initialized successfully!')
print(f'Toolbox operators: {list(scheduler.toolbox.__dict__.keys())}')
"
```

**Expected:**
- Scheduler created
- Toolbox has operators (select, evaluate, mate, mutate)

---

## Full Integration Test

```bash
# Create test script
cat > test_refactored_full.py << 'EOF'
"""
Full integration test for refactored code.
"""

from src.workflows import run_standard_workflow

def test_full_workflow():
    """Test complete workflow with small parameters."""
    print("="*60)
    print("FULL INTEGRATION TEST")
    print("="*60)
    
    result = run_standard_workflow(
        pop_size=20,
        generations=10,
        validate=True,
        output_dir="output/integration_test"
    )
    
    # Verify result structure
    assert "best_individual" in result, "Missing best_individual"
    assert "decoded_schedule" in result, "Missing decoded_schedule"
    assert "metrics" in result, "Missing metrics"
    assert "output_path" in result, "Missing output_path"
    
    # Verify fitness
    fitness = result["best_individual"].fitness.values
    assert len(fitness) == 2, "Fitness should have 2 values (hard, soft)"
    assert fitness[0] >= 0, "Hard constraint violations should be >= 0"
    assert fitness[1] >= 0, "Soft constraint penalty should be >= 0"
    
    # Verify schedule
    schedule = result["decoded_schedule"]
    assert len(schedule) > 0, "Schedule should have sessions"
    
    # Verify metrics
    metrics = result["metrics"]
    assert len(metrics.hard_violations) > 0, "Should have metrics"
    
    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)
    print(f"Best Fitness: {fitness}")
    print(f"Schedule Size: {len(schedule)} sessions")
    print(f"Output: {result['output_path']}")

if __name__ == "__main__":
    test_full_workflow()
EOF

# Run test
python test_refactored_full.py
```

**Expected:**
```
============================================================
FULL INTEGRATION TEST
============================================================
[... workflow execution ...]
============================================================
✅ ALL TESTS PASSED!
============================================================
Best Fitness: (0, 5.2)
Schedule Size: 120 sessions
Output: output/integration_test
```

---

## Verification Checklist

After running all tests:

- [ ] All imports work
- [ ] New version runs without errors
- [ ] Validation catches bad input
- [ ] Type safety provides autocomplete
- [ ] GAScheduler can be instantiated
- [ ] Full workflow produces results
- [ ] Output directory created with files:
  - [ ] schedule.json
  - [ ] schedule.pdf
  - [ ] Evolution plots
  - [ ] Pareto front plot

---

## Troubleshooting

### Problem: Import Error
```
ImportError: No module named 'src.core'
```

**Solution:**
```bash
# Make sure you're in project root
cd c:\Users\krishna\Desktop\schedule-engine

# Check __init__.py files exist
ls src/core/__init__.py
ls src/validation/__init__.py
ls src/workflows/__init__.py
```

### Problem: DEAP Not Found
```
ModuleNotFoundError: No module named 'deap'
```

**Solution:**
```bash
# Activate conda environment
conda activate deap-env

# Verify DEAP installed
python -c "import deap; print(deap.__version__)"
```

### Problem: Data Files Missing
```
FileNotFoundError: [Errno 2] No such file or directory: 'data/Course.json'
```

**Solution:**
```bash
# Check data directory exists
ls data/Course.json
ls data/Groups.json
ls data/Instructors.json
ls data/Rooms.json

# If missing, you're in wrong directory
cd c:\Users\krishna\Desktop\schedule-engine
```

---

## Success Criteria

✅ All tests pass  
✅ No errors during execution  
✅ Output files generated  
✅ Similar results to original code  
✅ Validation works correctly  
✅ Type hints available

**If all criteria met:** Refactoring is successful! 🎉

---

## Next Steps After Successful Testing

1. **Run side-by-side comparison:**
   ```bash
   python main.py              # Original
   python main_refactored.py   # Refactored
   # Compare output directories
   ```

2. **Review code:**
   - Read new modules in `src/core/`, `src/validation/`, `src/workflows/`
   - Understand architecture changes

3. **Write unit tests:**
   - Test individual components
   - Target 70%+ coverage

4. **Switch to new version:**
   ```bash
   mv main.py main_legacy.py
   mv main_refactored.py main.py
   ```

5. **Start Phase 2:**
   - Refactor `population.py`
   - See `docs/REFACTORING_ANALYSIS.md`

---

## Questions?

- Check `docs/refactoring/COMPLETE_SUMMARY.md` for details
- Review individual refactoring docs
- Read inline code comments

**Happy Testing! 🚀**
