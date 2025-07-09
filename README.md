# Pure Genetic Algorithm-Based University Course Timetabling System

## Overview

This system implements a **PURE Genetic Algorithm (GA)** approach to solve the University Course Timetabling Problem (UCTP). It generates optimized course schedules by satisfying hard constraints and minimizing soft constraint violations using only genetic operators - no local search or hybrid optimization techniques.

## Key Features

- **Pure GA Implementation**: Uses only selection, crossover, mutation, and elitism
- **No Local Search**: No hill climbing, simulated annealing, or other local optimization
- **Simplified Room Model**: Rooms are always available (no room availability constraints)
- **Data Ingestion**: Supports CSV and JSON input formats
- **Entity Modeling**: Comprehensive modeling of courses, instructors, rooms, and student groups
- **Genetic Algorithm Engine**: Customizable GA with multiple genetic operators
- **Constraint Handling**: Strict enforcement of hard constraints and optimization of soft constraints
- **Fitness Evaluation**: Multi-objective fitness function with configurable weights
- **Output Generation**: Export to CSV, Excel, and tabular formats
- **Visualization**: Performance monitoring and schedule visualization
- **Logging**: Comprehensive logging and debugging capabilities

## Project Structure

```
genetics/
├── src/
│   ├── __init__.py
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── course.py
│   │   ├── instructor.py
│   │   ├── room.py
│   │   └── group.py
│   ├── data/
│   │   ├── __init__.py
│   │   ├── ingestion.py
│   │   └── validation.py
│   ├── ga/
│   │   ├── __init__.py
│   │   ├── chromosome.py
│   │   ├── population.py
│   │   ├── operators.py
│   │   └── engine.py
│   ├── constraints/
│   │   ├── __init__.py
│   │   ├── hard_constraints.py
│   │   ├── soft_constraints.py
│   │   └── checker.py
│   ├── fitness/
│   │   ├── __init__.py
│   │   └── evaluator.py
│   ├── output/
│   │   ├── __init__.py
│   │   └── generator.py
│   ├── visualization/
│   │   ├── __init__.py
│   │   └── charts.py
│   └── utils/
│       ├── __init__.py
│       ├── config.py
│       └── logger.py
├── data/
│   ├── sample_courses.csv
│   ├── sample_instructors.csv
│   ├── sample_rooms.csv
│   └── sample_groups.csv
├── tests/
├── examples/
│   └── basic_example.py
├── requirements.txt
└── main.py
```

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd genetics
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from main import TimetablingSystem

# Initialize system
system = TimetablingSystem()

# Load data
system.load_data('data/sample_courses.csv', 'data/sample_instructors.csv',
                 'data/sample_rooms.csv', 'data/sample_groups.csv')

# Run optimization
best_schedule = system.optimize()

# Export results
system.export_schedule(best_schedule, 'output/schedule.csv')
```

### Configuration

The system can be configured through `src/utils/config.py`:

```python
GA_CONFIG = {
    'population_size': 50,
    'generations': 100,
    'crossover_rate': 0.8,
    'mutation_rate': 0.1,
    'elitism_rate': 0.1,
    'tournament_size': 5
}
```

## Data Format

### Courses (CSV)

```csv
course_id,name,sessions_per_week,duration,required_room_type,group_ids,qualified_instructor_ids
CS101,Introduction to Programming,2,90,lab,"1,2","1,2,3"
```

### Instructors (CSV)

```csv
instructor_id,name,qualified_courses,available_slots,preferred_slots
1,Dr. Smith,"CS101,CS102","mon_09:00-17:00,tue_09:00-17:00","mon_10:00-12:00"
```

### Rooms (CSV)

```csv
room_id,name,capacity,type,available_slots
R101,Computer Lab 1,30,lab,"mon_08:00-18:00,tue_08:00-18:00"
```

### Groups (CSV)

```csv
group_id,name,student_count,enrolled_courses
1,CS Year 1,25,"CS101,MATH101"
```

## Constraints

### Hard Constraints

- No instructor/room conflicts
- Room capacity constraints  
- Instructor qualification requirements
- Student group availability
- **Note**: Rooms are always available (no room availability constraints)

### Soft Constraints

- Instructor time preferences
- Compact schedules
- Room consistency
- Balanced workload distribution

## Performance

- Handles 20-50 courses within 2-5 minutes
- Scales linearly with problem size
- Memory usage < 500MB for typical instances
