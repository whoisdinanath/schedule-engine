#!/usr/bin/env python3

"""
Debug script to isolate the adaptive weights issue.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from main import TimetablingSystem
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

def debug_adaptive_weights():
    """Debug the adaptive weights issue."""
    
    # Create a test TimetablingSystem
    system = TimetablingSystem()
    
    # Load data
    print("Loading data...")
    system.load_input_data('data/sample_courses.csv', 'data/sample_instructors.csv', 
                          'data/sample_rooms.csv', 'data/sample_groups.csv')
    
    # Create GA engine
    ga_engine = GAEngine(
        population_size=50,
        max_generations=5,
        mutation_rate=0.1,
        crossover_rate=0.8
    )
    
    # Initialize GA
    ga_engine.initialize(system.courses, system.instructors, system.rooms, system.groups)
    
    # Create and evaluate a test chromosome
    chromosome = Chromosome()
    chromosome.generate_random_schedule(system.courses, system.instructors, system.rooms, system.groups)
    
    # Count violations
    violations = ga_engine._count_violations(chromosome)
    print(f"Violations structure: {violations}")
    print(f"Violations type: {type(violations)}")
    
    # Test flattening
    flat_violations = {}
    flat_violations.update(violations.get('hard', {}))
    flat_violations.update(violations.get('soft', {}))
    print(f"Flattened violations: {flat_violations}")
    print(f"Flattened violations type: {type(flat_violations)}")
    
    # Test adaptive weights
    try:
        ga_engine.adaptive_weights.update_weights(flat_violations, 0)
        print("✓ Adaptive weights updated successfully")
    except Exception as e:
        print(f"✗ Adaptive weights failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_adaptive_weights()
