"""
GA Scheduler Module

Encapsulates NSGA-II genetic algorithm execution for course scheduling.
Extracted from monolithic main.py for better testability and separation of concerns.
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass, field
from deap import base, tools
import random
import time
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.table import Table
from rich.live import Live

from src.ga.population import generate_course_group_aware_population
from src.ga.operators.crossover import crossover_course_group_aware
from src.ga.operators.mutation import mutate_individual
from src.ga.evaluator.fitness import evaluate
from src.ga.evaluator.detailed_fitness import evaluate_detailed
from src.metrics.diversity import average_pairwise_diversity
from src.core.types import SchedulingContext

console = Console()


@dataclass
class GAConfig:
    """
    GA configuration parameters.

    Attributes:
        pop_size: Population size
        generations: Number of generations to evolve
        crossover_prob: Probability of crossover operation
        mutation_prob: Probability of mutation operation
        repair_config: Repair heuristics configuration dict (from ga_params.REPAIR_HEURISTICS_CONFIG)
    """

    pop_size: int
    generations: int
    crossover_prob: float
    mutation_prob: float
    repair_config: Dict = field(default_factory=dict)


@dataclass
class GAMetrics:
    """
    Tracks GA evolution metrics per generation.

    Attributes:
        hard_violations: Best hard constraint violations per generation
        soft_penalties: Best soft constraint penalties per generation
        diversity: Population diversity per generation
        detailed_hard: Per-constraint hard violation tracking
        detailed_soft: Per-constraint soft penalty tracking
        repair_stats: Repair statistics per generation
    """

    hard_violations: List[float] = field(default_factory=list)
    soft_penalties: List[float] = field(default_factory=list)
    diversity: List[float] = field(default_factory=list)
    detailed_hard: Dict[str, List[float]] = field(default_factory=dict)
    detailed_soft: Dict[str, List[float]] = field(default_factory=dict)
    repair_stats: List[Dict] = field(
        default_factory=list
    )  # NEW: Track repairs per generation


class GAScheduler:
    """
    Manages NSGA-II genetic algorithm execution for timetabling.

    This class encapsulates the entire GA lifecycle:
    - Toolbox initialization
    - Population generation and validation
    - Evolution loop execution
    - Metrics tracking
    - Best solution selection

    Usage:
        config = GAConfig(pop_size=50, generations=100, ...)
        scheduler = GAScheduler(config, context, hard_names, soft_names)
        scheduler.setup_toolbox()
        scheduler.initialize_population()
        scheduler.evolve()
        best = scheduler.get_best_solution()
    """

    def __init__(
        self,
        config: GAConfig,
        context: SchedulingContext,
        hard_constraint_names: List[str],
        soft_constraint_names: List[str],
        pool=None,  # NEW: Optional multiprocessing Pool
    ):
        """
        Initialize GA scheduler.

        Args:
            config: GA configuration parameters
            context: Scheduling context with courses, groups, etc.
            hard_constraint_names: Names of enabled hard constraints
            soft_constraint_names: Names of enabled soft constraints
            pool: Optional multiprocessing.Pool for parallel fitness evaluation
        """
        self.config = config
        self.context = context
        self.hard_constraint_names = hard_constraint_names
        self.soft_constraint_names = soft_constraint_names
        self.pool = pool  # NEW: Store pool for parallel evaluation

        self.toolbox = None
        self.population = None
        self.metrics = GAMetrics(
            detailed_hard={name: [] for name in hard_constraint_names},
            detailed_soft={name: [] for name in soft_constraint_names},
        )

    def setup_toolbox(self):
        """Initialize DEAP toolbox with operators."""
        self.toolbox = base.Toolbox()

        # NEW: Register parallel map if pool is provided
        if self.pool is not None:
            self.toolbox.register("map", self.pool.map)

        # Selection operator
        self.toolbox.register("select", tools.selNSGA2)

        # Population generation operators
        self.toolbox.register(
            "individual",
            generate_course_group_aware_population,
            n=1,
            context=self.context,
        )
        self.toolbox.register(
            "population", generate_course_group_aware_population, context=self.context
        )

        # Evaluation operator
        self.toolbox.register(
            "evaluate",
            evaluate,
            courses=self.context.courses,
            instructors=self.context.instructors,
            groups=self.context.groups,
            rooms=self.context.rooms,
        )

        # Genetic operators
        self.toolbox.register(
            "mate", crossover_course_group_aware, cx_prob=self.config.crossover_prob
        )
        self.toolbox.register(
            "mutate",
            mutate_individual,
            context=self.context,
            mut_prob=self.config.mutation_prob,
        )

    def initialize_population(self):
        """Create and evaluate initial population."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
            transient=True,
        ) as progress:
            task = progress.add_task("[cyan]Initializing Population...", total=2)

            self.population = self.toolbox.population(n=self.config.pop_size)
            progress.advance(task)

            # Validate gene alignment
            self._validate_population_structure()
            progress.advance(task)

        # Evaluate initial population
        console.print("[cyan]Evaluating Initial Population...[/cyan]")

        # Use toolbox.map for parallel evaluation when pool is available
        fitness_values = list(self.toolbox.map(self.toolbox.evaluate, self.population))

        for ind, fit in zip(self.population, fitness_values):
            ind.fitness.values = fit

    def evolve(self):
        """Run genetic algorithm evolution loop."""
        gen_times = []

        # Create progress bar (first line)
        progress_bar = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[cyan]{task.completed}/{task.total}"),
            console=console,
            refresh_per_second=10,
        )

        # Create time info bar (second line)
        time_bar = Progress(
            TextColumn("[dim]Elapsed:[/dim]"),
            TimeElapsedColumn(),
            TextColumn("•"),
            TextColumn("[dim]Remaining:[/dim]"),
            TimeRemainingColumn(),
            TextColumn("•"),
            TextColumn("[dark_red]{task.fields[speed_display]}[/dark_red]"),
            console=console,
            refresh_per_second=10,
        )

        # Combine both into a table for multi-line display
        progress_table = Table.grid()
        progress_table.add_row(progress_bar)
        progress_table.add_row(time_bar)

        with Live(progress_table, console=console, refresh_per_second=10):
            task1 = progress_bar.add_task(
                "[bold green]Evolution Progress",
                total=self.config.generations,
            )
            task2 = time_bar.add_task(
                "",
                total=self.config.generations,
                speed_display="--s/gen",
            )

            for gen in range(self.config.generations):
                gen_start = time.time()
                self._evolve_generation(gen, progress_bar)
                gen_time = time.time() - gen_start
                gen_times.append(gen_time)

                progress_bar.advance(task1)
                time_bar.advance(task2)

                # Calculate speed display
                if gen_times:
                    avg_gen_time = sum(gen_times) / len(gen_times)
                    if avg_gen_time < 1.0:
                        speed_display = f"{avg_gen_time*1000:.0f}ms/gen"
                    else:
                        speed_display = f"{avg_gen_time:.1f}s/gen"
                else:
                    speed_display = "--s/gen"

                time_bar.update(task2, speed_display=speed_display)

                # Early stopping if perfect solution found
                best = tools.selBest(self.population, 1)[0]
                if best.fitness.values[0] == 0:
                    console.print(
                        f"\n✓ [bold green]Perfect solution found at generation {gen + 1}![/bold green]"
                    )
                    break

    def _evolve_generation(self, gen: int, progress=None):
        """Execute one generation of evolution."""
        repair_config = self.config.repair_config
        generation_repair_stats = {
            "instructor_availability_fixes": 0,
            "overlap_fixes": 0,
            "room_fixes": 0,
            "instructor_conflict_fixes": 0,
            "qualification_fixes": 0,
            "room_type_fixes": 0,
            "clustering_fixes": 0,
            "session_count_fixes": 0,
            "total_fixes": 0,
        }

        # Selection
        offspring = self.toolbox.select(self.population, len(self.population))
        offspring = list(map(self.toolbox.clone, offspring))

        # Crossover
        for i in range(1, len(offspring), 2):
            if random.random() < self.config.crossover_prob:
                self.toolbox.mate(offspring[i - 1], offspring[i])
                del offspring[i - 1].fitness.values
                del offspring[i].fitness.values

                # Apply repairs after crossover if enabled
                if repair_config.get("enabled", False) and repair_config.get(
                    "apply_after_crossover", False
                ):
                    from src.ga.operators.repair import repair_individual

                    stats1 = repair_individual(
                        offspring[i - 1],
                        self.context,
                        max_iterations=repair_config.get("max_iterations", 3),
                    )
                    stats2 = repair_individual(
                        offspring[i],
                        self.context,
                        max_iterations=repair_config.get("max_iterations", 3),
                    )

                    # Aggregate all repair stats
                    for key in generation_repair_stats.keys():
                        if key in stats1 and key in stats2:
                            generation_repair_stats[key] += stats1[key] + stats2[key]

        # Mutation
        for mutant in offspring:
            if random.random() < self.config.mutation_prob:
                self.toolbox.mutate(mutant)
                del mutant.fitness.values

                # Apply repairs after mutation if enabled
                if repair_config.get("enabled", False) and repair_config.get(
                    "apply_after_mutation", False
                ):
                    from src.ga.operators.repair import repair_individual

                    # Check violation threshold if specified
                    threshold = repair_config.get("violation_threshold")
                    should_repair = True

                    if threshold is not None and mutant.fitness.valid:
                        should_repair = mutant.fitness.values[0] > threshold

                    if should_repair:
                        stats = repair_individual(
                            mutant,
                            self.context,
                            max_iterations=repair_config.get("max_iterations", 3),
                        )

                        # Aggregate all repair stats
                        for key in generation_repair_stats.keys():
                            if key in stats:
                                generation_repair_stats[key] += stats[key]

        # Evaluate invalid individuals
        invalid = [ind for ind in offspring if not ind.fitness.valid]
        if invalid:
            # Use toolbox.map for parallel evaluation when pool is available
            fitness_values = list(self.toolbox.map(self.toolbox.evaluate, invalid))
            for ind, fit in zip(invalid, fitness_values):
                ind.fitness.values = fit

        # Replacement: combine parents and offspring, select next generation
        combined = self.population + offspring
        self.population[:] = self.toolbox.select(combined, len(self.population))

        # Memetic mode: Apply intensive local search to elite individuals
        if repair_config.get("enabled", False) and repair_config.get(
            "memetic_mode", False
        ):
            from src.ga.operators.repair import repair_individual

            elite_percentage = repair_config.get("elite_percentage", 0.2)
            elite_count = max(1, int(elite_percentage * len(self.population)))
            elite_individuals = tools.selBest(self.population, elite_count)

            for individual in elite_individuals:
                stats = repair_individual(
                    individual,
                    self.context,
                    max_iterations=repair_config.get("memetic_iterations", 5),
                )

                # Invalidate fitness after repair
                del individual.fitness.values

                # Aggregate all memetic stats
                for key in generation_repair_stats.keys():
                    if key in stats:
                        generation_repair_stats[key] += stats[key]

            # Re-evaluate elite after memetic repair
            # Use toolbox.map for parallel evaluation when pool is available
            fitness_values = list(
                self.toolbox.map(self.toolbox.evaluate, elite_individuals)
            )
            for ind, fit in zip(elite_individuals, fitness_values):
                ind.fitness.values = fit

        # Store generation repair stats
        self.metrics.repair_stats.append(generation_repair_stats)

        # Track metrics
        self._track_metrics(gen)

    def _track_metrics(self, gen: int):
        """Record metrics for current generation."""
        # Basic metrics
        self.metrics.hard_violations.append(
            min(ind.fitness.values[0] for ind in self.population)
        )
        self.metrics.soft_penalties.append(
            min(ind.fitness.values[1] for ind in self.population)
        )
        self.metrics.diversity.append(average_pairwise_diversity(self.population))

        # Detailed constraint breakdown
        best = tools.selBest(self.population, 1)[0]
        hard_details, soft_details = evaluate_detailed(
            best,
            self.context.courses,
            self.context.instructors,
            self.context.groups,
            self.context.rooms,
        )

        for name in self.hard_constraint_names:
            self.metrics.detailed_hard[name].append(hard_details[name])

        for name in self.soft_constraint_names:
            self.metrics.detailed_soft[name].append(soft_details[name])

        # Periodic logging
        if gen % 10 == 0 or gen == self.config.generations - 1:
            self._log_generation_details(gen, best, hard_details, soft_details)

    def _log_generation_details(
        self, gen: int, best, hard_details: Dict, soft_details: Dict
    ):
        """Print detailed constraint breakdown."""
        console.print(
            f"\n[cyan]GEN {gen+1}[/cyan] Hard=[yellow]{best.fitness.values[0]:.0f}[/yellow], "
            f"Soft=[blue]{best.fitness.values[1]:.2f}[/blue]"
        )

        # Display repair statistics if enabled
        if self.config.repair_config.get("enabled", False) and gen < len(
            self.metrics.repair_stats
        ):
            repair_stats = self.metrics.repair_stats[gen]
            if repair_stats["total_fixes"] > 0:
                # Build repair summary with all non-zero categories
                repair_parts = []
                if repair_stats.get("instructor_availability_fixes", 0) > 0:
                    repair_parts.append(
                        f"instr_avail:{repair_stats['instructor_availability_fixes']}"
                    )
                if repair_stats.get("overlap_fixes", 0) > 0:
                    repair_parts.append(f"group:{repair_stats['overlap_fixes']}")
                if repair_stats.get("room_fixes", 0) > 0:
                    repair_parts.append(f"room:{repair_stats['room_fixes']}")
                if repair_stats.get("instructor_conflict_fixes", 0) > 0:
                    repair_parts.append(
                        f"instr:{repair_stats['instructor_conflict_fixes']}"
                    )
                if repair_stats.get("qualification_fixes", 0) > 0:
                    repair_parts.append(f"qual:{repair_stats['qualification_fixes']}")
                if repair_stats.get("room_type_fixes", 0) > 0:
                    repair_parts.append(f"type:{repair_stats['room_type_fixes']}")
                if repair_stats.get("clustering_fixes", 0) > 0:
                    repair_parts.append(f"cluster:{repair_stats['clustering_fixes']}")
                if repair_stats.get("session_count_fixes", 0) > 0:
                    repair_parts.append(f"count:{repair_stats['session_count_fixes']}")

                repair_summary = ", ".join(repair_parts) if repair_parts else "misc"
                console.print(
                    f"   [green]Repairs: {repair_stats['total_fixes']} fixes[/green] ({repair_summary})"
                )

        if best.fitness.values[0] > 0:
            console.print(
                f"   [yellow]HARD Total: {best.fitness.values[0]:.0f}[/yellow]"
            )
            for name, value in hard_details.items():
                if value > 0:
                    console.print(f"      • {name}: {value}")

        if best.fitness.values[1] > 0:
            console.print(f"   [blue]SOFT Total: {best.fitness.values[1]:.2f}[/blue]")
            for name, value in soft_details.items():
                if value > 0:
                    console.print(f"      • {name}: {value:.2f}")

    def get_best_solution(self):
        """
        Select best solution from final population.

        Prefers feasible solutions (hard constraints satisfied) with
        lowest soft constraint penalty. If no feasible solution exists,
        returns the solution with fewest hard constraint violations.

        Returns:
            Best individual from the final population
        """
        pareto_front = tools.sortNondominated(
            self.population, len(self.population), first_front_only=True
        )[0]

        # Prefer feasible solutions (no hard constraint violations)
        feasible = [ind for ind in pareto_front if ind.fitness.values[0] == 0]

        if feasible:
            # Among feasible solutions, select one with minimum soft penalty
            return min(feasible, key=lambda ind: ind.fitness.values[1])
        else:
            # No feasible solution, return best from Pareto front
            return pareto_front[0]

    def _validate_population_structure(self):
        """
        Validate gene alignment across population.

        Ensures all individuals have matching (course, group) pairs at each
        gene position. This is critical for position-independent crossover.

        Raises:
            ValueError: If population structure is invalid
        """
        if not self.population:
            return

        reference = [
            (gene.course_id, gene.course_type, tuple(sorted(gene.group_ids)))
            for gene in self.population[0]
        ]
        reference_set = set(reference)

        for idx, individual in enumerate(self.population[1:], start=1):
            current = [
                (gene.course_id, gene.course_type, tuple(sorted(gene.group_ids)))
                for gene in individual
            ]
            current_set = set(current)

            if current_set != reference_set:
                missing = reference_set - current_set
                extra = current_set - reference_set
                raise ValueError(
                    f"[X] Gene alignment validation FAILED!\n"
                    f"   Individual {idx} has different structure than Individual 0.\n"
                    f"   Missing pairs: {missing}\n"
                    f"   Extra pairs: {extra}\n"
                    f"   This indicates a bug in population generation."
                )

            # Check for duplicates within individual
            if len(current) != len(current_set):
                duplicates = [x for x in current if current.count(x) > 1]
                raise ValueError(
                    f"[X] Individual {idx} contains DUPLICATE (course, course_type, group) pairs!\n"
                    f"   Duplicates: {set(duplicates)}"
                )
