"""
Logging utilities for the Genetic Algorithm-based Timetabling System.
Provides structured logging with different levels and outputs.
"""

import logging
import logging.handlers
import os
import sys
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        # Add color to levelname
        if record.levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['RESET']}"
            )
        
        return super().format(record)


class TimetablingLogger:
    """
    Custom logger class for the timetabling system.
    Provides structured logging with file and console outputs.
    """
    
    def __init__(self, name: str, log_dir: str = "logs"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Setup handlers
        self._setup_file_handler()
        self._setup_console_handler()
        
        # Performance tracking
        self.start_time = None
        self.metrics = {}
    
    def _setup_file_handler(self):
        """Setup file handler for logging to file."""
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = self.log_dir / f"{self.name}_{timestamp}.log"
        
        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # File formatter (detailed)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        
        self.logger.addHandler(file_handler)
    
    def _setup_console_handler(self):
        """Setup console handler for logging to stdout."""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Console formatter (colored and concise)
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        
        self.logger.addHandler(console_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, extra=kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, extra=kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, extra=kwargs)
    
    def start_timing(self, operation: str):
        """Start timing an operation."""
        self.start_time = datetime.now()
        self.info(f"Starting {operation}...")
    
    def end_timing(self, operation: str):
        """End timing and log duration."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            self.info(f"Completed {operation} in {duration.total_seconds():.2f} seconds")
            return duration.total_seconds()
        return 0
    
    def log_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics."""
        self.metrics.update(metrics)
        metrics_str = ", ".join([f"{k}: {v}" for k, v in metrics.items()])
        self.info(f"Metrics - {metrics_str}")
    
    def log_ga_generation(self, generation: int, best_fitness: float, 
                         avg_fitness: float, violations: int):
        """Log genetic algorithm generation information."""
        self.info(f"Generation {generation:3d} - "
                 f"Best: {best_fitness:8.4f}, "
                 f"Avg: {avg_fitness:8.4f}, "
                 f"Violations: {int(violations):3d}")
    
    def log_constraint_violations(self, violations: Dict[str, int]):
        """Log constraint violation details."""
        if violations:
            violation_str = ", ".join([f"{k}: {v}" for k, v in violations.items() if v > 0])
            self.warning(f"Constraint violations - {violation_str}")
        else:
            self.info("No constraint violations detected")
    
    def log_solution_quality(self, fitness: float, hard_violations: int, 
                           soft_violations: int):
        """Log solution quality metrics."""
        self.info(f"Solution Quality - "
                 f"Fitness: {fitness:.4f}, "
                 f"Hard violations: {hard_violations}, "
                 f"Soft violations: {soft_violations}")
    
    def log_data_summary(self, courses: int, instructors: int, 
                        rooms: int, groups: int):
        """Log data loading summary."""
        self.info(f"Data loaded - "
                 f"Courses: {courses}, "
                 f"Instructors: {instructors}, "
                 f"Rooms: {rooms}, "
                 f"Groups: {groups}")
    
    def exception(self, message: str, exc_info=True):
        """Log exception with traceback."""
        self.logger.exception(message, exc_info=exc_info)


# Global logger registry
_loggers: Dict[str, TimetablingLogger] = {}


def get_logger(name: str, log_dir: str = "logs") -> TimetablingLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name (usually class name)
        log_dir: Directory for log files
    
    Returns:
        TimetablingLogger instance
    """
    if name not in _loggers:
        _loggers[name] = TimetablingLogger(name, log_dir)
    
    return _loggers[name]


def setup_logging(level: str = "INFO", log_dir: str = "logs", 
                 console_output: bool = True, file_output: bool = True):
    """
    Setup global logging configuration.
    
    Args:
        level: Logging level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
        log_dir: Directory for log files
        console_output: Whether to output to console
        file_output: Whether to output to file
    """
    # Create log directory
    Path(log_dir).mkdir(exist_ok=True)
    
    # Set logging level
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Setup handlers based on parameters
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(numeric_level)
        
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
    
    if file_output:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = Path(log_dir) / f"timetabling_{timestamp}.log"
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)


def log_system_info():
    """Log system information."""
    logger = get_logger("SystemInfo")
    
    logger.info("="*50)
    logger.info("Genetic Algorithm Timetabling System Started")
    logger.info("="*50)
    
    # Python version
    logger.info(f"Python version: {sys.version}")
    
    # System information
    import platform
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Architecture: {platform.architecture()[0]}")
    
    # Memory information (if available)
    try:
        import psutil
        memory = psutil.virtual_memory()
        logger.info(f"Total memory: {memory.total / (1024**3):.1f} GB")
        logger.info(f"Available memory: {memory.available / (1024**3):.1f} GB")
    except ImportError:
        logger.debug("psutil not available - memory info not logged")
    
    logger.info("="*50)


# Setup default logging
setup_logging()
