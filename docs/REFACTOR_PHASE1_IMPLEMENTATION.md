# Phase 1 Implementation Guide: Extract Entry Points

**Goal:** Break monolithic `main.py` into testable, modular components  
**Timeline:** 1 week  
**Risk:** LOW (minimal logic changes)

---

## Overview

Current `main.py` responsibilities (342 lines):
1. Data loading & linking
2. GA toolbox setup
3. Population validation
4. GA execution loop
5. Metrics tracking
6. Plotting results
7. Exporting schedules

**After Phase 1**, these become:
- `main.py` (50 lines) → Entry point only
- `src/core/ga_scheduler.py` → GA execution
- `src/workflows/standard_run.py` → Orchestration
- `src/workflows/reporting.py` → Plotting/exports

---

## Step 1: Extract GAScheduler Class

### File: `src/core/ga_scheduler.py`

```python
"""
GA Scheduler Module

Encapsulates NSGA-II genetic algorithm execution for course scheduling.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from deap import base, tools
import random
from tqdm import tqdm

from src.ga.population import generate_course_group_aware_population
from src.ga.operators.crossover import crossover_course_group_aware
from src.ga.operators.mutation import mutate_individual
from src.ga.evaluator.fitness import evaluate
from src.ga.evaluator.detailed_fitness import evaluate_detailed
from src.metrics.diversity import average_pairwise_diversity


@dataclass
class GAConfig:
    """GA configuration parameters."""
    pop_size: int
    generations: int
    crossover_prob: float
    mutation_prob: float


@dataclass
class GAMetrics:
    """Tracks GA evolution metrics per generation."""
    hard_violations: List[float] = field(default_factory=list)
    soft_penalties: List[float] = field(default_factory=list)
    diversity: List[float] = field(default_factory=list)
    detailed_hard: Dict[str, List[float]] = field(default_factory=dict)
    detailed_soft: Dict[str, List[float]] = field(default_factory=dict)


class GAScheduler:
    """
    Manages NSGA-II genetic algorithm execution for timetabling.
    
    Responsibilities:
    - Initialize DEAP toolbox
    - Run evolution loop
    - Track metrics
    - Select best solutions
    """
    
    def __init__(
        self,
        config: GAConfig,
        context: Dict,
        hard_constraint_names: List[str],
        soft_constraint_names: List[str]
    ):
        self.config = config
        self.context = context
        self.hard_constraint_names = hard_constraint_names
        self.soft_constraint_names = soft_constraint_names
        
        self.toolbox = None
        self.population = None
        self.metrics = GAMetrics(
            detailed_hard={name: [] for name in hard_constraint_names},
            detailed_soft={name: [] for name in soft_constraint_names}
        )
    
    def setup_toolbox(self):
        """Initialize DEAP toolbox with operators."""
        self.toolbox = base.Toolbox()
        
        # Selection
        self.toolbox.register("select", tools.selNSGA2)
        
        # Population generation
        self.toolbox.register(
            "individual",
            generate_course_group_aware_population,
            n=1,
            context=self.context
        )
        self.toolbox.register(
            "population",
            generate_course_group_aware_population,
            context=self.context
        )
        
        # Evaluation
        self.toolbox.register(
            "evaluate",
            evaluate,
            courses=self.context["courses"],
            instructors=self.context["instructors"],
            groups=self.context["groups"],
            rooms=self.context["rooms"]
        )
        
        # Genetic operators
        self.toolbox.register(
            "mate",
            crossover_course_group_aware,
            cx_prob=self.config.crossover_prob
        )
        self.toolbox.register(
            "mutate",
            mutate_individual,
            context=self.context,
            mut_prob=self.config.mutation_prob
        )
    
    def initialize_population(self):
        """Create and evaluate initial population."""
        print(f"Generating population of size {self.config.pop_size}...")
        self.population = self.toolbox.population(n=self.config.pop_size)
        
        # Validate gene alignment
        self._validate_population_structure()
        
        # Evaluate
        print("Evaluating initial population...")
        fitness_values = list(map(
            self.toolbox.evaluate,
            tqdm(self.population, desc="Initial Eval", leave=False)
        ))
        for ind, fit in zip(self.population, fitness_values):
            ind.fitness.values = fit
    
    def evolve(self):
        """Run genetic algorithm evolution loop."""
        for gen in tqdm(range(self.config.generations), desc="GA Progress", unit="gen"):
            self._evolve_generation(gen)
            
            # Early stopping
            best = tools.selBest(self.population, 1)[0]
            if best.fitness.values[0] == 0:
                tqdm.write(f"✓ Perfect solution found at generation {gen + 1}!")
                break
    
    def _evolve_generation(self, gen: int):
        """Execute one generation of evolution."""
        # Selection
        offspring = self.toolbox.select(self.population, len(self.population))
        offspring = list(map(self.toolbox.clone, offspring))
        
        # Crossover
        for i in range(1, len(offspring), 2):
            if random.random() < self.config.crossover_prob:
                self.toolbox.mate(offspring[i - 1], offspring[i])
                del offspring[i - 1].fitness.values
                del offspring[i].fitness.values
        
        # Mutation
        for mutant in offspring:
            if random.random() < self.config.mutation_prob:
                self.toolbox.mutate(mutant)
                del mutant.fitness.values
        
        # Evaluate invalid individuals
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        fitness_values = list(map(
            self.toolbox.evaluate,
            tqdm(
                invalid,
                desc=f"Gen {gen+1} Eval",
                leave=False,
                disable=len(invalid) == 0
            )
        ))
        for ind, fit in zip(invalid, fitness_values):
            ind.fitness.values = fit
        
        # Replacement
        combined = self.population + offspring
        self.population[:] = self.toolbox.select(combined, len(self.population))
        
        # Track metrics
        self._track_metrics(gen)
    
    def _track_metrics(self, gen: int):
        """Record metrics for current generation."""
        # Basic metrics
        self.metrics.hard_violations.append(
            min(ind.fitness.values[0] for ind in self.population)
        )
        self.metrics.soft_penalties.append(
            min(ind.fitness.values[1] for ind in self.population)
        )
        self.metrics.diversity.append(
            average_pairwise_diversity(self.population)
        )
        
        # Detailed constraint breakdown
        best = tools.selBest(self.population, 1)[0]
        hard_details, soft_details = evaluate_detailed(
            best,
            self.context["courses"],
            self.context["instructors"],
            self.context["groups"],
            self.context["rooms"]
        )
        
        for name in self.hard_constraint_names:
            self.metrics.detailed_hard[name].append(hard_details[name])
        
        for name in self.soft_constraint_names:
            self.metrics.detailed_soft[name].append(soft_details[name])
        
        # Logging
        if gen % 10 == 0 or gen == self.config.generations - 1:
            self._log_generation_details(gen, best, hard_details, soft_details)
    
    def _log_generation_details(self, gen, best, hard_details, soft_details):
        """Print detailed constraint breakdown."""
        tqdm.write(
            f"Gen {gen+1}: Hard={best.fitness.values[0]:.0f}, "
            f"Soft={best.fitness.values[1]:.2f}"
        )
        
        tqdm.write(f"  [HARD] Total: {best.fitness.values[0]:.0f}")
        for name, value in hard_details.items():
            if value > 0:
                tqdm.write(f"    - {name}: {value}")
        
        tqdm.write(f"  [SOFT] Total: {best.fitness.values[1]:.2f}")
        for name, value in soft_details.items():
            if value > 0:
                tqdm.write(f"    - {name}: {value}")
    
    def get_best_solution(self):
        """Select best solution from final population."""
        pareto_front = tools.sortNondominated(
            self.population,
            len(self.population),
            first_front_only=True
        )[0]
        
        # Prefer feasible solutions
        feasible = [ind for ind in pareto_front if ind.fitness.values[0] == 0]
        
        if feasible:
            return min(feasible, key=lambda ind: ind.fitness.values[1])
        else:
            return pareto_front[0]
    
    def _validate_population_structure(self):
        """Validate gene alignment across population."""
        if not self.population:
            return
        
        reference = [
            (gene.course_id, tuple(sorted(gene.group_ids)))
            for gene in self.population[0]
        ]
        reference_set = set(reference)
        
        for idx, individual in enumerate(self.population[1:], start=1):
            current = [
                (gene.course_id, tuple(sorted(gene.group_ids)))
                for gene in individual
            ]
            current_set = set(current)
            
            if current_set != reference_set:
                raise ValueError(
                    f"Gene alignment validation FAILED! "
                    f"Individual {idx} has different structure."
                )
```

**Key Improvements:**
- **Encapsulation:** All GA logic in one class
- **Configuration:** Type-safe `GAConfig` dataclass
- **Metrics:** Structured `GAMetrics` instead of raw lists
- **Testable:** Can mock dependencies easily

---

## Step 2: Extract Workflow Orchestration

### File: `src/workflows/standard_run.py`

```python
"""
Standard Workflow Module

Orchestrates full scheduling pipeline: load → schedule → export.
"""

import os
from datetime import datetime
from typing import Dict, Optional

from src.encoder.input_encoder import (
    load_courses,
    load_groups,
    load_instructors,
    load_rooms,
    link_courses_and_groups,
    link_courses_and_instructors
)
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.decoder.individual_decoder import decode_individual
from src.core.ga_scheduler import GAScheduler, GAConfig
from src.workflows.reporting import generate_reports
from config.constraints import HARD_CONSTRAINTS_CONFIG, SOFT_CONSTRAINTS_CONFIG


def run_standard_workflow(
    pop_size: int,
    generations: int,
    crossover_prob: float = 0.7,
    mutation_prob: float = 0.2,
    data_dir: str = "data",
    output_dir: Optional[str] = None,
    seed: int = 69
) -> Dict:
    """
    Execute standard GA scheduling workflow.
    
    Args:
        pop_size: Population size
        generations: Number of GA generations
        crossover_prob: Crossover probability
        mutation_prob: Mutation probability
        data_dir: Input data directory
        output_dir: Output directory (auto-generated if None)
        seed: Random seed for reproducibility
    
    Returns:
        Dict containing:
            - best_individual: Best solution found
            - decoded_schedule: Decoded schedule
            - metrics: GA evolution metrics
            - output_path: Path to results
    """
    
    # Setup
    import random
    random.seed(seed)
    
    if output_dir is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = os.path.join("output", f"evaluation_{timestamp}")
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Output directory: {output_dir}")
    
    # Load data
    print("\n=== Loading Input Data ===")
    qts = QuantumTimeSystem()
    context = load_input_data(data_dir, qts)
    
    # Configure GA
    ga_config = GAConfig(
        pop_size=pop_size,
        generations=generations,
        crossover_prob=crossover_prob,
        mutation_prob=mutation_prob
    )
    
    # Get constraint names for tracking
    hard_names = [
        name for name, cfg in HARD_CONSTRAINTS_CONFIG.items()
        if cfg["enabled"]
    ]
    soft_names = [
        name for name, cfg in SOFT_CONSTRAINTS_CONFIG.items()
        if cfg["enabled"]
    ]
    
    # Run GA
    print("\n=== Running Genetic Algorithm ===")
    scheduler = GAScheduler(ga_config, context, hard_names, soft_names)
    scheduler.setup_toolbox()
    scheduler.initialize_population()
    scheduler.evolve()
    
    # Get results
    best_individual = scheduler.get_best_solution()
    decoded_schedule = decode_individual(
        best_individual,
        context["courses"],
        context["instructors"],
        context["groups"],
        context["rooms"]
    )
    
    print(f"\n=== Best Solution ===")
    print(f"Hard Violations: {best_individual.fitness.values[0]:.0f}")
    print(f"Soft Penalty: {best_individual.fitness.values[1]:.2f}")
    
    # Generate reports
    print("\n=== Generating Reports ===")
    generate_reports(
        decoded_schedule=decoded_schedule,
        metrics=scheduler.metrics,
        population=scheduler.population,
        qts=qts,
        output_dir=output_dir
    )
    
    print(f"\n✓ Complete! Results saved to: {output_dir}")
    
    return {
        "best_individual": best_individual,
        "decoded_schedule": decoded_schedule,
        "metrics": scheduler.metrics,
        "output_path": output_dir
    }


def load_input_data(data_dir: str, qts: QuantumTimeSystem) -> Dict:
    """Load and link all input entities."""
    courses = load_courses(os.path.join(data_dir, "Course.json"))
    groups = load_groups(os.path.join(data_dir, "Groups.json"), qts)
    instructors = load_instructors(os.path.join(data_dir, "Instructors.json"), qts)
    rooms = load_rooms(os.path.join(data_dir, "Rooms.json"), qts)
    
    link_courses_and_groups(courses, groups)
    link_courses_and_instructors(courses, instructors)
    
    return {
        "courses": courses,
        "groups": groups,
        "instructors": instructors,
        "rooms": rooms,
        "available_quanta": qts.get_all_operating_quanta()
    }
```

---

## Step 3: Extract Reporting Logic

### File: `src/workflows/reporting.py`

```python
"""
Reporting Workflow Module

Handles plotting and export of GA results.
"""

from typing import List, Dict
from src.entities.decoded_session import CourseSession
from src.encoder.quantum_time_system import QuantumTimeSystem
from src.core.ga_scheduler import GAMetrics
from src.exporter.exporter import export_everything
from src.exporter.plotdiversity import plot_diversity_trend
from src.exporter.plothard import plot_hard_constraint_violation_over_generation
from src.exporter.plotsoft import plot_soft_constraint_violation_over_generation
from src.exporter.plotpareto import plot_pareto_front
from src.exporter.plot_detailed_constraints import (
    plot_individual_hard_constraints,
    plot_individual_soft_constraints,
    plot_constraint_summary
)


def generate_reports(
    decoded_schedule: List[CourseSession],
    metrics: GAMetrics,
    population: List,
    qts: QuantumTimeSystem,
    output_dir: str
):
    """
    Generate all output artifacts: plots, JSON, PDFs.
    
    Args:
        decoded_schedule: Best schedule solution
        metrics: GA evolution metrics
        population: Final population (for Pareto front)
        qts: Quantum time system
        output_dir: Output directory path
    """
    
    # Export schedule
    print("Exporting schedule...")
    export_everything(decoded_schedule, output_dir, qts)
    
    # Plot evolution trends
    print("Generating evolution plots...")
    plot_hard_constraint_violation_over_generation(
        metrics.hard_violations,
        output_dir
    )
    plot_soft_constraint_violation_over_generation(
        metrics.soft_penalties,
        output_dir
    )
    plot_diversity_trend(metrics.diversity, output_dir)
    
    # Plot Pareto front
    print("Generating Pareto front plot...")
    plot_pareto_front(population, output_dir)
    
    # Plot detailed constraints
    print("Generating detailed constraint plots...")
    plot_individual_hard_constraints(metrics.detailed_hard, output_dir)
    plot_individual_soft_constraints(metrics.detailed_soft, output_dir)
    plot_constraint_summary(metrics.detailed_hard, metrics.detailed_soft, output_dir)
    
    print(f"All reports saved to: {output_dir}")
```

---

## Step 4: Refactor main.py

### File: `main.py` (after refactor)

```python
"""
Schedule Engine Entry Point

Runs standard GA-based course scheduling workflow.
"""

from src.workflows.standard_run import run_standard_workflow
from config.ga_params import POP_SIZE, NGEN, CXPB, MUTPB


def main():
    """Execute standard scheduling workflow."""
    result = run_standard_workflow(
        pop_size=POP_SIZE,
        generations=NGEN,
        crossover_prob=CXPB,
        mutation_prob=MUTPB
    )
    
    print(f"\nFinal Fitness: {result['best_individual'].fitness.values}")
    print(f"Results: {result['output_path']}")


if __name__ == "__main__":
    main()
```

**Result:** `main.py` reduced from 342 → 23 lines!

---

## Testing Strategy

### 1. Characterization Tests
Before refactoring, capture current outputs:

```python
# test/test_characterization.py
import json
from main import main  # old version

def test_capture_baseline():
    """Run old system and save outputs for comparison."""
    # Run with fixed seed
    result = main()  # modify to return result
    
    # Save schedule JSON
    with open("test/baseline_schedule.json", "w") as f:
        json.dump(result["schedule"], f)
    
    # Save metrics
    with open("test/baseline_metrics.json", "w") as f:
        json.dump(result["metrics"], f)
```

### 2. Regression Tests
After refactoring:

```python
# test/test_regression.py
from src.workflows.standard_run import run_standard_workflow
import json

def test_refactored_matches_baseline():
    """Ensure refactored code produces same results."""
    result = run_standard_workflow(
        pop_size=10,
        generations=5,
        seed=42
    )
    
    # Load baseline
    with open("test/baseline_schedule.json") as f:
        baseline = json.load(f)
    
    # Compare (allow minor float differences)
    assert len(result["decoded_schedule"]) == len(baseline["sessions"])
    # ... detailed comparisons
```

### 3. Unit Tests

```python
# test/test_ga_scheduler.py
from src.core.ga_scheduler import GAScheduler, GAConfig

def test_scheduler_initialization():
    """Test GAScheduler setup."""
    config = GAConfig(pop_size=10, generations=5, crossover_prob=0.7, mutation_prob=0.2)
    # ... test initialization

def test_scheduler_metrics_tracking():
    """Test metrics are recorded correctly."""
    # ... test metrics collection
```

---

## Migration Checklist

- [ ] Create `src/core/` package
- [ ] Create `src/workflows/` package
- [ ] Implement `GAScheduler` class
- [ ] Implement `standard_run.py`
- [ ] Implement `reporting.py`
- [ ] Run characterization test (capture baseline)
- [ ] Refactor `main.py`
- [ ] Run regression test (compare with baseline)
- [ ] Add unit tests for `GAScheduler`
- [ ] Update documentation
- [ ] Create PR: "Phase 1: Extract entry points"

---

## Rollback Plan

If refactor breaks:
1. Revert to pre-refactor commit
2. Identify broken test
3. Fix in isolated branch
4. Re-run full test suite
5. Merge when green

---

## Next Steps

After Phase 1 completion:
- **Phase 2:** Refactor `population.py` into modular seeding classes
- **Phase 3:** Create service layer for business logic
- **Phase 4:** Consolidate configuration with pydantic
