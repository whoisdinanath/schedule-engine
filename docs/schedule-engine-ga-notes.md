# Schedule Engine GA Notes

## GA Rationale
- Multi-objective course scheduling framed as minimizing hard violations then soft penalties; solved with NSGA-II following Deb et al. (2002) domination ordering.
- Chromosome encodes one `SessionGene` per course-group pairing; genes carry room, instructor, and quantum set to respect resource clashes.
- Fitness emphasises feasibility first via hard constraint count, then timetable quality (soft penalties) to keep Pareto frontier interpretable.
- Diversity tracked through average pairwise Hamming distance to avoid convergence to identical timetables during evolution.

## Implementation Snapshot
- Data ingestion starts with `src/encoder/input_encoder.py`, which builds entities (`src/entities/*`) and translates availability windows with `QuantumTimeSystem` quanta.
- Population seeding in `src/ga/population.py` links courses, groups, and available slots before dispatching to DEAP's NSGA-II loop configured in `main.py`.
- Mutation and crossover live in `src/ga/operators/{mutation,crossover}.py`; both assume the context dictionary packaged in `src/ga/individual.py` includes courses, instructors, rooms, groups, and precomputed quanta.
- Evaluation flows through `src/ga/evaluator/fitness.py`, which decodes chromosomes using `src/decoder/individual_decoder.py` and applies hard/soft constraint modules.
- Export pipeline `src/exporter/exporter.py` captures schedules and plots into `output/evaluation_<timestamp>/`, with calendar formatting driven by `config/calendar_config.py`.
