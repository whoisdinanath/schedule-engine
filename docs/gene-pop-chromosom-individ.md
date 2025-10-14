# GA Structure: Gene, Chromosome, Individual, Population

## Core Components

### Gene = `SessionGene`
**Purpose:** Atomic scheduling unit representing one class session.

**Encodes:**
- Course identifier
- Instructor assignment
- Student group
- Room allocation
- Time quanta (15-min blocks)

**Cardinality:** One gene = one course meeting.

---

### Chromosome = Individual = `List[SessionGene]`
**Purpose:** Complete timetable solution.

**Structure:** Ordered list of genes encoding all sessions for the scheduling period.

**DEAP Type:** `creator.Individual` (list subclass with fitness attribute)

**Size:** Variable (50-200 genes typical, depends on course-group enrollments)

**Fitness:** `FitnessMulti` with weights `(-1.0, -0.01)`
- Objective 1: Hard constraint violations (strict)
- Objective 2: Soft constraint penalties (preferences)

**Terminology Note:** "Chromosome" and "Individual" are **synonymous** in this project—both refer to the same `List[SessionGene]` structure. DEAP uses "Individual"; GA literature often uses "Chromosome."

---

### Population = `List[Individual]`
**Purpose:** Solution pool for evolutionary search.

**Configuration:**
- Size: 50 individuals (`POP_SIZE`)
- Generations: 100 (`NGEN`)
- Selection: NSGA-II (multi-objective, Pareto-based)

**Initialization:** Course-group-aware seeding via `generate_course_group_aware_population`
- Respects enrollment relationships
- Creates L-T-P sessions (Lecture-Tutorial-Practical)
- Avoids initial conflicts (instructor/group/room clashes)

**Evolution:**
1. Select parents (NSGA-II)
2. Crossover (70% uniform gene swap)
3. Mutation (15% gene modification)
4. Evaluate offspring
5. Combine + select best 50

---

## Data Flow

```
Input JSON (courses, groups, instructors, rooms)
    ↓
SessionGene (encoded, compact)
    ↓
List[SessionGene] = Individual/Chromosome
    ↓
List[Individual] = Population
    ↓
Evolution (100 generations, NSGA-II)
    ↓
Best Individual
    ↓
Decode to CourseSession (rich objects)
    ↓
Export (JSON, calendars, plots)
```

---

## Key Distinctions

| Term | Type | Scope | Module |
|------|------|-------|--------|
| **Gene** | `SessionGene` | Single session | `src/ga/sessiongene.py` |
| **Chromosome** | `List[SessionGene]` | Full schedule | DEAP Individual |
| **Individual** | `List[SessionGene]` | Full schedule | `src/ga/individual.py` |
| **Population** | `List[Individual]` | Solution set | `src/ga/population.py` |

---

## Rationale

**Why List-Based Chromosomes?**
- Natural mapping: schedule = list of sessions
- DEAP compatibility (built-in list operators)
- Flexible length (handles varying enrollments)

**Why Multi-Objective?**
- Hard constraints: infeasibility (must be zero)
- Soft constraints: quality (minimize)
- NSGA-II balances both via Pareto dominance

**Why Course-Group Seeding?**
- Random initialization violates fundamental constraints
- Enrollment-aware approach starts with structurally valid solutions
- Faster convergence (fewer generations needed)

---

## Related Modules

- **Creation:** `src/ga/creator_registry.py` (DEAP types)
- **Seeding:** `src/ga/population.py` (initialization)
- **Operators:** `src/ga/operators/{crossover,mutation}.py`
- **Evaluation:** `src/ga/evaluator/{fitness,detailed_fitness}.py`
- **Decoding:** `src/decoder/individual_decoder.py` (SessionGene → CourseSession)
- **Constraints:** `src/constraints/{hard,soft}.py`

---

## Evolution Parameters

See `config/ga_params.py` for tunable values:
- Population size (50)
- Generation count (100)
- Crossover probability (0.7)
- Mutation probability (0.15)

Lower mutation preserves structural validity; higher crossover spreads good patterns.
