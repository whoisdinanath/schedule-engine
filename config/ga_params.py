# This File Contains Genetic Algorithm Parameters

# Population size - smaller population for faster convergence with constraint-aware initialization
POP_SIZE = 30

# Number of generations - reduced since constraint-aware init should converge faster
NGEN = 100

# Crossover and mutation probabilities optimized for constraint-aware population
CXPB, MUTPB = 0.7, 0.15  # Reduced mutation to preserve good constraint relationships

# Notes:
# - Smaller population works better with constraint-aware initialization
# - Lower mutation rate preserves the structural integrity of solutions
# - Higher crossover rate allows good solutions to spread quickly
