# Quick Test Configuration for Parallelization
# Temporarily set small values to test multiprocessing implementation

# ORIGINAL VALUES (restore after testing):
# POP_SIZE = 100
# NGEN = 1000

# TEST VALUES (for quick validation):
POP_SIZE = 20
NGEN = 10

CXPB, MUTPB = 0.5, 0.3

# Parallelization Settings
USE_MULTIPROCESSING = True  # Test with multiprocessing enabled
NUM_WORKERS = None  # Use all available CPU cores

# Instructions:
# 1. Run: python main.py
# 2. Should complete in ~10-30 seconds
# 3. Check console output for "Multiprocessing enabled: X workers"
# 4. After successful test, restore original values above
