# DIAGNOSIS: Instructor Qualification Hard Constraint Not Decreasing

## Problem
`instructor_not_qualified` hard constraint remains constant across all generations - GA evolution cannot reduce it.

## Root Cause Analysis

### 1. **Mutation Does NOT Respect Qualifications**

**Location**: `src/ga/operators/mutation.py:27-38`

**The Bug**:
```python
qualified_instructors = [
    inst_id
    for inst_id, inst in context["instructors"].items()
    if gene.course_id in getattr(inst, "qualified_courses", [gene.course_id])
]

# If current instructor is qualified, keep with high probability (70%)
if gene.instructor_id in qualified_instructors and random.random() < 0.7:
    new_instructor = gene.instructor_id
else:
    new_instructor = random.choice(
        qualified_instructors if qualified_instructors else [gene.instructor_id]
    )
```

**Problem**: The fallback `[gene.instructor_id]` means:
- When `qualified_instructors` is empty (no qualified instructor exists)
- Mutation keeps the UNQUALIFIED instructor
- Violations NEVER get fixed by mutation

### 2. **Population Initialization Also Doesn't Guarantee Qualifications**

**Location**: `src/ga/population.py:286-289`

**The Code**:
```python
qualified_instructors = find_qualified_instructors(course_id, context)
if not qualified_instructors:
    qualified_instructors = list(context["instructors"].values())
```

**Problem**: When no qualified instructor exists:
- Falls back to ANY instructor
- Creates initial population with violations
- These violations are LOCKED IN (mutation can't fix them)

### 3. **Why Soft Constraints Can Improve But Hard Cannot**

**Soft constraints** (like gaps) can improve because:
- Mutations change TIME SLOTS → reduces gaps naturally
- No instructor qualification needed

**Hard constraints** (instructor_not_qualified) cannot improve because:
- Mutations keep unqualified instructors when no alternative exists
- No mechanism to FORCE qualified selection
- Population starts with violations that persist forever

## Data Structure Issue - **THE SMOKING GUN**

**Reality Check**:
- Total courses: **392**
- Total instructors: **193**
- Courses with NO qualified instructors: **214** (54.6% of all courses!)

**Examples of unassigned courses**:
- ENSH 101 (Engineering Mathematics I)
- ENME 103 (Engineering Mechanics I)
- ENAR 101 (Design Studio I) + ENAR 101-PR
- ENCT 101 + ENCT 101-PR
- ...and 200+ more

**Why this happens**:
1. Instructors in `Instructors.json` list course codes they teach (e.g., "ENSH 151")
2. BUT many courses in `Course.json` have NO instructors listing them
3. `link_courses_and_instructors()` only creates links when BOTH sides match
4. Result: 214 courses are **orphaned** - no qualified instructor exists

**System behavior**:
- When `course.qualified_instructor_ids = []` (empty!)
- Population initialization falls back to ANY instructor
- Mutation has NO valid instructor to choose
- Violations are **PERMANENTLY LOCKED IN**

## Impact

When testing with ONLY `instructor_not_qualified` enabled:
- Initial population: 214+ violations (one per orphaned course × groups)
- After 1000 generations: STILL 214+ violations
- Constraint value NEVER changes
- GA appears "broken" but it's actually **DATA COMPLETENESS ISSUE**

## Why This Happens

1. **Missing instructor qualification data** in `Instructors.json`
   - Instructors don't list all courses they can teach
   
2. **No fallback strategy** in mutation
   - When `qualified_instructors` is empty, keeps violating instructor
   
3. **No repair mechanism** 
   - GA has no way to "discover" that instructor X could teach course Y

## Why Soft Constraint Improves But Hard Doesn't

**Soft Constraint (group_gaps_penalty)**: ✅ **CAN IMPROVE**
- Measures gaps between sessions for the same group
- Mutation changes TIME SLOTS (quanta) → naturally reduces/increases gaps
- No dependency on external data (instructors, qualifications)
- GA can explore different time arrangements freely

**Hard Constraint (instructor_not_qualified)**: ❌ **CANNOT IMPROVE**
- Measures instructor-course qualification mismatch
- Mutation tries to change INSTRUCTOR → but falls back to same unqualified one
- **Dependency on data**: needs `qualified_instructor_ids` list
- When list is EMPTY, mutation has nowhere to go
- GA is **trapped** - cannot discover new qualifications

## The Trap Mechanism

```
Course X has NO qualified instructors
    ↓
Population init: Assigns random instructor A (UNQUALIFIED)
    ↓
Evaluation: +1 violation for instructor_not_qualified
    ↓
Selection: Individual survives (it's no worse than others)
    ↓
Mutation on gene for Course X:
    - Looks for qualified_instructors → EMPTY LIST
    - Fallback: keeps instructor A (still UNQUALIFIED)
    ↓
Evaluation: +1 violation (SAME AS BEFORE)
    ↓
LOOP FOREVER - violation never decreases
```

## Solution Required

Must fix BOTH:

### 1. **Data Fix**: Ensure all courses have qualified instructors
- Option A: Add instructor qualifications to `Instructors.json`
- Option B: Create "default" instructor qualified for all courses
- Option C: Allow any instructor to teach any course (remove constraint temporarily)

### 2. **Logic Fix**: Mutation should handle empty qualification list
**Current (BROKEN)**:
```python
qualified_instructors = find_qualified_instructors(course_id, context)
new_instructor = random.choice(
    qualified_instructors if qualified_instructors else [gene.instructor_id]  # ← KEEPS VIOLATING
)
```

**Fixed**:
```python
qualified_instructors = find_qualified_instructors(course_id, context)
if not qualified_instructors:
    # When no qualified instructor exists, pick ANY instructor
    # This doesn't fix the violation, but allows GA to explore
    qualified_instructors = list(context["instructors"].keys())
new_instructor = random.choice(qualified_instructors)
```

### 3. **Alternative**: Disable constraint until data is complete
In `config/constraints.py`:
```python
"instructor_not_qualified": {"enabled": False, "weight": 1.0},
```

This allows testing OTHER constraints while data is being prepared.
