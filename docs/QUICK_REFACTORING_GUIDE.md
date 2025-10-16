# Quick Refactoring Guide: Immediate Actions

**Priority:** Fix the mess NOW  
**Time:** 4-6 hours for critical fixes

---

## 🔥 Critical Issues (Fix Today)

### 1. Giant `population.py` (758 lines)

**Problem:** One file does everything—seeding, conflict tracking, quanta allocation.

**Quick Fix:**
```python
# Create these files:
src/ga/seeding/
├── __init__.py
├── conflict_tracker.py      # Extract lines 449-493 (assign_conflict_free_quanta)
├── quanta_allocator.py      # Extract lines 662-697 (assign_intelligent_quanta)
└── gene_factory.py          # Extract lines 260-353 (create_session_gene_with_conflict_avoidance)
```

**Action:**
1. Copy functions to new files
2. Add imports to `population.py`
3. Test—should work identically

---

### 2. Monolithic `main.py` (342 lines)

**Problem:** Can't test anything in isolation.

**Quick Fix:**
```python
# Extract GA loop into class
# src/core/ga_scheduler.py

class GAScheduler:
    def __init__(self, config, context):
        self.config = config
        self.context = context
    
    def run(self):
        # Move lines 90-310 from main.py here
        ...
```

**Action:**
1. Create `GAScheduler` class
2. Move GA loop code
3. Update `main.py` to call `scheduler.run()`

---

### 3. Context Dict Everywhere

**Problem:** `context` dict passed to 20+ functions—hard to track what's needed.

**Quick Fix:**
```python
# src/core/types.py
from dataclasses import dataclass
from typing import Dict

@dataclass
class SchedulingContext:
    """Type-safe context for GA operations."""
    courses: Dict
    groups: Dict
    instructors: Dict
    rooms: Dict
    available_quanta: List[int]
```

**Action:**
1. Create `SchedulingContext` dataclass
2. Replace `context: Dict` with `context: SchedulingContext`
3. Use `context.courses` instead of `context["courses"]`

---

### 4. No Input Validation

**Problem:** Bad input data crashes GA 50 generations in.

**Quick Fix:**
```python
# src/validation/input_validator.py

def validate_input_data(courses, groups, instructors, rooms):
    """Validate input before GA runs."""
    errors = []
    
    # Check required relationships
    for course_id, course in courses.items():
        if not course.qualified_instructor_ids:
            errors.append(f"Course {course_id} has no qualified instructors")
    
    for group_id, group in groups.items():
        if not group.enrolled_courses:
            errors.append(f"Group {group_id} has no enrolled courses")
    
    if errors:
        raise ValueError(f"Input validation failed:\n" + "\n".join(errors))
    
    return True
```

**Action:**
1. Create validator module
2. Call in `main.py` before GA setup
3. Fail fast with clear error messages

---

### 5. Magic Numbers Everywhere

**Problem:** Constants like `0.7`, `0.3` scattered in code.

**Quick Fix:**
```python
# config/ga_params.py (add these)

# Mutation probabilities
KEEP_QUALIFIED_INSTRUCTOR_PROB = 0.7
KEEP_SUITABLE_ROOM_PROB = 0.5
KEEP_TIME_SLOTS_PROB = 0.3

# Seeding probabilities
PREFER_CONSECUTIVE_QUANTA = True
MAX_CONFLICT_RETRIES = 10
```

**Action:**
1. Find all magic numbers: `grep -r "0\.[0-9]" src/ga/`
2. Move to config
3. Replace with named constants

---

## 🛠️ Medium Priority (This Week)

### 6. Tight Coupling in Evaluators

**Problem:** `fitness.py` imports from 5+ modules.

**Quick Fix:**
```python
# src/ga/evaluator/constraint_evaluator.py

class ConstraintEvaluator:
    """Decouples constraint logic from GA."""
    
    def __init__(self, hard_constraints, soft_constraints):
        self.hard = hard_constraints
        self.soft = soft_constraints
    
    def evaluate(self, sessions):
        hard_score = sum(fn(sessions) for fn in self.hard.values())
        soft_score = sum(fn(sessions) for fn in self.soft.values())
        return (hard_score, soft_score)
```

**Action:**
1. Create evaluator class
2. Pass constraint functions in constructor
3. Use in `fitness.py`

---

### 7. Duplicate Code in Plotters

**Problem:** 6 plot files with near-identical structure.

**Quick Fix:**
```python
# src/exporter/plot_base.py

def create_evolution_plot(data, ylabel, title, output_path):
    """Base function for evolution plots."""
    from .thesis_style import create_thesis_figure, save_figure
    
    fig, ax = create_thesis_figure(figsize=(10, 6))
    ax.plot(range(len(data)), data, linewidth=2)
    ax.set_xlabel("Generation")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    save_figure(fig, output_path)
```

**Action:**
1. Extract common plotting logic
2. Rewrite plotters to use base function
3. Delete duplicate code

---

### 8. No Logging System

**Problem:** Using `print()` and `tqdm.write()` inconsistently.

**Quick Fix:**
```python
# src/utils/logger.py
import logging

def setup_logger(name="schedule-engine", level=logging.INFO):
    """Setup structured logging."""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Usage in main.py
from src.utils.logger import setup_logger
logger = setup_logger()

logger.info("Starting GA scheduler...")
logger.warning("No qualified instructors for course X")
logger.error("Population validation failed")
```

**Action:**
1. Replace all `print()` with `logger.info()`
2. Use log levels appropriately
3. Add file logging for long runs

---

## 📏 Code Quality Rules

### Enforce These Immediately:

1. **Max Function Length: 50 lines**
   - If longer → split into helper functions

2. **Max File Length: 300 lines**
   - If longer → split into modules

3. **Type Hints Required**
   ```python
   # BAD
   def evaluate(individual, courses, groups):
   
   # GOOD
   def evaluate(
       individual: List[SessionGene],
       courses: Dict[str, Course],
       groups: Dict[str, Group]
   ) -> Tuple[float, float]:
   ```

4. **Docstrings Required for Public Functions**
   ```python
   def mutate_gene(gene: SessionGene, context: SchedulingContext) -> SessionGene:
       """
       Mutates a single gene while preserving course-group structure.
       
       Args:
           gene: SessionGene to mutate
           context: Scheduling context with available resources
       
       Returns:
           Mutated SessionGene with same course_id and group_ids
       """
   ```

5. **No Deep Nesting (Max 3 Levels)**
   ```python
   # BAD
   if x:
       if y:
           if z:
               if w:
                   ...
   
   # GOOD - Early returns
   if not x:
       return
   if not y:
       return
   if not z:
       return
   ...
   ```

---

## 🧪 Testing Checklist

### Add These Tests TODAY:

```python
# test/test_critical_paths.py

def test_population_generation_deterministic():
    """Ensure same seed produces same population."""
    import random
    random.seed(42)
    pop1 = generate_population(n=10, context=test_context)
    
    random.seed(42)
    pop2 = generate_population(n=10, context=test_context)
    
    assert pop1[0].genes == pop2[0].genes

def test_mutation_preserves_structure():
    """Ensure mutation doesn't change course-group pairs."""
    original = create_test_gene(course="CS101", groups=["A"])
    mutated = mutate_gene(original, test_context)
    
    assert mutated.course_id == original.course_id
    assert mutated.group_ids == original.group_ids

def test_constraints_sum_correctly():
    """Ensure constraint weights are applied."""
    sessions = create_test_sessions()
    hard, soft = evaluate(sessions, ...)
    
    # Verify known violations produce expected scores
    assert hard == EXPECTED_HARD_SCORE
    assert soft == EXPECTED_SOFT_SCORE
```

---

## 🎯 Priority Order

### TODAY (4-6 hours):
1. ✅ Extract `ConflictTracker` from `population.py`
2. ✅ Create `SchedulingContext` dataclass
3. ✅ Add input validation
4. ✅ Replace magic numbers with config constants

### THIS WEEK (2-3 days):
5. ✅ Extract `GAScheduler` class
6. ✅ Create workflow orchestrator
7. ✅ Add logging system
8. ✅ Write critical tests

### NEXT WEEK (3-4 days):
9. ✅ Refactor constraint evaluator
10. ✅ Consolidate plotting code
11. ✅ Add type hints everywhere
12. ✅ Document all public APIs

---

## 🚨 Don't Do These (Common Mistakes)

❌ **Don't rewrite everything at once**  
✅ Refactor incrementally, keep tests passing

❌ **Don't change behavior during refactor**  
✅ Extract first, then improve

❌ **Don't skip tests**  
✅ Every refactor needs regression test

❌ **Don't optimize prematurely**  
✅ Fix structure first, performance later

❌ **Don't ignore warnings**  
✅ Treat warnings as errors

---

## 📊 Before/After Metrics

### Before Refactor:
- `population.py`: 758 lines
- `main.py`: 342 lines
- Test coverage: 0%
- Cyclomatic complexity: 25+ in key functions
- Import depth: 5-6 levels

### After Quick Fixes:
- `population.py`: ~400 lines (rest in `seeding/`)
- `main.py`: ~50 lines (rest in `workflows/`)
- Test coverage: 40%
- Cyclomatic complexity: <10 everywhere
- Import depth: 2-3 levels

---

## 🏁 Success Criteria

You'll know refactor worked when:

1. **New developer understands codebase in 1 hour** (not 1 day)
2. **Can add new constraint in 10 minutes** (not 2 hours)
3. **Tests run in <30 seconds**
4. **No "I don't know what this does" comments**
5. **Changes don't break unrelated code**

---

## 📞 Help

If stuck:
1. Commit current state
2. Create new branch
3. Try refactor
4. If fails, revert
5. Ask for code review before merge

**Remember:** Working code is better than perfect code!
