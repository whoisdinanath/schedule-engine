#!/usr/bin/env python3
"""
Test script to verify the enhanced genetic algorithm with adaptive mechanisms.
"""

import sys
sys.path.append('c:\\Users\\krishna\\Desktop\\genetics')

import logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   handlers=[logging.StreamHandler(sys.stdout)])

from main import TimetablingSystem
import time

def test_enhanced_ga():
    """Test the enhanced GA with adaptive mechanisms."""
    print("Testing Enhanced Genetic Algorithm with Adaptive Mechanisms")
    print("=" * 60)
    
    # Initialize system
    system = TimetablingSystem()
    
    # Load sample data
    try:
        system.load_data(
            'c:\\Users\\krishna\\Desktop\\genetics\\data\\sample_courses.csv',
            'c:\\Users\\krishna\\Desktop\\genetics\\data\\sample_instructors.csv', 
            'c:\\Users\\krishna\\Desktop\\genetics\\data\\sample_rooms.csv',
            'c:\\Users\\krishna\\Desktop\\genetics\\data\\sample_groups.csv'
        )
        print("✓ Successfully loaded data")
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return False
    
    # Create progress callback
    def progress_callback(generation: int, best_fitness: float, stats: dict) -> bool:
        """Show progress every 10 generations."""
        if generation % 10 == 0:
            violations = stats.get('violations', {})
            hard_violations = violations.get('total_hard', 0)
            diversity = stats.get('diversity', 0)
            stagnation = stats.get('stagnation', 0)
            
            print(f"Gen {generation:3d}: Fitness={best_fitness:8.4f}, "
                  f"Hard_Violations={hard_violations:3d}, "
                  f"Diversity={diversity:.3f}, "
                  f"Stagnation={stagnation:2d}")
            
            # Stop if feasible solution found
            if hard_violations == 0:
                print("✓ Found feasible solution!")
                return False
        
        return True
    
    # Run optimization
    print("\\nStarting optimization with enhanced GA...")
    start_time = time.time()
    
    try:
        best_solution = system.optimize(callback=progress_callback)
        end_time = time.time()
        
        if best_solution:
            print(f"\\n✓ Optimization completed in {end_time - start_time:.2f} seconds")
            
            # Get final statistics
            stats = system.get_evolution_stats()
            if stats:
                final_solution = stats.get('final_solution', {})
                print(f"Final solution feasible: {final_solution.get('is_feasible', False)}")
                print(f"Hard violations: {final_solution.get('hard_violations', 'N/A')}")
                print(f"Soft violations: {final_solution.get('soft_violations', 'N/A')}")
                
                # Show fitness improvement
                evolution = stats.get('evolution', {})
                print(f"Total generations: {evolution.get('generations', 'N/A')}")
                print(f"Total evaluations: {evolution.get('total_evaluations', 'N/A')}")
                
                fitness_history = stats.get('fitness', {}).get('fitness_history', [])
                if len(fitness_history) > 1:
                    initial_fitness = fitness_history[0]['best']
                    final_fitness = fitness_history[-1]['best']
                    improvement = final_fitness - initial_fitness
                    print(f"Fitness improvement: {improvement:+.4f} ({initial_fitness:.4f} → {final_fitness:.4f})")
            
            return True
        else:
            print("✗ Optimization failed")
            return False
            
    except Exception as e:
        print(f"✗ Error during optimization: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_enhanced_ga()
    sys.exit(0 if success else 1)
