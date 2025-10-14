# Parent-Subgroup Aware Initialization Strategy

## Problem Statement

Current issues:
1. **Multi-quanta genes**: One gene represents multiple quanta (e.g., L+T=5 creates one gene with 5 quanta)
2. **Parent-subgroup conflicts**: No mechanism to prevent scheduling parent and subgroups simultaneously
3. **Random initialization**: C, G, I, T, R all assigned randomly, leading to high initial violations
4. **Over/under-scheduling**: No guarantee of correct total hours per course

## Proposed Solution: Two-Phase Initialization

### Phase 1: Generate (Course, Group) Pairs with Rules
**Fixed**: Course ID, Group IDs  
**Unknown**: Instructor, Time, Room

Rules:
- **Theory sessions** (L+T): Assign to parent group OR all subgroups together
  - One gene per quantum (L+T=5 → 5 genes)
  - All genes for same theory session share: Course, Groups (parent or all subgroups)
  - Example: `[(ENME151, [BAE2], None, None, None)] × 5 genes`
  
- **Practical sessions** (P): Assign to individual subgroups separately
  - One gene per quantum (P=3 → 3 genes per subgroup)
  - Example: `[(ENME151-PR, [BAE2A], None, None, None)] × 3 genes`
  - Example: `[(ENME151-PR, [BAE2B], None, None, None)] × 3 genes`

### Phase 2: Assign I, T, R with Conflict Minimization
- For each gene from Phase 1, assign:
  - **Instructor**: From qualified instructors, prefer available
  - **Time**: Find available quantum, avoid conflicts
  - **Room**: Match capacity and features, prefer available

## Architecture Changes

### 1. Gene Structure: One Quantum Per Gene

**Current**:
```python
SessionGene(
    course_id="ENME 151",
    group_ids=["BAE2"],
    quanta=[32, 33, 34, 35, 36]  # 5 quanta in one gene
)
```

**New** (5 separate genes):
```python
SessionGene(course_id="ENME 151", group_ids=["BAE2"], quanta=[32])
SessionGene(course_id="ENME 151", group_ids=["BAE2"], quanta=[33])
SessionGene(course_id="ENME 151", group_ids=["BAE2"], quanta=[34])
SessionGene(course_id="ENME 151", group_ids=["BAE2"], quanta=[35])
SessionGene(course_id="ENME 151", group_ids=["BAE2"], quanta=[36])
```

**Benefits**:
- More granular mutation (can change single hour)
- Easier to enforce non-consecutive sessions
- Better for partial scheduling
- Clearer constraint checking

### 2. Parent-Subgroup Strategy

```python
def identify_group_hierarchy(groups: Dict) -> Dict:
    """
    Returns:
        {
            "parents": ["BAE2", "BAE4", ...],
            "subgroups": {"BAE2": ["BAE2A", "BAE2B"], ...},
            "parent_map": {"BAE2A": "BAE2", "BAE2B": "BAE2", ...}
        }
    """
```

**Theory Session Logic**:
```python
# Option A: Schedule for parent (implicitly all subgroups attend together)
group_ids = [parent_id]

# Option B: Explicitly list all subgroups (for clarity)
group_ids = ["BAE2A", "BAE2B"]  # All subgroups together
```

**Practical Session Logic**:
```python
# Each subgroup gets separate practical sessions
for subgroup in subgroups:
    group_ids = [subgroup]
```

### 3. Constraint Updates

**Over/Under-Scheduling Check**:
```python
def check_course_hour_compliance(individual, courses):
    """
    Count genes per course and verify:
    - Theory course: total genes == L+T
    - Practical course: total genes per subgroup == P
    """
    course_gene_count = defaultdict(int)
    for gene in individual:
        course_gene_count[gene.course_id] += 1
    
    violations = 0
    for course_id, course in courses.items():
        expected = course.L + course.T if "-PR" not in course_id else course.P
        actual = course_gene_count[course_id]
        if actual != expected:
            violations += abs(expected - actual)
    
    return violations
```

**Parent-Subgroup Conflict**:
```python
def check_parent_subgroup_conflict(individual, group_hierarchy):
    """
    Verify no time conflicts between parent and its subgroups.
    If parent scheduled at time T, subgroups cannot be scheduled at T.
    """
    conflicts = 0
    parent_map = group_hierarchy["parent_map"]
    
    # Build time usage map
    for gene in individual:
        for group_id in gene.group_ids:
            for quantum in gene.quanta:
                # Check if this conflicts with parent/subgroups
                ...
    
    return conflicts
```

### 4. Decoder Updates

**Merge consecutive single-quantum genes into sessions**:
```python
def merge_consecutive_genes(individual):
    """
    Merge consecutive single-quantum genes with same C,G,I,R
    into multi-quantum sessions for export.
    
    Input: 5 genes with quanta [32], [33], [34], [35], [36]
    Output: 1 session with quanta [32, 33, 34, 35, 36]
    """
```

## Implementation Plan

### Step 1: Group Hierarchy Analyzer
```python
# src/ga/group_hierarchy.py
def analyze_group_hierarchy(groups_dict: Dict[str, Group]) -> Dict
```

### Step 2: Course-Group Pair Generator
```python
# src/ga/course_group_pairs.py
def generate_course_group_pairs(courses, groups, hierarchy) -> List[Tuple]
```

Returns:
```python
[
    ("ENME 151", ["BAE2"], "theory", 5),      # 5 theory quanta for parent
    ("ENME 151-PR", ["BAE2A"], "practical", 3),  # 3 practical quanta for subgroup A
    ("ENME 151-PR", ["BAE2B"], "practical", 3),  # 3 practical quanta for subgroup B
]
```

### Step 3: Phase 1 Skeleton Generator
```python
# src/ga/initialization/phase1_skeleton.py
def generate_skeleton_genes(course_group_pairs) -> List[SessionGene]
```

Creates genes with:
- `course_id`: ✓
- `group_ids`: ✓
- `instructor_id`: None
- `room_id`: None
- `quanta`: [None]  # Single quantum, value TBD

### Step 4: Phase 2 Assignment
```python
# src/ga/initialization/phase2_assignment.py
def assign_instructor_time_room(skeleton_genes, context) -> List[SessionGene]
```

Heuristics:
1. Assign time: Find available quantum avoiding conflicts
2. Assign instructor: From qualified, prefer available at that time
3. Assign room: Match features/capacity, prefer available

### Step 5: Constraint Adaptation
- Update `hard.py` to check over/under-scheduling
- Add parent-subgroup conflict check
- Adapt all constraint functions for single-quantum genes

### Step 6: Decoder/Exporter Updates
- Merge consecutive genes before export
- Maintain backward compatibility

## Benefits

✅ **Guarantees**:
- No over/under-scheduling (fixed C,G pairs ensure exact hours)
- No parent-subgroup conflicts (explicit hierarchy awareness)
- Theory sessions for whole class, practicals for subgroups

✅ **GA Optimization**:
- I, T, R can still be mutated/optimized
- Single-quantum genes allow finer control
- Better convergence from lower-violation initialization

✅ **Maintainability**:
- Clear separation of concerns (Phase 1 vs Phase 2)
- Explicit parent-subgroup relationships
- Easier to debug scheduling issues

## Example: Complete Flow

**Input**: BAE2 (parent) with subgroups BAE2A, BAE2B enrolled in ENME 151 (L=3, T=2, P=3)

**Phase 1 Output**:
```python
# Theory: 5 genes for parent (all subgroups attend together)
[
    SessionGene("ENME 151", ["BAE2"], None, None, [None]),  # Gene 1
    SessionGene("ENME 151", ["BAE2"], None, None, [None]),  # Gene 2
    SessionGene("ENME 151", ["BAE2"], None, None, [None]),  # Gene 3
    SessionGene("ENME 151", ["BAE2"], None, None, [None]),  # Gene 4
    SessionGene("ENME 151", ["BAE2"], None, None, [None]),  # Gene 5
]

# Practical: 3 genes per subgroup
[
    SessionGene("ENME 151-PR", ["BAE2A"], None, None, [None]),  # Gene 6
    SessionGene("ENME 151-PR", ["BAE2A"], None, None, [None]),  # Gene 7
    SessionGene("ENME 151-PR", ["BAE2A"], None, None, [None]),  # Gene 8
    SessionGene("ENME 151-PR", ["BAE2B"], None, None, [None]),  # Gene 9
    SessionGene("ENME 151-PR", ["BAE2B"], None, None, [None]),  # Gene 10
    SessionGene("ENME 151-PR", ["BAE2B"], None, None, [None]),  # Gene 11
]
```

**Phase 2 Output** (I, T, R assigned):
```python
[
    SessionGene("ENME 151", ["BAE2"], "INS001", "ROOM101", [32]),
    SessionGene("ENME 151", ["BAE2"], "INS001", "ROOM101", [33]),
    SessionGene("ENME 151", ["BAE2"], "INS001", "ROOM101", [128]),  # Different day
    SessionGene("ENME 151", ["BAE2"], "INS001", "ROOM101", [129]),
    SessionGene("ENME 151", ["BAE2"], "INS001", "ROOM101", [130]),
    
    SessionGene("ENME 151-PR", ["BAE2A"], "INS002", "LAB101", [40]),
    SessionGene("ENME 151-PR", ["BAE2A"], "INS002", "LAB101", [41]),
    SessionGene("ENME 151-PR", ["BAE2A"], "INS002", "LAB101", [42]),
    
    SessionGene("ENME 151-PR", ["BAE2B"], "INS002", "LAB101", [136]),  # Different time
    SessionGene("ENME 151-PR", ["BAE2B"], "INS002", "LAB101", [137]),
    SessionGene("ENME 151-PR", ["BAE2B"], "INS002", "LAB101", [138]),
]
```

**Export** (merged back):
```json
{
    "course_id": "ENME 151",
    "group_ids": ["BAE2"],
    "instructor_id": "INS001",
    "room_id": "ROOM101",
    "time": {
        "Monday": [{"start": "08:00", "end": "10:00"}],
        "Wednesday": [{"start": "08:00", "end": "11:00"}]
    }
}
```
