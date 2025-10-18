# Smart Repair System

## Overview
Enhanced repair heuristics that consider **alternative qualified instructors** and **session clustering** when resolving conflicts.

## Key Innovation: `_find_available_slot_smart()`

### What It Does
Instead of blindly moving conflicting sessions to any available slot, it:

1. **Finds ALL qualified instructors** for the course (by checking course subject)
2. **Tries each qualified instructor's availability**
3. **Scores slots by clustering quality**:
   - **100 points**: Adjacent to existing session (forms 2-3 quantum blocks)
   - **10 points**: Same day as existing session
   - **0 points**: Different day
4. **Returns best slot + potentially better instructor + potentially better room**

### Benefits
- **Reduces instructor conflicts**: By considering alternative qualified instructors
- **Improves clustering**: Prefers slots that form 2-3 quantum blocks
- **Maintains feasibility**: All hard constraints still satisfied
- **Reduces soft penalties**: Better clustering = fewer gap penalties

## Clustering Strategy

### Session Block Preferences (2-3 Quanta)
Based on `config/time_config.py`:
- `PREFERRED_BLOCK_SIZE_MIN = 2`
- `PREFERRED_BLOCK_SIZE_MAX = 3`

### Scoring Logic
```
Adjacent quantum (e.g., 9:00-10:00 next to 10:00-11:00): +100 score
Same day (e.g., both on Monday): +10 score
Different day: 0 score
```

### Why This Works
- **2-quantum blocks**: Natural for 2-hour courses (lecture+tutorial)
- **3-quantum blocks**: Good for 3-hour courses or lecture+practical
- **Adjacent slots**: Minimize student/instructor travel time
- **Same-day clustering**: Reduce days students must attend

## Updated Repair Functions

### 1. `repair_group_overlaps()` (Priority 2)
**Old**: Move to any available slot  
**New**: Move to best clustering slot with qualified instructor

### 2. `repair_instructor_conflicts()` (Priority 4)
**Old**: Move to any available slot  
**New**: Move to best clustering slot with alternative qualified instructor

### 3. `repair_session_clustering()` (Priority 7)
**Strategy**: **ONLY rearranges**, never adds/removes quanta
- Moves isolated 1-quantum sessions to adjacent free positions
- Forms 2-3 quantum blocks when possible
- Preserves total scheduled hours per course

## Implementation Details

### Helper Functions
- `_find_available_slot_smart()`: Main smart finder
- `_validate_candidate_slot()`: Check all hard constraints
- `_score_clustering()`: Score slot quality
- `_try_rearrange_isolated_quantum()`: Move isolated quanta (clustering repair)

### Constraints Preserved
✓ Instructor availability  
✓ Room availability  
✓ Group availability  
✓ No group overlaps  
✓ No instructor conflicts  
✓ No room conflicts  
✓ Instructor qualifications  
✓ **Total quanta per course (population invariant)**

## Configuration

### Enable Smart Repairs
Already enabled in `config/ga_params.py`:
```python
"repair_group_overlaps": {"enabled": True, "priority": 2}
"repair_instructor_conflicts": {"enabled": True, "priority": 4}
"repair_session_clustering": {"enabled": True, "priority": 7}
```

### Clustering Parameters
In `config/time_config.py`:
```python
PREFERRED_BLOCK_SIZE_MIN = 2  # Minimum preferred block size
PREFERRED_BLOCK_SIZE_MAX = 3  # Maximum preferred block size
ISOLATED_SESSION_PENALTY = 5  # Penalty per isolated 1-quantum session
```

## Expected Impact

### Hard Constraint Violations
- **Instructor conflicts**: ↓ 30-50% (alternative instructors)
- **Group overlaps**: ↓ 20-30% (better slot selection)

### Soft Constraint Penalties
- **Group gaps**: ↓ 40-60% (clustering reduces gaps)
- **Instructor gaps**: ↓ 30-50% (clustering reduces gaps)
- **Clustering penalty**: ↓ 50-70% (direct optimization)

### Population Quality
- **Crossover success rate**: ↑ (fewer violations)
- **Convergence speed**: ↑ (better repair quality)
- **Solution diversity**: ↑ (multiple qualified instructors)

## Testing

Run with current configuration:
```powershell
.\x.ps1
```

Monitor these metrics in output:
- `Repairs: XXX fixes (instr_avail:XXX)`
- `session_block_clustering_penalty: XXX`
- `group_gaps_penalty: XXX`
- `instructor_gaps_penalty: XXX`

Expected: Lower penalties after ~10-20 generations as smart repairs propagate through population.
