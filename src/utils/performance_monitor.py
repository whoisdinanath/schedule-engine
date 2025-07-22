"""
Performance Monitoring and Optimization System
Provides comprehensive performance tracking, profiling, and optimization recommendations.
"""

import time
import psutil
import threading
import functools
import gc
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from collections import defaultdict, deque
import logging
import json
from pathlib import Path
import cProfile
import pstats
import io
from contextlib import contextmanager
import weakref

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics data structure"""

    function_name: str
    execution_time: float
    memory_usage: float
    cpu_usage: float
    call_count: int
    timestamp: float
    parameters: Dict[str, Any] = field(default_factory=dict)
    optimization_suggestions: List[str] = field(default_factory=list)


@dataclass
class SystemMetrics:
    """System-wide performance metrics"""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_available: float
    disk_usage: float
    process_memory: float
    process_cpu: float
    thread_count: int
    file_descriptors: int


class PerformanceProfiler:
    """Advanced performance profiler with automatic optimization suggestions"""

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.metrics_history: List[PerformanceMetrics] = []
        self.system_metrics_history: List[SystemMetrics] = []
        self.function_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self.bottlenecks: List[str] = []
        self.optimization_suggestions: Dict[str, List[str]] = defaultdict(list)

        # Monitoring thread
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None

        # Performance thresholds
        self.slow_function_threshold = 1.0  # seconds
        self.memory_threshold = 80.0  # percentage
        self.cpu_threshold = 90.0  # percentage

        # Caching for optimization
        self.function_cache: Dict[str, Any] = {}
        self.cache_hits = 0
        self.cache_misses = 0

        # Memory tracking
        self.memory_snapshots: deque = deque(maxlen=100)
        self.memory_leak_detection = True

        # Process handle
        self.process = psutil.Process()

    def start_monitoring(self):
        """Start continuous system monitoring"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitor_system)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop system monitoring"""
        if self.monitoring_active:
            self.monitoring_active = False
            if self.monitoring_thread:
                self.monitoring_thread.join()
            logger.info("Performance monitoring stopped")

    def _monitor_system(self):
        """Monitor system metrics continuously"""
        while self.monitoring_active:
            try:
                metrics = SystemMetrics(
                    timestamp=time.time(),
                    cpu_percent=psutil.cpu_percent(interval=None),
                    memory_percent=psutil.virtual_memory().percent,
                    memory_available=psutil.virtual_memory().available,
                    disk_usage=psutil.disk_usage("/").percent,
                    process_memory=self.process.memory_info().rss / 1024 / 1024,  # MB
                    process_cpu=self.process.cpu_percent(),
                    thread_count=self.process.num_threads(),
                    file_descriptors=(
                        self.process.num_fds()
                        if hasattr(self.process, "num_fds")
                        else 0
                    ),
                )

                self.system_metrics_history.append(metrics)

                # Check for performance issues
                self._check_performance_issues(metrics)

                # Memory leak detection
                if self.memory_leak_detection:
                    self._detect_memory_leaks(metrics)

                time.sleep(self.monitoring_interval)

            except Exception as e:
                logger.error(f"Error in system monitoring: {e}")
                time.sleep(self.monitoring_interval)

    def _check_performance_issues(self, metrics: SystemMetrics):
        """Check for performance issues and generate alerts"""
        if metrics.memory_percent > self.memory_threshold:
            logger.warning(f"High memory usage: {metrics.memory_percent:.1f}%")
            self._add_optimization_suggestion(
                "system", "Consider reducing memory usage"
            )

        if metrics.cpu_percent > self.cpu_threshold:
            logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")
            self._add_optimization_suggestion(
                "system", "Consider optimizing CPU-intensive operations"
            )

        if metrics.process_memory > 1000:  # 1GB
            logger.warning(f"High process memory: {metrics.process_memory:.1f}MB")
            self._add_optimization_suggestion(
                "system", "Consider memory optimization techniques"
            )

    def _detect_memory_leaks(self, metrics: SystemMetrics):
        """Detect potential memory leaks"""
        self.memory_snapshots.append(metrics.process_memory)

        if len(self.memory_snapshots) >= 10:
            # Check for consistent memory growth
            recent_memory = list(self.memory_snapshots)[-5:]
            if all(
                recent_memory[i] > recent_memory[i - 1]
                for i in range(1, len(recent_memory))
            ):
                logger.warning(
                    "Potential memory leak detected - consistent memory growth"
                )
                self._add_optimization_suggestion(
                    "memory", "Investigate potential memory leaks"
                )

    def _add_optimization_suggestion(self, category: str, suggestion: str):
        """Add optimization suggestion"""
        if suggestion not in self.optimization_suggestions[category]:
            self.optimization_suggestions[category].append(suggestion)

    def profile_function(self, func: Callable, *args, **kwargs) -> tuple:
        """Profile a single function execution"""
        start_time = time.time()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        start_cpu = self.process.cpu_percent()

        # Execute function
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error executing {func.__name__}: {e}")
            raise

        end_time = time.time()
        end_memory = self.process.memory_info().rss / 1024 / 1024
        end_cpu = self.process.cpu_percent()

        # Calculate metrics
        execution_time = end_time - start_time
        memory_usage = end_memory - start_memory
        cpu_usage = end_cpu - start_cpu

        # Create metrics
        metrics = PerformanceMetrics(
            function_name=func.__name__,
            execution_time=execution_time,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            call_count=1,
            timestamp=start_time,
            parameters={"args_count": len(args), "kwargs_count": len(kwargs)},
        )

        # Add performance suggestions
        if execution_time > self.slow_function_threshold:
            metrics.optimization_suggestions.append(
                "Function is slow - consider optimization"
            )

        if memory_usage > 100:  # 100MB
            metrics.optimization_suggestions.append(
                "High memory usage - consider memory optimization"
            )

        self.metrics_history.append(metrics)
        self._update_function_stats(func.__name__, metrics)

        return result, metrics

    def _update_function_stats(self, function_name: str, metrics: PerformanceMetrics):
        """Update function statistics"""
        stats = self.function_stats[function_name]

        if "total_calls" not in stats:
            stats["total_calls"] = 0
            stats["total_time"] = 0.0
            stats["max_time"] = 0.0
            stats["min_time"] = float("inf")
            stats["total_memory"] = 0.0
            stats["max_memory"] = 0.0

        stats["total_calls"] += 1
        stats["total_time"] += metrics.execution_time
        stats["max_time"] = max(stats["max_time"], metrics.execution_time)
        stats["min_time"] = min(stats["min_time"], metrics.execution_time)
        stats["total_memory"] += metrics.memory_usage
        stats["max_memory"] = max(stats["max_memory"], metrics.memory_usage)
        stats["avg_time"] = stats["total_time"] / stats["total_calls"]
        stats["avg_memory"] = stats["total_memory"] / stats["total_calls"]

        # Check for bottlenecks
        if stats["avg_time"] > self.slow_function_threshold:
            if function_name not in self.bottlenecks:
                self.bottlenecks.append(function_name)
                logger.warning(f"Bottleneck detected: {function_name}")

    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        report = {
            "summary": {
                "monitoring_duration": time.time()
                - (
                    self.system_metrics_history[0].timestamp
                    if self.system_metrics_history
                    else time.time()
                ),
                "total_functions_profiled": len(self.function_stats),
                "total_function_calls": sum(
                    stats["total_calls"] for stats in self.function_stats.values()
                ),
                "bottlenecks_detected": len(self.bottlenecks),
                "cache_hit_rate": (
                    self.cache_hits / (self.cache_hits + self.cache_misses)
                    if (self.cache_hits + self.cache_misses) > 0
                    else 0
                ),
            },
            "bottlenecks": self.bottlenecks,
            "function_stats": dict(self.function_stats),
            "optimization_suggestions": dict(self.optimization_suggestions),
            "system_metrics": {
                "current_memory": (
                    self.system_metrics_history[-1].memory_percent
                    if self.system_metrics_history
                    else 0
                ),
                "current_cpu": (
                    self.system_metrics_history[-1].cpu_percent
                    if self.system_metrics_history
                    else 0
                ),
                "peak_memory": (
                    max(m.memory_percent for m in self.system_metrics_history)
                    if self.system_metrics_history
                    else 0
                ),
                "peak_cpu": (
                    max(m.cpu_percent for m in self.system_metrics_history)
                    if self.system_metrics_history
                    else 0
                ),
            },
        }

        return report

    def save_report(self, filepath: str):
        """Save performance report to file"""
        report = self.get_performance_report()

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Performance report saved to {filepath}")

    def clear_metrics(self):
        """Clear all collected metrics"""
        self.metrics_history.clear()
        self.system_metrics_history.clear()
        self.function_stats.clear()
        self.bottlenecks.clear()
        self.optimization_suggestions.clear()
        self.function_cache.clear()
        self.cache_hits = 0
        self.cache_misses = 0
        logger.info("Performance metrics cleared")


# Global profiler instance
profiler = PerformanceProfiler()


def performance_monitor(
    enable_profiling: bool = True,
    enable_caching: bool = False,
    cache_size: int = 1000,
    profile_memory: bool = True,
):
    """Decorator for comprehensive performance monitoring"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Check cache first
            if enable_caching:
                cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
                if cache_key in profiler.function_cache:
                    profiler.cache_hits += 1
                    return profiler.function_cache[cache_key]
                profiler.cache_misses += 1

            if enable_profiling:
                result, metrics = profiler.profile_function(func, *args, **kwargs)

                # Cache result if enabled
                if enable_caching and len(profiler.function_cache) < cache_size:
                    profiler.function_cache[cache_key] = result

                return result
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def memory_profile(func: Callable) -> Callable:
    """Decorator for memory profiling"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Force garbage collection before measurement
        gc.collect()

        start_memory = psutil.Process().memory_info().rss / 1024 / 1024
        result = func(*args, **kwargs)
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024

        memory_used = end_memory - start_memory

        if memory_used > 50:  # 50MB threshold
            logger.warning(f"High memory usage in {func.__name__}: {memory_used:.2f}MB")

        return result

    return wrapper


def time_profile(func: Callable) -> Callable:
    """Decorator for execution time profiling"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        execution_time = end_time - start_time

        if execution_time > 1.0:  # 1 second threshold
            logger.warning(f"Slow execution in {func.__name__}: {execution_time:.2f}s")

        return result

    return wrapper


@contextmanager
def profile_context(context_name: str):
    """Context manager for profiling code blocks"""
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024

    try:
        yield
    finally:
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024

        execution_time = end_time - start_time
        memory_used = end_memory - start_memory

        logger.info(
            f"Profile {context_name}: {execution_time:.2f}s, {memory_used:.2f}MB"
        )


class PerformanceOptimizer:
    """Automatic performance optimization suggestions and implementations"""

    def __init__(self, profiler: PerformanceProfiler):
        self.profiler = profiler
        self.optimizations_applied = []

    def suggest_optimizations(self) -> List[str]:
        """Generate optimization suggestions based on profiling data"""
        suggestions = []

        # Analyze function performance
        for func_name, stats in self.profiler.function_stats.items():
            if stats["avg_time"] > 1.0:
                suggestions.append(
                    f"Optimize {func_name} - average execution time: {stats['avg_time']:.2f}s"
                )

            if stats["max_memory"] > 500:  # 500MB
                suggestions.append(
                    f"Reduce memory usage in {func_name} - peak usage: {stats['max_memory']:.2f}MB"
                )

            if stats["total_calls"] > 1000:
                suggestions.append(
                    f"Consider caching for {func_name} - called {stats['total_calls']} times"
                )

        # Analyze cache performance
        if self.profiler.cache_hits + self.profiler.cache_misses > 0:
            hit_rate = self.profiler.cache_hits / (
                self.profiler.cache_hits + self.profiler.cache_misses
            )
            if hit_rate < 0.5:
                suggestions.append("Consider improving cache strategy - low hit rate")

        return suggestions

    def apply_automatic_optimizations(self):
        """Apply automatic optimizations where possible"""
        # Force garbage collection
        gc.collect()
        self.optimizations_applied.append("Garbage collection")

        # Clear unused cache entries
        if len(self.profiler.function_cache) > 500:
            self.profiler.function_cache.clear()
            self.optimizations_applied.append("Cache cleanup")

        logger.info(f"Applied optimizations: {', '.join(self.optimizations_applied)}")


def create_performance_report(output_dir: str = "performance_reports"):
    """Create comprehensive performance report"""
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)

    timestamp = int(time.time())
    report_file = output_path / f"performance_report_{timestamp}.json"

    profiler.save_report(str(report_file))

    # Generate optimization suggestions
    optimizer = PerformanceOptimizer(profiler)
    suggestions = optimizer.suggest_optimizations()

    suggestions_file = output_path / f"optimization_suggestions_{timestamp}.txt"
    with open(suggestions_file, "w") as f:
        f.write("Performance Optimization Suggestions\n")
        f.write("=" * 40 + "\n\n")
        for suggestion in suggestions:
            f.write(f"• {suggestion}\n")

    logger.info(f"Performance report created: {report_file}")
    logger.info(f"Optimization suggestions: {suggestions_file}")

    return str(report_file), str(suggestions_file)


def start_performance_monitoring():
    """Start global performance monitoring"""
    profiler.start_monitoring()


def stop_performance_monitoring():
    """Stop global performance monitoring"""
    profiler.stop_monitoring()


def get_performance_summary() -> Dict[str, Any]:
    """Get performance summary"""
    return profiler.get_performance_report()
