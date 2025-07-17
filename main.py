#!/usr/bin/env python3
"""
Main execution file for the University Course Timetabling Problem (UCTP) solver.
This script demonstrates a simple instance of the genetic algorithm-based timetabling system.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
sys.path.append(str(Path(__file__).parent / "src"))

from src.ga_deap.system import TimetablingSystem
from src.utils.logger import get_logger, setup_logging
from src.utils.config import GA_CONFIG


def main():
    """
    Main function to run a simple UCTP instance using the genetic algorithm.
    """
    # Setup logging
    setup_logging(level="INFO", log_dir="logs", console_output=True, file_output=True)
    logger = get_logger("main")
    
    logger.info("=" * 60)
    logger.info("University Course Timetabling Problem (UCTP) Solver")
    logger.info("Pure Genetic Algorithm Implementation")
    logger.info("=" * 60)
    
    try:
        # Initialize the timetabling system
        logger.info("Initializing Timetabling System...")
        system = TimetablingSystem(data_path="data")
        
        # Load data
        logger.info("Loading data from JSON files...")
        success = system.load_data()
        
        if not success:
            logger.error("Failed to load data. Exiting...")
            return False
        
        # Validate data
        logger.info("Validating loaded data...")
        is_valid, issues = system.validate_data()
        
        if not is_valid:
            logger.error("Data validation failed:")
            for issue in issues:
                logger.error(f"  - {issue}")
            return False
        
        logger.info("Data validation successful!")
        
        # Print data summary
        logger.info("Data Summary:")
        logger.info(f"  - Courses: {len(system.courses)}")
        logger.info(f"  - Instructors: {len(system.instructors)}")
        logger.info(f"  - Groups: {len(system.groups)}")
        logger.info(f"  - Rooms: {len(system.rooms)}")
        
        # Configure GA parameters for this simple instance
        generations = 50
        population_size = 100
        
        logger.info(f"Starting optimization with {generations} generations and population size {population_size}")
        logger.info("GA Configuration:")
        logger.info(f"  - Crossover Rate: {GA_CONFIG['crossover_rate']}")
        logger.info(f"  - Mutation Rate: {GA_CONFIG['mutation_rate']}")
        logger.info(f"  - Tournament Size: {GA_CONFIG['tournament_size']}")
        
        # Run the genetic algorithm
        start_time = datetime.now()
        best_solution = system.run_optimization(
            generations=generations, 
            population_size=population_size
        )
        end_time = datetime.now()
        
        optimization_time = (end_time - start_time).total_seconds()
        logger.info(f"Optimization completed in {optimization_time:.2f} seconds")
        
        # Get solution summary
        summary = system.get_solution_summary()
        logger.info("Solution Summary:")
        for key, value in summary.items():
            logger.info(f"  - {key}: {value}")
        
        # Export the schedule
        logger.info("Exporting schedule...")
        readable_schedule = system.export_schedule(format="readable")
        
        # Save to file
        output_file = Path("output") / f"schedule_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(readable_schedule)
        
        logger.info(f"Schedule exported to: {output_file}")
        
        # Display first few sessions of the schedule
        logger.info("\nFirst few scheduled sessions:")
        print("\n" + "="*80)
        print("SCHEDULE PREVIEW:")
        print("="*80)
        
        lines = readable_schedule.split('\n')
        for i, line in enumerate(lines[:20]):  # Show first 20 lines
            print(line)
        
        if len(lines) > 20:
            print(f"\n... and {len(lines) - 20} more lines")
        
        print("="*80)
        logger.info("UCTP solving completed successfully!")
        
        return True
        
    except Exception as e:
        logger.exception(f"An error occurred during execution: {str(e)}")
        return False
    
    finally:
        logger.info("Execution finished.")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
