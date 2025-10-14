# Creator Registry Pattern

## Problem
DEAP's `creator.create()` raises errors when called multiple times with the same type name. Scattered creator initialization across modules causes:
- Import order dependencies
- Duplicate registration errors
- Inconsistent fitness weights

## Solution
Centralized `creator_registry.py` module that:
- Initializes creator types once using `hasattr()` guard
- Provides `get_creator()` accessor function
- Auto-initializes on module import

## Usage
```python
from src.ga.creator_registry import get_creator

creator = get_creator()
individual = creator.Individual([gene1, gene2])
```

## Types Registered
- **FitnessMulti**: weights=(-1.0, -0.01) for hard/soft constraint minimization
- **Individual**: list subclass with FitnessMulti fitness

## Migration
All modules now import from `creator_registry` instead of directly using `deap.creator`. Module `src.ga.__init__` re-exports `get_creator` for convenience.
