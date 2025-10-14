# Documentation Standards - Schedule Engine

## Philosophy
Code is self-documenting. `/docs` captures **concepts and architecture**, not implementation details.

## Documentation Rules

### ✅ DO Include
- **Problem statement**: What issue does this solve?
- **Solution approach**: High-level strategy
- **Key components**: What modules/classes are involved?
- **Design rationale**: WHY this approach? What tradeoffs?
- **Architecture decisions**: How components interact
- **Migration impact**: Breaking changes, compatibility

### ❌ DON'T Include
- Code snippets (except minimal, crucial examples)
- Line-by-line implementation explanations
- Detailed function descriptions (use docstrings for that)
- Verbose prose or filler words
- Step-by-step tutorials

## Structure Template
```markdown
# Feature Name

## Problem
1-2 sentences: what issue existed?

## Solution
1 sentence: core approach

## Architecture
Bullet points:
- Component A: purpose
- Component B: purpose
- Key interaction: how they work together

## Design Rationale
Why this approach over alternatives? What tradeoffs?

## Implementation
"See `path/to/module.py`" (NO code details)
```

## Length Guidelines
- **Total doc**: 30-80 lines max
- **Per section**: 1-2 short paragraphs OR bullet list
- **Paragraphs**: 2-4 sentences max
- **Code examples**: Only if absolutely critical (< 5 lines)

## Example: Good vs Bad

### ❌ BAD (Too Verbose)
```markdown
The QuantumTimeSystem class uses several data structures to track
operating hours. First, it creates a day_quanta_offset dictionary
which stores the starting quantum index for each day. This is calculated
by iterating through all days and accumulating the quanta counts...

Here's how the time_to_quanta method works:
```python
def time_to_quanta(self, day: str, time_str: str) -> int:
    day = day.capitalize()
    if not self.is_operational(day):
        raise ValueError(f"{day} is not an operational day")
    # ... 20+ more lines
```
```

### ✅ GOOD (Concise)
```markdown
## Architecture
- `day_quanta_offset`: Starting index per operational day
- `time_to_quanta()`: Converts wall-clock to continuous index, validates against operating hours
- Raises `ValueError` for non-operational times

See `src/encoder/quantum_time_system.py` for implementation.
```

## Cross-References
Instead of repeating information:
- Link to other docs: "See `quantum-migration.md` for update steps"
- Reference code: "Implementation in `constraints/soft.py`"
- Point to tests: "Run `test_continuous_quanta.py` to verify"

## Maintenance
- Update docs when **concepts** change, not for small code tweaks
- Remove outdated docs immediately
- Merge redundant docs into single files

## Enforcement
All `/docs` files reviewed for:
1. Concept-focused (not code-focused)
2. Conciseness (under length limits)
3. Problem → Solution → Architecture structure
4. No redundant explanations

---

**Remember**: If it's in the code, it doesn't need to be in the docs. Document the thinking, not the typing.
