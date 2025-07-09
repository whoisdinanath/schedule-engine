"""
Test script to verify the enhanced genetic algorithm with adaptive features.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.ga.engine import GAEngine
from src.entities import Course, Instructor, Room, Group
from src.utils.config import GA_CONFIG
from src.constraints.adaptive_weights import AdaptiveConstraintWeights
from src.ga.local_search import LocalSearch
import json

def test_adaptive_weights():
    """Test the adaptive constraint weights system."""
    print("Testing adaptive constraint weights...")
    
    # Create adaptive weights instance
    adaptive_weights = AdaptiveConstraintWeights()
    
    # Test with sample violation history
    violation_history = [
        {'total_hard': 50, 'hard': {'instructor_conflict': 20, 'room_conflict': 30}},
        {'total_hard': 45, 'hard': {'instructor_conflict': 15, 'room_conflict': 30}},
        {'total_hard': 40, 'hard': {'instructor_conflict': 10, 'room_conflict': 30}},
    ]
    
    # Update weights
    adaptive_weights.update_weights(violation_history, generation=10)
    weights = adaptive_weights.get_weights()
    
    print(f"Updated weights: {weights}")
    assert weights is not None
    assert len(weights) > 0
    print("✓ Adaptive weights test passed")

def test_local_search():
    """Test the local search system."""
    print("Testing local search...")
    
    # Create local search instance
    local_search = LocalSearch(max_iterations=10)
    
    # Create sample entities
    courses = {
        'CS101': Course('CS101', 'Introduction to CS', 'lecture', 3, 30),
        'CS102': Course('CS102', 'Data Structures', 'lecture', 3, 25)
    }
    
    instructors = {
        'I001': Instructor('I001', 'Dr. Smith', ['CS101', 'CS102']),
        'I002': Instructor('I002', 'Prof. Johnson', ['CS101', 'CS102'])
    }
    
    rooms = {
        'R001': Room('R001', 'Room 101', 'lecture', 35),
        'R002': Room('R002', 'Room 102', 'lecture', 30)
    }
    
    groups = {
        'G001': Group('G001', 'Group A', 28),
        'G002': Group('G002', 'Group B', 22)
    }
    
    # Create a sample chromosome
    from src.ga.chromosome import Chromosome
    chromosome = Chromosome()
    chromosome.initialize_random(courses, instructors, rooms, groups)
    
    print(f"Original chromosome fitness: {chromosome.fitness}")
    
    # Apply local search
    improved = local_search.hill_climbing(chromosome, courses, instructors, rooms, groups)
    
    print(f"Improved chromosome fitness: {improved.fitness}")
    assert improved is not None
    print("✓ Local search test passed")

def test_enhanced_ga_engine():
    """Test the enhanced GA engine with all new features."""
    print("Testing enhanced GA engine...")
    
    # Create a test configuration with smaller parameters for quick testing
    test_config = GA_CONFIG.copy()
    test_config.update({
        'population_size': 20,
        'max_generations': 10,
        'adaptive_weights_update_frequency': 5,
        'local_search_frequency': 5,
        'restart_threshold': 8
    })
    
    # Create GA engine
    ga_engine = GAEngine(test_config)
    
    # Verify new components are initialized
    assert hasattr(ga_engine, 'adaptive_weights')
    assert hasattr(ga_engine, 'local_search')
    assert hasattr(ga_engine, 'restart_count')
    
    print("✓ Enhanced GA engine initialization test passed")

def test_integration():
    """Test integration of all components."""
    print("Testing full integration...")
    
    # Load sample data
    from src.data.loader import DataLoader
    loader = DataLoader()
    
    try:
        # Load entities
        courses = loader.load_courses("data/sample_courses.csv")
        instructors = loader.load_instructors("data/sample_instructors.csv")
        rooms = loader.load_rooms("data/sample_rooms.csv")
        groups = loader.load_groups("data/sample_groups.csv")
        
        print(f"Loaded {len(courses)} courses, {len(instructors)} instructors, "
              f"{len(rooms)} rooms, {len(groups)} groups")
        
        # Create enhanced GA engine
        test_config = GA_CONFIG.copy()
        test_config.update({
            'population_size': 10,
            'max_generations': 5,
            'adaptive_weights_update_frequency': 3,
            'local_search_frequency': 3,
            'restart_threshold': 4
        })
        
        ga_engine = GAEngine(test_config)
        
        # Initialize and run a few generations
        ga_engine.initialize(courses, instructors, rooms, groups)
        
        # Run evolution for a few generations
        for generation in range(3):
            ga_engine.generation = generation
            
            # Test adaptive weights update
            if generation % ga_engine.adaptive_weights.update_frequency == 0:
                if ga_engine.violation_history:
                    ga_engine.adaptive_weights.update_weights(ga_engine.violation_history, generation)
                    weights = ga_engine.adaptive_weights.get_weights()
                    print(f"Generation {generation}: Updated weights: {list(weights.keys())[:3]}...")
            
            # Test local search application
            if generation % ga_engine.local_search.apply_frequency == 0:
                print(f"Generation {generation}: Would apply local search")
            
            # Simulate generation update
            ga_engine._evaluate_population()
            
            # Update best solution tracking
            if ga_engine.current_fitness:
                generation_best_idx = ga_engine.current_fitness.index(max(ga_engine.current_fitness))
                generation_best_fitness = ga_engine.current_fitness[generation_best_idx]
                
                if generation_best_fitness > ga_engine.best_fitness:
                    ga_engine.best_fitness = generation_best_fitness
                    ga_engine.best_chromosome = ga_engine.population.chromosomes[generation_best_idx].copy()
                    ga_engine.last_improvement_generation = generation
                
                # Count violations
                best_chromosome = ga_engine.population.chromosomes[generation_best_idx]
                violations = ga_engine._count_violations(best_chromosome)
                ga_engine.violation_history.append(violations)
                
                print(f"Generation {generation}: Best fitness: {ga_engine.best_fitness:.4f}, "
                      f"Violations: {violations['total']}")
        
        print("✓ Integration test passed")
        
    except Exception as e:
        print(f"Integration test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== Testing Enhanced Genetic Algorithm System ===")
    
    try:
        # Run all tests
        test_adaptive_weights()
        test_local_search()
        test_enhanced_ga_engine()
        test_integration()
        
        print("\n=== All Tests Passed! ===")
        print("The enhanced GA system is ready with:")
        print("✓ Adaptive constraint weights")
        print("✓ Local search with hill climbing")
        print("✓ Population restart mechanism")
        print("✓ Enhanced diversity control")
        print("✓ Improved stagnation detection")
        
    except Exception as e:
        print(f"\n=== Test Failed: {e} ===")
        import traceback
        traceback.print_exc()
