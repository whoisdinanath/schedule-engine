# BUGFIX: Pareto Front KDE Singular Matrix Error

## Problem
`gaussian_kde` failed with `LinAlgError` when population data had insufficient variance or lay in lower-dimensional subspace. Occurred during Pareto front density visualization when fitness values converged to similar points.

## Root Cause
- GA convergence produced near-identical fitness values
- Low variance → singular covariance matrix
- KDE requires non-degenerate data distribution

## Solution
Three-tier fallback in `src/exporter/plotpareto.py`:
1. **Pre-check**: Validate variance (`std > 1e-6`) before attempting KDE
2. **Catch LinAlgError**: Wrap KDE call in try-except for degenerate data
3. **Histogram fallback**: Use `np.histogram2d` when KDE fails
4. **Ultimate fallback**: Plain scatter plot

## Implementation
- Added variance validation before KDE computation
- Nested error handling for graceful degradation
- Maintains visualization quality with appropriate alternatives

## Impact
- No more crashes on converged populations
- Automatic density visualization method selection
- Preserves plot generation for all data distributions
