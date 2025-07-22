"""
Streamlined Configuration System for Genetics Timetabling
Provides essential configuration parameters for genetic algorithm optimization.
"""

import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class GeneticAlgorithmConfig:
    """Genetic Algorithm configuration parameters"""

    population_size: int = 200
    generations: int = 200
    elite_size: int = 3
    crossover_rate: float = 0.8
    mutation_rate: float = 0.2
    tournament_size: int = 20
    selection_method: str = "tournament"
    crossover_method: str = "two_point"
    mutation_method: str = "adaptive"
    max_generations: int = 500
    target_fitness: float = 0.0
    stagnation_limit: int = 200
    time_limit_minutes: int = 30
    diversity_threshold: float = 0.1
    adaptive_parameters: bool = True
    parallel_evaluation: bool = True
    memory_limit_mb: int = 2000


@dataclass
class ConstraintConfig:
    """Constraint configuration with adaptive weights"""

    hard_constraints: Dict[str, float] = field(
        default_factory=lambda: {
            "instructor_conflict": 100.0,
            "room_conflict": 100.0,
            "group_conflict": 100.0,
            "course_group_isolation": 100.0,
            "room_capacity": 100.0,
            "instructor_qualification": 100.0,
            "room_type_mismatch": 100.0,
            "availability_violation": 100.0,
        }
    )

    soft_constraints: Dict[str, float] = field(
        default_factory=lambda: {
            "instructor_preference": 10.0,
            "room_utilization": 5.0,
            "schedule_compactness": 8.0,
            "workload_balance": 6.0,
            "student_break_time": 7.0,
            "room_consistency": 4.0,
            "time_slot_distribution": 3.0,
            "lunch_break_respect": 9.0,
            "early_late_penalty": 5.0,
            "consecutive_classes": 2.0,
        }
    )

    adaptive_weights: bool = True
    weight_adjustment_factor: float = 0.05
    constraint_priorities: Dict[str, int] = field(
        default_factory=lambda: {
            "instructor_conflict": 1,
            "room_conflict": 1,
            "group_conflict": 1,
            "room_capacity": 2,
            "instructor_qualification": 2,
        }
    )


@dataclass
class PerformanceConfig:
    """Performance and optimization configuration"""

    enable_caching: bool = True
    cache_size: int = 1000
    parallel_processes: int = 4
    memory_monitoring: bool = True
    profiling_enabled: bool = False
    batch_evaluation: bool = True
    lazy_evaluation: bool = True
    checkpoint_interval: int = 50
    auto_save: bool = True


@dataclass
class VisualizationConfig:
    """Visualization configuration"""

    enable_real_time: bool = False
    update_interval: int = 5
    chart_types: List[str] = field(
        default_factory=lambda: [
            "fitness_evolution",
            "constraint_violations",
            "diversity_metrics",
        ]
    )
    export_formats: List[str] = field(default_factory=lambda: ["pdf", "png", "svg"])
    color_scheme: str = "default"
    figure_size: tuple = (12, 8)
    dpi: int = 300


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_output: bool = True
    console_output: bool = True
    log_dir: str = "logs"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    structured_logging: bool = True


@dataclass
class CleanConfig:
    """Main configuration container"""

    ga_config: GeneticAlgorithmConfig = field(default_factory=GeneticAlgorithmConfig)
    constraint_config: ConstraintConfig = field(default_factory=ConstraintConfig)
    performance_config: PerformanceConfig = field(default_factory=PerformanceConfig)
    visualization_config: VisualizationConfig = field(
        default_factory=VisualizationConfig
    )
    logging_config: LoggingConfig = field(default_factory=LoggingConfig)

    def __post_init__(self):
        """Post-initialization setup"""
        self._setup_logging()
        self._create_directories()

    def _setup_logging(self):
        """Setup logging configuration"""
        log_level = getattr(logging, self.logging_config.level.upper())
        logging.basicConfig(
            level=log_level,
            format=self.logging_config.format,
            handlers=[
                logging.FileHandler(
                    Path(self.logging_config.log_dir) / "genetics_timetabling.log"
                ),
                logging.StreamHandler(),
            ],
        )

    def _create_directories(self):
        """Create necessary directories"""
        directories = [
            self.logging_config.log_dir,
            "output",
            "cache",
            "checkpoints",
        ]
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "ga_config": self.ga_config.__dict__,
            "constraint_config": self.constraint_config.__dict__,
            "performance_config": self.performance_config.__dict__,
            "visualization_config": self.visualization_config.__dict__,
            "logging_config": self.logging_config.__dict__,
        }

    def save_to_file(self, path: str):
        """Save configuration to JSON file"""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_file(cls, path: str) -> "CleanConfig":
        """Load configuration from JSON file"""
        with open(path, "r") as f:
            data = json.load(f)

        config = cls()
        if "ga_config" in data:
            for key, value in data["ga_config"].items():
                setattr(config.ga_config, key, value)
        if "constraint_config" in data:
            for key, value in data["constraint_config"].items():
                setattr(config.constraint_config, key, value)
        if "performance_config" in data:
            for key, value in data["performance_config"].items():
                setattr(config.performance_config, key, value)
        if "visualization_config" in data:
            for key, value in data["visualization_config"].items():
                setattr(config.visualization_config, key, value)
        if "logging_config" in data:
            for key, value in data["logging_config"].items():
                setattr(config.logging_config, key, value)

        return config

    def validate(self) -> List[str]:
        """Validate configuration parameters"""
        errors = []

        # Validate GA parameters
        if self.ga_config.population_size <= 0:
            errors.append("Population size must be positive")
        if self.ga_config.generations <= 0:
            errors.append("Generations must be positive")
        if not 0 <= self.ga_config.crossover_rate <= 1:
            errors.append("Crossover rate must be between 0 and 1")
        if not 0 <= self.ga_config.mutation_rate <= 1:
            errors.append("Mutation rate must be between 0 and 1")

        # Validate performance parameters
        if self.performance_config.cache_size <= 0:
            errors.append("Cache size must be positive")
        if self.performance_config.parallel_processes <= 0:
            errors.append("Parallel processes must be positive")

        return errors

    def get_optimized_config(self) -> "CleanConfig":
        """Get optimized configuration for better performance"""
        config = CleanConfig()

        # Optimize GA parameters
        config.ga_config.population_size = min(
            300, max(100, self.ga_config.population_size)
        )
        config.ga_config.generations = min(1000, max(50, self.ga_config.generations))
        config.ga_config.elite_size = max(2, min(10, self.ga_config.elite_size))
        config.ga_config.tournament_size = max(
            3, min(15, self.ga_config.tournament_size)
        )
        config.ga_config.adaptive_parameters = True
        config.ga_config.parallel_evaluation = True

        # Optimize performance parameters
        config.performance_config.enable_caching = True
        config.performance_config.cache_size = 5000
        config.performance_config.batch_evaluation = True
        config.performance_config.lazy_evaluation = True

        # Copy other configurations
        config.constraint_config = self.constraint_config
        config.visualization_config = self.visualization_config
        config.logging_config = self.logging_config

        return config


# Global configuration instance
_config_instance = None


def get_config() -> CleanConfig:
    """Get global configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = CleanConfig()
    return _config_instance


def set_config(config: CleanConfig):
    """Set global configuration instance"""
    global _config_instance
    _config_instance = config


def load_config_from_file(path: str) -> CleanConfig:
    """Load configuration from file and set as global"""
    config = CleanConfig.from_file(path)
    set_config(config)
    return config


def create_default_config_file(path: str = "config.json"):
    """Create default configuration file"""
    config = CleanConfig()
    config.save_to_file(path)
    return config
