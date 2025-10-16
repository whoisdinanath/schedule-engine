# Codebase Refactoring Analysis & Action Plan

**Date:** October 16, 2025  
**Status:** 36 Python files, ~165 KB codebase  
**Architecture:** GA-based NSGA-II scheduler with quantum time system

---

## 🔴 Critical Issues

### 1. **Monolithic `main.py` (342 lines)**
**Problem:** Single file orchestrating everything—data loading, GA setup, evaluation loop, plotting, exports.  
**Impact:** Hard to test, maintain, debug. No entry points for experimentation.  
**Fix Priority:** HIGH

### 2. **God Module: `population.py` (758 lines)**
**Problem:** Handles population generation, seeding logic, constraint-aware initialization, conflict avoidance, helper utilities—all mixed together.  
**Impact:** Impossible to understand without reading entire file. Functions like `create_session_gene_with_conflict_avoidance` are deeply nested.  
**Fix Priority:** CRITICAL

### 3. **Circular Import Risk**
**Problem:** Many cross-dependencies between `src.ga.*`, `src.entities.*`, `src.constraints.*`. Example: `fitness.py` imports from `decoder`, `constraints`, `entities`.  
**Impact:** Fragile import structure; refactoring one module breaks others.  
**Fix Priority:** HIGH

### 4. **No Service Layer / Business Logic Separation**
**Problem:** GA logic, constraint checking, data encoding, and I/O are tightly coupled.  
**Impact:** Can't swap constraint implementations, test GA operators in isolation, or reuse modules.  
**Fix Priority:** HIGH

### 5. **Config Sprawl**
**Problem:** 6 config files (`constraints.py`, `ga_params.py`, `time_config.py`, `calendar_config.py`, `color_palette.py`, `io_paths.py`) with overlapping concerns.  
**Impact:** Hard to locate settings; no validation layer.  
**Fix Priority:** MEDIUM

### 6. **Inconsistent Abstraction Levels**
**Problem:** High-level GA loop in `main.py` directly manipulates low-level gene structures. Mutation/crossover operators access raw context dicts.  
**Impact:** Leaky abstractions; hard to reason about system boundaries.  
**Fix Priority:** MEDIUM

---

## 📊 Architectural Issues

### A. **Lack of Layers**
Current structure is flat:
```
main.py → calls everything directly
    ├── src/encoder/*.py  (data loading)
    ├── src/ga/*.py       (population, operators, evaluation)
    ├── src/constraints/*.py
    ├── src/decoder/*.py
    └── src/exporter/*.py
```

**Missing layers:**
- **Application Layer** (orchestration, workflows)
- **Service Layer** (business logic boundaries)
- **Repository Layer** (data access abstraction)

### B. **God Objects & Functions**
- `generate_course_group_aware_population()` does too much
- `context` dict is passed everywhere (poor encapsulation)
- `evaluate_detailed()` returns dicts instead of typed results

### C. **No Dependency Injection**
Hard-coded dependencies make testing impossible:
```python
# In main.py - directly creates everything
courses = load_courses("data/Course.json")  # hardcoded path
toolbox.register("evaluate", evaluate, courses=courses, ...)  # tight coupling
```

---

## 🛠️ Refactoring Strategy

### Phase 1: Extract Entry Points (Week 1)
**Goal:** Break `main.py` into manageable pieces.

#### Actions:
1. **Create `src/core/scheduler.py`**
   - Extract GA loop into `GAScheduler` class
   - Methods: `setup()`, `run()`, `select_best()`
   - Owns: population, toolbox, metrics tracking

2. **Create `src/workflows/standard_run.py`**
   - Orchestration logic from `main.py`
   - Steps: load data → initialize GA → run → export
   - Entry point: `run_standard_workflow()`

3. **Create `src/workflows/experiment_runner.py`**
   - For hyperparameter tuning, ablation studies
   - Supports multiple runs with config variations

4. **Slim `main.py` to ~50 lines:**
```python
# main.py (after refactor)
from src.workflows.standard_run import run_standard_workflow
from config.ga_params import POP_SIZE, NGEN

if __name__ == "__main__":
    run_standard_workflow(
        pop_size=POP_SIZE,
        generations=NGEN,
        output_dir="output"
    )
```

---

### Phase 2: Modularize Population Logic (Week 2)
**Goal:** Break down `population.py` into focused modules.

#### New Structure:
```
src/ga/
├── seeding/
│   ├── seeder.py                   # CourseGroupSeeder class
│   ├── conflict_tracker.py         # ConflictTracker class
│   ├── quanta_allocator.py         # QuantaAllocator class
│   └── gene_factory.py             # SessionGeneFactory class
├── operators/
│   ├── crossover.py                # existing
│   ├── mutation.py                 # existing
│   └── selection.py                # NSGA-II wrapper
├── population.py                   # Simplified coordinator
└── ...
```

#### Classes to Extract:
```python
class CourseGroupSeeder:
    """Generates constraint-aware initial population."""
    def seed(self, pairs, context) -> List[Individual]: ...

class ConflictTracker:
    """Tracks instructor/group/room schedules during seeding."""
    def is_conflicting(self, instructor, quanta) -> bool: ...
    
class QuantaAllocator:
    """Allocates time quanta with conflict avoidance."""
    def allocate(self, num_quanta, available, conflicts) -> List[int]: ...
```

**Benefits:**
- Each class has single responsibility
- Testable in isolation
- Reusable across different seeding strategies

---

### Phase 3: Service Layer (Week 3)
**Goal:** Create clean business logic boundaries.

#### Services to Implement:

**1. DataService**
```python
class DataService:
    def load_input_data(self, data_dir: str) -> InputData:
        """Loads and links all entities."""
        
    def validate_input(self, data: InputData) -> List[ValidationError]:
        """Validates loaded data for consistency."""
```

**2. ConstraintService**
```python
class ConstraintService:
    def __init__(self, config: ConstraintConfig):
        self.hard_constraints = load_hard_constraints(config)
        self.soft_constraints = load_soft_constraints(config)
    
    def evaluate(self, sessions: List[CourseSession]) -> ConstraintResult:
        """Returns typed result, not dicts."""
```

**3. SchedulerService**
```python
class SchedulerService:
    def __init__(self, ga_config, constraint_service, data_service):
        ...
    
    def create_schedule(self) -> ScheduleResult:
        """Runs GA and returns best solution."""
```

**Benefits:**
- Clear API contracts
- Easy to mock for testing
- Swap implementations without breaking callers

---

### Phase 4: Configuration Management (Week 4)

#### Consolidate Configs:
```python
# config/settings.py (unified)
from pydantic import BaseModel

class GAConfig(BaseModel):
    pop_size: int = 50
    generations: int = 100
    crossover_prob: float = 0.7
    mutation_prob: float = 0.2

class ConstraintConfig(BaseModel):
    hard_constraints: Dict[str, ConstraintSetting]
    soft_constraints: Dict[str, ConstraintSetting]

class AppConfig(BaseModel):
    ga: GAConfig
    constraints: ConstraintConfig
    time: TimeConfig
    io: IOConfig
```

**Benefits:**
- Type validation with pydantic
- Single source of truth
- Environment-specific configs (dev/prod)

---

### Phase 5: Dependency Injection (Week 5)

#### Use Dependency Injector:
```python
# src/di_container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Data Layer
    data_service = providers.Singleton(
        DataService,
        qts=providers.Singleton(QuantumTimeSystem)
    )
    
    # Constraint Layer
    constraint_service = providers.Singleton(
        ConstraintService,
        config=config.constraints
    )
    
    # GA Layer
    scheduler_service = providers.Factory(
        SchedulerService,
        ga_config=config.ga,
        constraint_service=constraint_service,
        data_service=data_service
    )
```

**Benefits:**
- Testable (inject mocks)
- Flexible (swap implementations)
- Clear dependencies

---

## 📁 Target Architecture

```
schedule-engine/
├── main.py                         # Slim entry point
├── config/
│   ├── settings.py                 # Unified config with pydantic
│   └── defaults/                   # Default config files
├── src/
│   ├── core/                       # Core domain logic
│   │   ├── entities/               # Data classes
│   │   ├── time_system.py          # QuantumTimeSystem
│   │   └── types.py                # Type definitions
│   ├── services/                   # Business logic
│   │   ├── data_service.py
│   │   ├── constraint_service.py
│   │   └── scheduler_service.py
│   ├── ga/                         # GA implementation
│   │   ├── operators/
│   │   ├── seeding/
│   │   ├── evaluator/
│   │   └── scheduler.py            # GAScheduler class
│   ├── constraints/                # Constraint implementations
│   ├── io/                         # I/O adapters
│   │   ├── loaders/
│   │   └── exporters/
│   ├── workflows/                  # Use case orchestration
│   │   ├── standard_run.py
│   │   └── experiment_runner.py
│   └── di_container.py             # Dependency injection
├── test/                           # Tests mirror src/
└── docs/
```

---

## 🎯 Quick Wins (This Week)

### 1. **Extract GAScheduler Class** (2 hours)
Move GA loop from `main.py` into `src/core/scheduler.py`.

### 2. **Create Workflow Module** (1 hour)
Extract orchestration logic into `src/workflows/standard_run.py`.

### 3. **Type Hint Missing Functions** (1 hour)
Add return types to all public functions in `src/ga/`.

### 4. **Add Input Validation** (2 hours)
Create `DataService.validate_input()` to catch bad data early.

### 5. **Extract ConflictTracker** (3 hours)
Pull conflict tracking logic out of `population.py` into dedicated class.

---

## 🧪 Testing Strategy

### Current State:
- **Zero unit tests** in `test/`
- Only `test_thesis_style.py` (plotting test)

### Refactoring Testing:
1. **Characterization Tests First**
   - Run current system, capture outputs
   - Compare after each refactor step

2. **Service-Level Tests**
   - Mock dependencies
   - Test business logic in isolation

3. **Integration Tests**
   - End-to-end workflow tests
   - Validate GA produces valid schedules

### Target Coverage:
- Core services: 80%
- GA operators: 70%
- Constraints: 90% (critical logic)

---

## 📏 Code Quality Metrics

### Current Issues:
- **Cyclomatic Complexity:** `population.py` functions exceed 20
- **Function Length:** Many functions >100 lines
- **Import Count:** Some files import from 10+ modules

### Targets After Refactor:
- Max function complexity: 10
- Max function length: 50 lines
- Max imports per file: 7
- Max file length: 300 lines

---

## 🚀 Migration Path

### Step-by-Step:
1. **Freeze Current Behavior** (create reference outputs)
2. **Extract GAScheduler** (no behavior change)
3. **Run regression tests**
4. **Extract Workflows** (no behavior change)
5. **Run regression tests**
6. **Continue iteratively...**

### Risk Mitigation:
- **Branch per phase** (`refactor/phase-1-entry-points`)
- **Keep `main.py` working** until all phases complete
- **Run benchmark suite** after each merge

---

## 📝 Implementation Checklist

### Phase 1: Entry Points
- [ ] Create `src/core/scheduler.py`
- [ ] Create `src/workflows/standard_run.py`
- [ ] Extract plotting logic into `src/workflows/plot_results.py`
- [ ] Slim `main.py` to <50 lines
- [ ] Add docstrings to all new modules

### Phase 2: Population Refactor
- [ ] Create `src/ga/seeding/` package
- [ ] Extract `ConflictTracker` class
- [ ] Extract `QuantaAllocator` class
- [ ] Extract `SessionGeneFactory` class
- [ ] Create `CourseGroupSeeder` coordinator
- [ ] Update `population.py` to use new classes
- [ ] Add unit tests for each new class

### Phase 3: Services
- [ ] Create `src/services/` package
- [ ] Implement `DataService`
- [ ] Implement `ConstraintService`
- [ ] Implement `SchedulerService`
- [ ] Update workflows to use services
- [ ] Add integration tests

### Phase 4: Config
- [ ] Install pydantic
- [ ] Create `config/settings.py`
- [ ] Migrate all config files
- [ ] Add validation schemas
- [ ] Update code to use new config

### Phase 5: DI
- [ ] Install dependency-injector
- [ ] Create `src/di_container.py`
- [ ] Wire up all services
- [ ] Update main.py to use container
- [ ] Add DI examples to docs

---

## 💡 Key Principles

1. **SOLID Principles**
   - Single Responsibility: Each class does one thing
   - Open/Closed: Extend behavior without modifying existing code
   - Liskov Substitution: Use interfaces/protocols
   - Interface Segregation: Small, focused interfaces
   - Dependency Inversion: Depend on abstractions

2. **Separation of Concerns**
   - I/O vs Business Logic vs Presentation
   - GA mechanics vs Domain constraints
   - Data structures vs Algorithms

3. **Testability First**
   - If it's hard to test, it's poorly designed
   - Mock external dependencies
   - Pure functions where possible

4. **Incremental Improvement**
   - Small, safe refactors
   - Always keep system working
   - Measure before/after

---

## 📚 References

- **Clean Architecture** (Robert Martin) - layered design
- **Refactoring** (Martin Fowler) - safe transformation techniques
- **Domain-Driven Design** (Eric Evans) - service boundaries
- **Effective Python** (Brett Slatkin) - Python best practices

---

## 🎓 Expected Outcomes

### Before Refactor:
- Hard to add features
- No tests
- Unclear where to start
- Fragile code

### After Refactor:
- Clear module boundaries
- 70%+ test coverage
- Easy to extend constraints
- New developers can contribute
- Faster iteration cycles

**Estimated Total Time:** 5-6 weeks (part-time)  
**Immediate ROI:** Week 3 (when services stabilize)
