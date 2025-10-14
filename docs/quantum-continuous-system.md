# Continuous Quantum Time System

## Problem
Old system mapped quantum indices to absolute wall-clock time (24h × 7 days), wasting 60-75% of indices on non-operational hours (nights, closed days). Led to sparse indices with invalid values.

## Solution
**Continuous indexing**: quantum indices assigned ONLY to operating hours. Sunday 08:00 → quantum 0, Monday 08:00 → quantum 12. No gaps, all indices valid.

## Architecture

### Core Concept
Single time unit (`QUANTUM_MINUTES = 60`) represents both quantum duration and session length. Each operational day contributes only its operating hours to the continuous index space.

### Key Structures
- `day_quanta_offset`: Starting index per day
- `day_quanta_count`: Available quanta per day  
- `total_quanta`: Sum across all operational days

Example: 6 days × 12 hours = 72 continuous quanta (vs 168 in old system).

### API Changes
- `time_to_quanta()` / `quanta_to_time()`: Now instance methods (not classmethods)
- Validation: Raises `ValueError` for non-operational times (was silent before)
- Removed: `QUANTA_PER_DAY`, `TOTAL_WEEKLY_QUANTA` (replaced by dynamic `total_quanta`)

## Benefits
- **Efficiency**: Zero wasted indices
- **Validation**: Built-in operational hours checking
- **Flexibility**: Supports varying hours per day
- **Simplicity**: Index 0 = first slot, N-1 = last slot

## Migration Impact
**Breaking change**. Dependent code must update:
- Replace `TOTAL_WEEKLY_QUANTA` → `total_quanta`
- Remove hardcoded `QUANTA_PER_DAY` calculations
- Use `time_system` instance for day determination

Critical: `src/constraints/soft.py` requires rewrite (uses hardcoded day calculations). See `migration-guide.md`.

## Implementation
See `src/encoder/quantum_time_system.py` for code details.
