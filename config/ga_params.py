# This File Contains Genetic Algorithm Parameters

# Population size - smaller population for faster convergence with constraint-aware initialization
POP_SIZE = 100

# Number of generations - reduced since constraint-aware init should converge faster
NGEN = 1000

# Crossover and mutation probabilities optimized for constraint-aware population
CXPB, MUTPB = 0.5, 0.3  # Reduced mutation to preserve good constraint relationships

# Parallelization Settings
USE_MULTIPROCESSING = True  # Set to False for debugging (single-threaded execution)
NUM_WORKERS = None  # None = use all available CPU cores, or specify manually (e.g., 4)

# Notes:
# - Smaller population works better with constraint-aware initialization
# - Lower mutation rate preserves the structural integrity of solutions
# - Higher crossover rate allows good solutions to spread quickly
# - Multiprocessing provides 3-6× speedup by parallelizing fitness evaluation
# - Set USE_MULTIPROCESSING=False when debugging to simplify error tracking
