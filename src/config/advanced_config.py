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
class AdvancedConfig:
    """Main configuration container"""

    environment: ConfigEnvironment = ConfigEnvironment.DEVELOPMENT
    ga_config: GeneticAlgorithmConfig = field(default_factory=GeneticAlgorithmConfig)
    constraint_config: ConstraintConfig = field(default_factory=ConstraintConfig)
    performance_config: PerformanceConfig = field(default_factory=PerformanceConfig)
    visualization_config: VisualizationConfig = field(
        default_factory=VisualizationConfig
    )
    logging_config: LoggingConfig = field(default_factory=LoggingConfig)

    # Data paths
    data_dir: str = "data"
    output_dir: str = "output"
    temp_dir: str = "temp"
    backup_dir: str = "backups"

    # Feature flags
    enable_experimental_features: bool = False
    enable_multi_objective: bool = False
    enable_interactive_mode: bool = False


class ConfigManager:
    """Advanced configuration management system"""

    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.config: Optional[AdvancedConfig] = None
        self.config_cache: Dict[str, Any] = {}
        self.environment = self._detect_environment()

    def _detect_environment(self) -> ConfigEnvironment:
        """Detect the current environment"""
        env_var = os.getenv("GENETICS_ENV", "development").lower()
        try:
            return ConfigEnvironment(env_var)
        except ValueError:
            logger.warning(
                f"Unknown environment '{env_var}', defaulting to development"
            )
            return ConfigEnvironment.DEVELOPMENT

    def load_config(self, config_path: Optional[str] = None) -> AdvancedConfig:
        """Load configuration from file or create default"""
        if config_path is None:
            config_path = self.config_dir / f"{self.environment.value}.yaml"

        config_path = Path(config_path)

        if config_path.exists():
            logger.info(f"Loading configuration from {config_path}")
            config_data = self._load_config_file(config_path)
            self.config = self._create_config_from_dict(config_data)
        else:
            logger.info("Creating default configuration")
            self.config = AdvancedConfig(environment=self.environment)
            self.save_config(config_path)

        self._validate_config()
        return self.config

    def _load_config_file(self, config_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML or JSON file"""
        try:
            with open(config_path, "r") as f:
                if (
                    config_path.suffix.lower() == ".yaml"
                    or config_path.suffix.lower() == ".yml"
                ):
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load config file {config_path}: {e}")
            raise

    def _create_config_from_dict(self, config_data: Dict[str, Any]) -> AdvancedConfig:
        """Create AdvancedConfig from dictionary"""
        # Handle nested configurations
        ga_config = GeneticAlgorithmConfig(**config_data.get("ga_config", {}))
        constraint_config = ConstraintConfig(**config_data.get("constraint_config", {}))
        performance_config = PerformanceConfig(
            **config_data.get("performance_config", {})
        )
        visualization_config = VisualizationConfig(
            **config_data.get("visualization_config", {})
        )
        logging_config = LoggingConfig(**config_data.get("logging_config", {}))

        # Remove nested configs from main dict
        main_config = {
            k: v
            for k, v in config_data.items()
            if k
            not in [
                "ga_config",
                "constraint_config",
                "performance_config",
                "visualization_config",
                "logging_config",
            ]
        }

        return AdvancedConfig(
            ga_config=ga_config,
            constraint_config=constraint_config,
            performance_config=performance_config,
            visualization_config=visualization_config,
            logging_config=logging_config,
            **main_config,
        )

    def save_config(self, config_path: Optional[Path] = None):
        """Save current configuration to file"""
        if self.config is None:
            raise ValueError("No configuration loaded")

        if config_path is None:
            config_path = self.config_dir / f"{self.environment.value}.yaml"

        config_dict = self._config_to_dict(self.config)

        try:
            with open(config_path, "w") as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
            logger.info(f"Configuration saved to {config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def _config_to_dict(self, config: AdvancedConfig) -> Dict[str, Any]:
        """Convert AdvancedConfig to dictionary for serialization"""
        return {
            "environment": config.environment.value,
            "ga_config": config.ga_config.__dict__,
            "constraint_config": {
                "hard_constraints": config.constraint_config.hard_constraints,
                "soft_constraints": config.constraint_config.soft_constraints,
                "adaptive_weights": config.constraint_config.adaptive_weights,
                "weight_adjustment_factor": config.constraint_config.weight_adjustment_factor,
                "constraint_priorities": config.constraint_config.constraint_priorities,
            },
            "performance_config": config.performance_config.__dict__,
            "visualization_config": {
                "enable_real_time": config.visualization_config.enable_real_time,
                "update_interval": config.visualization_config.update_interval,
                "chart_types": config.visualization_config.chart_types,
                "export_formats": config.visualization_config.export_formats,
                "color_scheme": config.visualization_config.color_scheme,
                "figure_size": list(config.visualization_config.figure_size),
                "dpi": config.visualization_config.dpi,
            },
            "logging_config": config.logging_config.__dict__,
            "data_dir": config.data_dir,
            "output_dir": config.output_dir,
            "temp_dir": config.temp_dir,
            "backup_dir": config.backup_dir,
            "enable_experimental_features": config.enable_experimental_features,
            "enable_multi_objective": config.enable_multi_objective,
            "enable_interactive_mode": config.enable_interactive_mode,
        }

    def _validate_config(self):
        """Validate configuration parameters"""
        if self.config is None:
            raise ValueError("No configuration loaded")

        # Validate GA parameters
        ga = self.config.ga_config
        if ga.population_size <= 0:
            raise ValueError("Population size must be positive")
        if ga.generations <= 0:
            raise ValueError("Generations must be positive")
        if not 0 <= ga.crossover_rate <= 1:
            raise ValueError("Crossover rate must be between 0 and 1")
        if not 0 <= ga.mutation_rate <= 1:
            raise ValueError("Mutation rate must be between 0 and 1")

        # Validate constraint weights
        for weight in self.config.constraint_config.hard_constraints.values():
            if weight < 0:
                raise ValueError("Constraint weights must be non-negative")

        # Validate performance settings
        perf = self.config.performance_config
        if perf.parallel_processes <= 0:
            raise ValueError("Parallel processes must be positive")
        if perf.cache_size <= 0:
            raise ValueError("Cache size must be positive")

        logger.info("Configuration validation passed")

    def get_config(self) -> AdvancedConfig:
        """Get current configuration"""
        if self.config is None:
            return self.load_config()
        return self.config

    def update_config(self, updates: Dict[str, Any]):
        """Update configuration with new values"""
        if self.config is None:
            self.load_config()

        # Apply updates (simplified - in practice you'd want more sophisticated merging)
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

        self._validate_config()
        logger.info("Configuration updated")

    def get_environment_config(self, environment: ConfigEnvironment) -> AdvancedConfig:
        """Get configuration for specific environment"""
        config_path = self.config_dir / f"{environment.value}.yaml"
        if config_path.exists():
            config_data = self._load_config_file(config_path)
            return self._create_config_from_dict(config_data)
        else:
            # Create default config for environment
            config = AdvancedConfig(environment=environment)
            # Apply environment-specific defaults
            if environment == ConfigEnvironment.TESTING:
                config.ga_config.generations = 10
                config.ga_config.population_size = 20
                config.logging_config.level = "DEBUG"
            elif environment == ConfigEnvironment.PRODUCTION:
                config.ga_config.generations = 500
                config.ga_config.population_size = 500
                config.performance_config.parallel_processes = 8
                config.logging_config.level = "WARNING"
            elif environment == ConfigEnvironment.OPTIMIZATION:
                config.ga_config.generations = 1000
                config.ga_config.population_size = 1000
                config.ga_config.adaptive_parameters = True
                config.performance_config.parallel_processes = 12

            return config

    def create_experiment_config(
        self, base_config: AdvancedConfig, experiment_params: Dict[str, Any]
    ) -> AdvancedConfig:
        """Create configuration for experiments"""
        import copy

        exp_config = copy.deepcopy(base_config)

        # Apply experiment parameters
        for key, value in experiment_params.items():
            if hasattr(exp_config.ga_config, key):
                setattr(exp_config.ga_config, key, value)

        return exp_config


# Global configuration manager instance
config_manager = ConfigManager()


def get_config() -> AdvancedConfig:
    """Get the global configuration instance"""
    return config_manager.get_config()


def load_config(config_path: Optional[str] = None) -> AdvancedConfig:
    """Load configuration from file"""
    return config_manager.load_config(config_path)


def save_config(config_path: Optional[str] = None):
    """Save current configuration"""
    config_manager.save_config(config_path)
