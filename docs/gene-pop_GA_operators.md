# GA Operators: Selection, Crossover, Mutation, Evaluation

## Overview

GA operators transform population through iterative improvement cycles. Each operator operates at different levels: gene-level, individual-level, or population-level.

**Operator Hierarchy:**
```
Population-level: Selection, Elitism
    ↓
Individual-level: Crossover, Cloning
    ↓
Gene-level: Mutation
    ↓
Evaluation: Fitness Assignment
```

---

## 1. Selection (Population → Parents)

**Operator:** `tools.selNSGA2` (DEAP NSGA-II)

**Purpose:** Choose parents for next generation based on multi-objective fitness.

**Level:** Population-level

**Input:** Current population (50 individuals)

**Output:** Selected parents (50 individuals, duplicates allowed)

### Mechanism

NSGA-II (Non-dominated Sorting Genetic Algorithm II) uses:

**Step 1: Non-dominated Sorting**
- Categorize individuals into Pareto fronts
- Front 1: Best individuals (no other individual dominates them on both objectives)
- Front 2: Dominated only by Front 1
- Front 3+: Progressive dominance levels

**Step 2: Crowding Distance**
- Within each front, calculate spacing between neighbors
- Rewards diversity: prefer individuals in less-crowded regions
- Prevents premature convergence to single solution

**Dominance Definition:**
Individual A dominates B if:
- A's hard violations ≤ B's hard violations AND
- A's soft penalties ≤ B's soft penalties AND
- At least one inequality is strict (<)

### Effect on Your Structures

**Gene:** No direct impact (selection doesn't modify genes)

**Individual/Chromosome:** 
- Better individuals (lower fitness values) selected more frequently
- Maintains diversity via crowding distance
- Duplicates possible (good solutions copied multiple times)

**Population:**
- Size remains constant (50 → 50)
- Composition shifts toward Pareto-optimal solutions
- Preserves multiple trade-off solutions (hard vs soft constraints)

### Parameters

- **Selection pressure:** Implicit (Pareto dominance + crowding)
- **Population size:** 50 (maintains constant)

**Rationale:** NSGA-II handles multi-objective optimization natively. No separate tournament selection needed (uses binary tournament internally for tie-breaking).

---

## 2. Cloning (Individual → Offspring)

**Operator:** `toolbox.clone` (DEAP deep copy)

**Purpose:** Create independent copies of selected individuals before modification.

**Level:** Individual-level

**Input:** Selected parent individual

**Output:** Deep copy of parent (separate memory)

### Mechanism

Creates exact duplicate with:
- Same gene list structure
- Same SessionGene values (course_id, instructor_id, group_id, room_id, quanta)
- Separate fitness object (initially shared, invalidated after mutation/crossover)

### Effect on Your Structures

**Gene:** Each `SessionGene` copied independently

**Individual/Chromosome:** 
- New list object with copied genes
- Prevents parent modification during crossover/mutation
- Fitness values initially copied, then invalidated if modified

**Population:**
- Offspring population created (50 clones)
- Parents preserved until next generation selection

**Critical:** Without cloning, crossover/mutation would corrupt parent population.

---

## 3. Crossover (Parent₁ + Parent₂ → Child₁ + Child₂)

**Operator:** `crossover_uniform` (custom implementation)

**Purpose:** Combine genetic material from two parents to create offspring.

**Level:** Individual-level (operates gene-by-gene)

**Input:** Two parent individuals (P1, P2)

**Output:** Two child individuals (C1, C2) with mixed genes

**Probability:** 70% per pair (`CXPB = 0.7`)

### Mechanism

**Uniform Crossover Process:**
```
For each gene position i in individual:
    Roll random [0, 1)
    If random < 0.5:
        Swap P1[i] ↔ P2[i]
    Else:
        Keep P1[i], P2[i] unchanged
```

**Example:**
```
Before:
P1: [Gene_A1, Gene_A2, Gene_A3, Gene_A4, Gene_A5]
P2: [Gene_B1, Gene_B2, Gene_B3, Gene_B4, Gene_B5]

Random rolls: [0.3, 0.7, 0.2, 0.8, 0.4]
Swap at:       YES   NO   YES   NO   YES

After:
C1: [Gene_B1, Gene_A2, Gene_B3, Gene_A4, Gene_B5]
C2: [Gene_A1, Gene_B2, Gene_A3, Gene_B4, Gene_A5]
```

### Effect on Your Structures

**Gene:** 
- Individual genes swapped wholesale (all 5 fields: course, instructor, group, room, quanta)
- No gene-internal modification
- Gene integrity preserved (no field mixing between genes)

**Individual/Chromosome:**
- Gene order preserved (position i remains position i)
- Approximately 50% genes from each parent (on average)
- Creates novel session combinations
- May introduce conflicts (instructor teaching two groups simultaneously)

**Population:**
- Applied to pairs: processes 50 parents → 50 offspring
- Operates on clones (parents unaffected)
- 70% of pairs undergo crossover, 30% pass through unchanged

### Constraint Implications

**Benefits:**
- Inherits valid course-group pairings from both parents
- Transfers good scheduling patterns (time slots, room assignments)
- Mixes instructor assignments

**Risks:**
- Creates instructor conflicts (if P1 and P2 both use instructor X at different times, child might have X twice simultaneously)
- Creates room conflicts (double-booking possible)
- Breaks good gene co-location (genes that work well together get separated)

**Mitigation:** Evaluation step filters out poor combinations; mutation can repair minor conflicts.

---

## 4. Mutation (Individual → Modified Individual)

**Operator:** `mutate_individual` (custom constraint-aware)

**Purpose:** Introduce variation to escape local optima and repair conflicts.

**Level:** Gene-level (operates on individual genes)

**Input:** One individual

**Output:** Modified individual with some genes changed

**Probability:** 
- **Individual selection:** 15% per generation (`MUTPB = 0.15`)
- **Gene mutation:** 20% per gene (if individual selected)

### Mechanism

**Two-Stage Process:**

**Stage 1: Individual Selection**
```
For each offspring:
    If random < 0.15:
        Apply mutation to this individual
```

**Stage 2: Gene-Level Mutation**
```
For each gene i in selected individual:
    If random < 0.2:
        gene[i] = mutate_gene(gene[i], context)
```

**Expected mutations per individual:** 0.2 × (genes per individual) ≈ 0.2 × 100 = 20 genes

### Gene Mutation Details (`mutate_gene`)

**Constraint-Aware Strategy:** Preserves validity while introducing variation.

**1. Group Mutation (90% preservation)**
- **Constraint:** Only mutate to groups enrolled in this course
- **Behavior:** 90% keep current group if valid, 10% change to another enrolled group
- **Rationale:** Course-group relationship is fundamental (hard constraint)

**2. Instructor Mutation (70% preservation)**
- **Constraint:** Only mutate to qualified instructors for this course
- **Behavior:** 70% keep current instructor if qualified, 30% change to another qualified instructor
- **Rationale:** Instructor qualification is hard constraint, but more flexible than enrollment

**3. Room Mutation (50% preservation)**
- **Constraint:** Match group size, course features (lab/classroom), room capacity
- **Behavior:** 50% keep current room if suitable, 50% change to another suitable room
- **Filters:**
  - Room capacity ≥ group size
  - Room features match course requirements (e.g., lab equipment for practical sessions)
  - Room type matches course type

**4. Time Mutation (30% preservation)**
- **Constraint:** Maintain session duration based on course L-T-P hours
- **Behavior:** 
  - 30% keep current time if duration matches
  - 70% reassign to new time slots
- **Strategy:**
  - Calculate required quanta: (L + T + P) × 4 quanta/hour
  - Attempt 5 times to find consecutive slots
  - Prefer compact sessions (max 2-hour blocks)
  - Fallback to random non-consecutive slots if needed

**5. Course ID (100% preservation)**
- **Never mutated:** Course identity defines the gene

### Effect on Your Structures

**Gene:**
- Replaced with new `SessionGene` object
- 1-4 fields modified (course_id always preserved)
- Maintains semantic validity (qualified instructors, enrolled groups, suitable rooms)

**Individual/Chromosome:**
- ~20 genes mutated per selected individual (20% of ~100 genes)
- 85% of population unchanged per generation
- Introduces local variations, not wholesale changes

**Population:**
- ~7.5 individuals mutated per generation (15% of 50)
- ~150 gene mutations total per generation across population
- Diversity maintained while preserving good structures

### Constraint Implications

**Benefits:**
- Reduces instructor conflicts (reassigns instructors)
- Fixes room mismatches (selects suitable rooms)
- Resolves time conflicts (reassigns quanta)
- Maintains course-group enrollment relationships

**Risks:**
- May break good time slot arrangements
- Can introduce new conflicts (though evaluation filters them)

**Balance:** Low mutation rate (15%) preserves good solutions while allowing exploration.

---

## 5. Evaluation (Individual → Fitness Values)

**Operator:** `evaluate` (custom multi-objective)

**Purpose:** Assign fitness scores measuring constraint violations.

**Level:** Individual-level (reads entire schedule)

**Input:** One individual (list of genes)

**Output:** Tuple of two fitness values: `(hard_penalty, soft_penalty)`

### Mechanism

**Step 1: Decode Individual**
Transform `List[SessionGene]` → `List[CourseSession]` (enriched with object references)

**Step 2: Evaluate Hard Constraints**
Sum violation counts:
- `no_group_overlap`: Groups in multiple places simultaneously
- `no_instructor_conflict`: Instructors teaching multiple sessions simultaneously
- `instructor_not_qualified`: Instructor lacking course qualification
- `room_type_mismatch`: Lab courses in classrooms, lectures in labs
- `availability_violations`: Sessions outside instructor/group/room availability windows
- `incomplete_or_extra_sessions`: Wrong number of sessions per course

**Step 3: Evaluate Soft Constraints**
Sum penalty points:
- `group_gaps_penalty`: Idle time between group sessions
- `instructor_gaps_penalty`: Idle time between instructor sessions
- `group_midday_break_violation`: No lunch break for groups
- `course_split_penalty`: Course sessions spread across multiple days
- `early_or_late_session_penalty`: Sessions before 8 AM or after 6 PM

**Step 4: Return Fitness Tuple**
`(hard_penalty, soft_penalty)` assigned to `individual.fitness.values`

### Effect on Your Structures

**Gene:** No modification (read-only)

**Individual/Chromosome:**
- No structural change
- Fitness attribute updated: `individual.fitness.values = (hard, soft)`
- Used by selection operator for dominance comparison

**Population:**
- Each individual evaluated independently
- Fitness values enable ranking and selection
- Invalid individuals (after crossover/mutation) re-evaluated

### Fitness Interpretation

**Hard Constraints:**
- Target: 0 (feasible solution)
- Weight: -1.0 (primary objective)
- Example: 5 group overlaps + 3 instructor conflicts = 8 hard penalty

**Soft Constraints:**
- Target: minimize (quality improvement)
- Weight: -0.01 (secondary objective)
- Typical range: 0-500 points
- Example: 200 gap minutes + 50 split penalty = 250 soft penalty

**Multi-Objective Trade-offs:**
- Individual A: (0, 500) → Feasible but poor quality
- Individual B: (2, 50) → Infeasible but good quality
- Pareto front: All non-dominated solutions preserved

---

## 6. Supporting Operations

### 6.1 Elitism (Implicit in NSGA-II)

**Mechanism:** `(parents + offspring) → select best 50`

**Purpose:** Prevent loss of best solutions found so far.

**Process:**
1. Combine parent population (50) + offspring (50) = 100 candidates
2. NSGA-II selection chooses best 50
3. Best individuals guaranteed to survive if not dominated

**Effect:** Monotonic fitness improvement (best solution never worsens).

---

### 6.2 Diversity Tracking

**Metric:** `average_pairwise_diversity` (custom implementation)

**Purpose:** Monitor population convergence.

**Calculation:**
```
For each pair (ind_i, ind_j) in population:
    gene_diff = count differences in (course, instructor, group, room, quanta)
    normalize to [0, 1]
    average across all genes
pairwise_diversity = average across all pairs
```

**Interpretation:**
- 1.0 = Maximum diversity (all individuals completely different)
- 0.0 = Zero diversity (all individuals identical)
- Typical evolution: 0.6 → 0.3 → 0.1 (convergence)

**Effect:** Read-only metric, doesn't modify population.

---

### 6.3 Fitness Invalidation

**Mechanism:** `del offspring[i].fitness.values`

**Purpose:** Mark individuals needing re-evaluation after modification.

**Trigger:** After crossover or mutation

**Effect:** 
- Sets `individual.fitness.valid = False`
- Forces re-evaluation before selection
- Prevents using stale fitness from parent

---

## Operator Pipeline (One Generation)

**Generation Loop (100 iterations):**

```
1. SELECTION (Population → Parents)
   Input:  50 individuals with fitness values
   Output: 50 selected parents (NSGA-II)

2. CLONING (Parents → Offspring)
   Input:  50 parents
   Output: 50 cloned offspring (independent copies)

3. CROSSOVER (Offspring pairs → Modified offspring)
   For i in [1, 3, 5, ..., 49] (pairs):
       If random < 0.7:
           crossover_uniform(offspring[i-1], offspring[i])
           Invalidate fitness for both
   Expected: ~35 pairs = 70 individuals modified

4. MUTATION (Each offspring → Modified offspring)
   For each offspring:
       If random < 0.15:
           For each gene:
               If random < 0.2:
                   mutate_gene(gene)
           Invalidate fitness
   Expected: ~7.5 individuals, ~150 total gene mutations

5. EVALUATION (Modified offspring → Fitness values)
   For each offspring with invalid fitness:
       fitness = evaluate(offspring)
       offspring.fitness.values = fitness
   Expected: ~70-75 evaluations (crossover + mutation overlap)

6. REPLACEMENT (Parents + Offspring → New population)
   Combined = parents (50) + offspring (50) = 100
   New population = NSGA-II select best 50 from combined
   
7. TRACKING
   Record: best hard/soft fitness, diversity, detailed constraints
```

---

## Parameter Summary

| Operator | Parameter | Value | Effect |
|----------|-----------|-------|--------|
| **Selection** | Method | NSGA-II | Multi-objective Pareto optimization |
| **Population** | Size | 50 | Individuals per generation |
| **Evolution** | Generations | 100 | Iteration count |
| **Crossover** | Rate | 70% | Pairs undergoing crossover |
| **Crossover** | Type | Uniform | 50% gene swap probability |
| **Mutation** | Individual Rate | 15% | Individuals mutated per generation |
| **Mutation** | Gene Rate | 20% | Genes mutated within selected individual |
| **Mutation** | Group Preservation | 90% | Keep valid course-group relationships |
| **Mutation** | Instructor Preservation | 70% | Keep qualified instructors |
| **Mutation** | Room Preservation | 50% | Keep suitable rooms |
| **Mutation** | Time Preservation | 30% | Keep appropriate time slots |
| **Fitness** | Hard Weight | -1.0 | Primary objective (feasibility) |
| **Fitness** | Soft Weight | -0.01 | Secondary objective (quality) |

---

## Rationale & Design Decisions

**Why Uniform Crossover?**
- Genes are independent (sessions don't have positional relationships)
- Uniform crossover mixes genes from both parents effectively
- No ordering constraints (session 1 vs session 50 position irrelevant)

**Why Low Mutation Rate?**
- Constraint-aware seeding produces structurally valid individuals
- High mutation would destroy good course-group relationships
- 15% × 20% = 3% per-gene mutation probability balances exploration/exploitation

**Why High Crossover Rate?**
- Good solutions spread quickly through population
- Crossover less disruptive than mutation (preserves more structure)
- 70% allows rapid propagation of successful patterns

**Why NSGA-II?**
- Natural fit for hard/soft constraint trade-offs
- Maintains diverse solution set (useful for different stakeholder preferences)
- Binary tournament and crowding distance built-in (no separate selector needed)

**Why Constraint-Aware Mutation?**
- Random mutation creates too many infeasible solutions
- Preserving course-group enrollment critical (data-driven constraint)
- Intelligent mutation repairs conflicts rather than creating them

---

## Interaction Effects

**Crossover + Mutation:**
- Crossover creates conflicts → Mutation repairs them
- Crossover spreads good genes → Mutation fine-tunes them
- Overlap possible (both modify same individual)

**Selection + Elitism:**
- NSGA-II naturally elitist (best survive in combined population)
- No separate elitism operator needed
- Guarantees monotonic progress on Pareto front

**Evaluation + Selection:**
- Selection depends entirely on evaluation output
- Poor evaluation = poor selection = failed optimization
- Multi-objective evaluation enables trade-off exploration

---

## Related Modules

- **Operators:** `src/ga/operators/{crossover,mutation}.py`
- **Selection:** DEAP `tools.selNSGA2` (external library)
- **Evaluation:** `src/ga/evaluator/{fitness,detailed_fitness}.py`
- **Constraints:** `src/constraints/{hard,soft}.py`
- **Diversity:** `src/metrics/diversity.py`
- **Parameters:** `config/ga_params.py`
- **Main Loop:** `main.py` (lines 155-185)

---

## Evolution Trajectory (Typical Run)

| Generation | Hard Violations | Soft Penalties | Diversity | Dominant Operator |
|------------|-----------------|----------------|-----------|-------------------|
| 0 (Initial) | 20-50 | 400-600 | 0.6-0.8 | Smart seeding |
| 10-30 | 5-15 | 300-500 | 0.4-0.6 | Crossover (spread good patterns) |
| 40-70 | 1-5 | 200-400 | 0.2-0.4 | Mutation (fine-tune conflicts) |
| 80-100 | 0-2 | 100-300 | 0.1-0.2 | Selection (exploit best) |

Hard constraints dominate early; soft optimization dominates late.
