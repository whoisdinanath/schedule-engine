"""
Enhanced Error Handling System for Genetics Timetabling
Provides comprehensive exception handling, retry mechanisms, and error recovery.
"""

import logging
import traceback
import functools
import time
from typing import Any, Callable, Dict, List, Optional, Type, Union
from dataclasses import dataclass
from enum import Enum
import inspect
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""

    DATA_LOADING = "data_loading"
    VALIDATION = "validation"
    GENETIC_ALGORITHM = "genetic_algorithm"
    CONSTRAINT_CHECKING = "constraint_checking"
    VISUALIZATION = "visualization"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    EXTERNAL = "external"


@dataclass
class ErrorInfo:
    """Detailed error information"""

    error_type: str
    error_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: float
    traceback: str
    context: Dict[str, Any]
    function_name: str
    line_number: int
    file_path: str
    recovery_suggestions: List[str]


class GeneticsException(Exception):
    """Base exception for genetics timetabling system"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.SYSTEM,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        recovery_suggestions: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.category = category
        self.severity = severity
        self.recovery_suggestions = recovery_suggestions or []
        self.timestamp = time.time()
        self.context = {}


class DataLoadingError(GeneticsException):
    """Exception for data loading issues"""

    def __init__(self, message: str, file_path: str = None, **kwargs):
        super().__init__(message, category=ErrorCategory.DATA_LOADING, **kwargs)
        self.file_path = file_path


class ValidationError(GeneticsException):
    """Exception for validation issues"""

    def __init__(self, message: str, validation_errors: List[str] = None, **kwargs):
        super().__init__(message, category=ErrorCategory.VALIDATION, **kwargs)
        self.validation_errors = validation_errors or []


class GeneticAlgorithmError(GeneticsException):
    """Exception for genetic algorithm issues"""

    def __init__(
        self,
        message: str,
        generation: int = None,
        population_size: int = None,
        **kwargs,
    ):
        super().__init__(message, category=ErrorCategory.GENETIC_ALGORITHM, **kwargs)
        self.generation = generation
        self.population_size = population_size


class ConstraintViolationError(GeneticsException):
    """Exception for constraint violation issues"""

    def __init__(
        self,
        message: str,
        constraint_type: str = None,
        violation_count: int = None,
        **kwargs,
    ):
        super().__init__(message, category=ErrorCategory.CONSTRAINT_CHECKING, **kwargs)
        self.constraint_type = constraint_type
        self.violation_count = violation_count


class PerformanceError(GeneticsException):
    """Exception for performance issues"""

    def __init__(
        self,
        message: str,
        memory_usage: float = None,
        execution_time: float = None,
        **kwargs,
    ):
        super().__init__(message, category=ErrorCategory.PERFORMANCE, **kwargs)
        self.memory_usage = memory_usage
        self.execution_time = execution_time


class ErrorHandler:
    """Advanced error handling with recovery mechanisms"""

    def __init__(self):
        self.error_history: List[ErrorInfo] = []
        self.recovery_strategies: Dict[ErrorCategory, List[Callable]] = {}
        self.error_counts: Dict[str, int] = {}
        self.circuit_breaker_status: Dict[str, bool] = {}
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 300  # 5 minutes
        self.last_error_time: Dict[str, float] = {}

    def register_recovery_strategy(self, category: ErrorCategory, strategy: Callable):
        """Register a recovery strategy for a specific error category"""
        if category not in self.recovery_strategies:
            self.recovery_strategies[category] = []
        self.recovery_strategies[category].append(strategy)

    def handle_error(
        self, error: Exception, context: Dict[str, Any] = None
    ) -> ErrorInfo:
        """Handle an error with comprehensive logging and recovery"""
        error_info = self._create_error_info(error, context or {})
        self.error_history.append(error_info)

        # Update error counts
        error_key = f"{error_info.category.value}_{error_info.error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_error_time[error_key] = time.time()

        # Check circuit breaker
        if self.error_counts[error_key] >= self.circuit_breaker_threshold:
            self.circuit_breaker_status[error_key] = True
            logger.critical(f"Circuit breaker activated for {error_key}")

        # Log error
        self._log_error(error_info)

        # Attempt recovery
        self._attempt_recovery(error_info)

        return error_info

    def _create_error_info(
        self, error: Exception, context: Dict[str, Any]
    ) -> ErrorInfo:
        """Create detailed error information"""
        frame = inspect.currentframe()
        try:
            # Get the caller's frame
            caller_frame = frame.f_back.f_back

            if isinstance(error, GeneticsException):
                category = error.category
                severity = error.severity
                recovery_suggestions = error.recovery_suggestions
            else:
                category = self._categorize_error(error)
                severity = self._determine_severity(error)
                recovery_suggestions = self._get_default_recovery_suggestions(error)

            return ErrorInfo(
                error_type=type(error).__name__,
                error_message=str(error),
                category=category,
                severity=severity,
                timestamp=time.time(),
                traceback=traceback.format_exc(),
                context=context,
                function_name=(
                    caller_frame.f_code.co_name if caller_frame else "unknown"
                ),
                line_number=caller_frame.f_lineno if caller_frame else 0,
                file_path=(
                    caller_frame.f_code.co_filename if caller_frame else "unknown"
                ),
                recovery_suggestions=recovery_suggestions,
            )
        finally:
            del frame

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """Categorize error based on type and context"""
        error_type = type(error).__name__

        if "data" in error_type.lower() or "file" in error_type.lower():
            return ErrorCategory.DATA_LOADING
        elif "validation" in error_type.lower():
            return ErrorCategory.VALIDATION
        elif "memory" in error_type.lower() or "performance" in error_type.lower():
            return ErrorCategory.PERFORMANCE
        elif "constraint" in error_type.lower():
            return ErrorCategory.CONSTRAINT_CHECKING
        elif "genetic" in error_type.lower() or "algorithm" in error_type.lower():
            return ErrorCategory.GENETIC_ALGORITHM
        else:
            return ErrorCategory.SYSTEM

    def _determine_severity(self, error: Exception) -> ErrorSeverity:
        """Determine error severity based on type and context"""
        if isinstance(error, (MemoryError, SystemError)):
            return ErrorSeverity.CRITICAL
        elif isinstance(error, (ValueError, TypeError)):
            return ErrorSeverity.HIGH
        elif isinstance(error, (FileNotFoundError, IOError)):
            return ErrorSeverity.MEDIUM
        else:
            return ErrorSeverity.LOW

    def _get_default_recovery_suggestions(self, error: Exception) -> List[str]:
        """Get default recovery suggestions based on error type"""
        error_type = type(error).__name__

        suggestions = {
            "FileNotFoundError": [
                "Check if the file path is correct",
                "Verify file permissions",
                "Ensure the file exists",
            ],
            "MemoryError": [
                "Reduce population size",
                "Increase available memory",
                "Enable memory optimization",
            ],
            "ValueError": [
                "Check input data format",
                "Verify parameter ranges",
                "Validate data consistency",
            ],
            "TimeoutError": [
                "Increase timeout duration",
                "Check network connectivity",
                "Reduce operation complexity",
            ],
        }

        return suggestions.get(error_type, ["Contact support for assistance"])

    def _log_error(self, error_info: ErrorInfo):
        """Log error with appropriate level"""
        log_message = (
            f"Error in {error_info.function_name} at line {error_info.line_number}: "
            f"{error_info.error_message}"
        )

        if error_info.severity == ErrorSeverity.CRITICAL:
            logger.critical(log_message)
        elif error_info.severity == ErrorSeverity.HIGH:
            logger.error(log_message)
        elif error_info.severity == ErrorSeverity.MEDIUM:
            logger.warning(log_message)
        else:
            logger.info(log_message)

        # Log recovery suggestions
        if error_info.recovery_suggestions:
            logger.info(
                f"Recovery suggestions: {', '.join(error_info.recovery_suggestions)}"
            )

    def _attempt_recovery(self, error_info: ErrorInfo):
        """Attempt recovery strategies for the error"""
        if error_info.category in self.recovery_strategies:
            for strategy in self.recovery_strategies[error_info.category]:
                try:
                    strategy(error_info)
                    logger.info(
                        f"Recovery strategy applied successfully for {error_info.category}"
                    )
                except Exception as recovery_error:
                    logger.error(f"Recovery strategy failed: {recovery_error}")

    def is_circuit_breaker_active(self, error_type: str) -> bool:
        """Check if circuit breaker is active for error type"""
        return self.circuit_breaker_status.get(error_type, False)

    def reset_circuit_breaker(self, error_type: str):
        """Reset circuit breaker for error type"""
        if error_type in self.circuit_breaker_status:
            del self.circuit_breaker_status[error_type]
        if error_type in self.error_counts:
            self.error_counts[error_type] = 0
        logger.info(f"Circuit breaker reset for {error_type}")

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of error statistics"""
        return {
            "total_errors": len(self.error_history),
            "error_counts": self.error_counts.copy(),
            "circuit_breakers": list(self.circuit_breaker_status.keys()),
            "recent_errors": [
                {
                    "type": error.error_type,
                    "category": error.category.value,
                    "severity": error.severity.value,
                    "timestamp": error.timestamp,
                }
                for error in self.error_history[-10:]  # Last 10 errors
            ],
        }


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(
    category: ErrorCategory = ErrorCategory.SYSTEM,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    recovery_suggestions: Optional[List[str]] = None,
    raise_on_error: bool = True,
):
    """Decorator for handling errors in functions"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    "function": func.__name__,
                    "args": str(args)[:100],  # Truncate for logging
                    "kwargs": str(kwargs)[:100],
                }

                if not isinstance(e, GeneticsException):
                    e = GeneticsException(
                        str(e),
                        category=category,
                        severity=severity,
                        recovery_suggestions=recovery_suggestions,
                    )

                error_handler.handle_error(e, context)

                if raise_on_error:
                    raise e
                return None

        return wrapper

    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
):
    """Decorator for retrying functions on specific errors"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt < max_retries:
                        sleep_time = delay * (backoff_factor**attempt)
                        logger.warning(
                            f"Attempt {attempt + 1} failed for {func.__name__}: {e}. "
                            f"Retrying in {sleep_time:.2f} seconds..."
                        )
                        time.sleep(sleep_time)
                    else:
                        logger.error(
                            f"All {max_retries + 1} attempts failed for {func.__name__}"
                        )
                        raise e

            raise last_exception

        return wrapper

    return decorator


def timeout_handler(timeout_seconds: float):
    """Decorator for handling function timeouts"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e

            thread = threading.Thread(target=target)
            thread.daemon = True
            thread.start()
            thread.join(timeout_seconds)

            if thread.is_alive():
                logger.error(
                    f"Function {func.__name__} timed out after {timeout_seconds} seconds"
                )
                raise TimeoutError(f"Function {func.__name__} timed out")

            if exception[0]:
                raise exception[0]

            return result[0]

        return wrapper

    return decorator


def safe_execute(func: Callable, *args, default_return=None, **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(
            e,
            {
                "function": func.__name__,
                "args": str(args)[:100],
                "kwargs": str(kwargs)[:100],
            },
        )
        return default_return


def batch_execute(
    functions: List[Callable],
    max_workers: int = 4,
    timeout: float = 300,
    ignore_errors: bool = False,
):
    """Execute multiple functions in parallel with error handling"""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_func = {executor.submit(func): func for func in functions}

        for future in as_completed(future_to_func, timeout=timeout):
            func = future_to_func[future]
            try:
                result = future.result()
                results.append(("success", func.__name__, result))
            except Exception as e:
                if not ignore_errors:
                    error_handler.handle_error(e, {"function": func.__name__})
                results.append(("error", func.__name__, str(e)))

    return results


class ErrorRecoveryStrategies:
    """Collection of error recovery strategies"""

    @staticmethod
    def data_loading_recovery(error_info: ErrorInfo):
        """Recovery strategy for data loading errors"""
        if "file" in error_info.error_message.lower():
            logger.info("Attempting to create missing directories...")
            # Implementation would create directories, check permissions, etc.

    @staticmethod
    def memory_recovery(error_info: ErrorInfo):
        """Recovery strategy for memory errors"""
        logger.info("Attempting memory cleanup...")
        import gc

        gc.collect()

    @staticmethod
    def genetic_algorithm_recovery(error_info: ErrorInfo):
        """Recovery strategy for genetic algorithm errors"""
        logger.info("Attempting GA parameter adjustment...")
        # Implementation would adjust population size, mutation rate, etc.


# Register default recovery strategies
error_handler.register_recovery_strategy(
    ErrorCategory.DATA_LOADING, ErrorRecoveryStrategies.data_loading_recovery
)
error_handler.register_recovery_strategy(
    ErrorCategory.PERFORMANCE, ErrorRecoveryStrategies.memory_recovery
)
error_handler.register_recovery_strategy(
    ErrorCategory.GENETIC_ALGORITHM, ErrorRecoveryStrategies.genetic_algorithm_recovery
)
