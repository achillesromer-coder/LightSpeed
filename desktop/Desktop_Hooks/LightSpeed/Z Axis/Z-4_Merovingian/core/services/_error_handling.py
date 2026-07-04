"""
Error Handling - Unified exception hierarchy and error handling decorators

Provides consistent error handling across all LightSpeed components.
Following Clean Code principles for error handling.

Features:
- Custom exception hierarchy
- Error handling decorators
- Centralized logging
- Graceful degradation
"""

import functools
import traceback
from typing import Callable, Any, Optional, Type, Tuple
from datetime import datetime
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


# ============================================================================
# Exception Hierarchy
# ============================================================================

class LightSpeedError(Exception):
    """Base exception for all LightSpeed errors"""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now()


class DatabaseError(LightSpeedError):
    """Database operation errors"""
    pass


class WorkflowError(LightSpeedError):
    """Workflow execution errors"""
    pass


class AIError(LightSpeedError):
    """AI/LLM integration errors"""
    pass


class FileOperationError(LightSpeedError):
    """File operation errors"""
    pass


class ValidationError(LightSpeedError):
    """Data validation errors"""
    pass


class ConfigurationError(LightSpeedError):
    """Configuration errors"""
    pass


class NetworkError(LightSpeedError):
    """Network/API errors"""
    pass


class AuthenticationError(LightSpeedError):
    """Authentication/authorization errors"""
    pass


class RenderingError(LightSpeedError):
    """3D rendering and visualization errors"""
    pass


class IntegrationError(LightSpeedError):
    """Component integration errors"""
    pass


# ============================================================================
# Error Handling Decorators
# ============================================================================

def handle_errors(
    default_return: Any = None,
    log_errors: bool = True,
    raise_errors: bool = False,
    error_callback: Optional[Callable] = None
) -> Callable:
    """
    Decorator for consistent error handling

    Args:
        default_return: Value to return on error
        log_errors: Whether to log errors
        raise_errors: Whether to re-raise errors after handling
        error_callback: Optional callback function for errors

    Usage:
        @handle_errors(default_return=[], log_errors=True)
        def risky_function():
            # Code that might fail
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except Exception as e:
                # Log error
                if log_errors:
                    logger = logging.getLogger(func.__module__)
                    logger.error(
                        f"Error in {func.__name__}: {str(e)}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )

                # Call error callback if provided
                if error_callback:
                    try:
                        error_callback(e, func, args, kwargs)
                    except Exception as callback_error:
                        logging.error(f"Error in error callback: {callback_error}")

                # Re-raise if requested
                if raise_errors:
                    raise

                # Return default value
                return default_return

        return wrapper
    return decorator


def retry_on_error(
    max_retries: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Callable:
    """
    Decorator to retry function on specific exceptions

    Args:
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries (seconds)
        exponential_backoff: Use exponential backoff for delays
        exceptions: Tuple of exceptions to catch and retry

    Usage:
        @retry_on_error(max_retries=3, delay=1.0)
        def flaky_network_call():
            # Code that might fail temporarily
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            current_delay = delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger = logging.getLogger(func.__module__)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed for {func.__name__}: {e}"
                        )
                        time.sleep(current_delay)

                        if exponential_backoff:
                            current_delay *= 2
                    else:
                        # Max retries exceeded
                        logger = logging.getLogger(func.__module__)
                        logger.error(
                            f"All {max_retries} retries failed for {func.__name__}: {e}"
                        )

            # Raise the last exception
            raise last_exception

        return wrapper
    return decorator


def validate_input(
    validators: dict,
    raise_on_invalid: bool = True
) -> Callable:
    """
    Decorator to validate function inputs

    Args:
        validators: Dict mapping parameter names to validation functions
        raise_on_invalid: Raise ValidationError if validation fails

    Usage:
        @validate_input({
            'age': lambda x: x >= 0,
            'name': lambda x: len(x) > 0
        })
        def create_user(name: str, age: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Validate each parameter
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    try:
                        if not validator(value):
                            error_msg = f"Validation failed for parameter '{param_name}': {value}"
                            if raise_on_invalid:
                                raise ValidationError(error_msg)
                            else:
                                logging.warning(error_msg)
                    except Exception as e:
                        error_msg = f"Error validating parameter '{param_name}': {e}"
                        if raise_on_invalid:
                            raise ValidationError(error_msg)
                        else:
                            logging.warning(error_msg)

            return func(*args, **kwargs)

        return wrapper
    return decorator


def log_calls(
    log_args: bool = True,
    log_result: bool = False,
    log_duration: bool = True
) -> Callable:
    """
    Decorator to log function calls

    Args:
        log_args: Log function arguments
        log_result: Log function return value
        log_duration: Log execution duration

    Usage:
        @log_calls(log_args=True, log_duration=True)
        def important_function(x, y):
            return x + y
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import time

            logger = logging.getLogger(func.__module__)
            func_name = func.__name__

            # Log call
            if log_args:
                logger.info(f"Calling {func_name} with args={args}, kwargs={kwargs}")
            else:
                logger.info(f"Calling {func_name}")

            # Execute function
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)

                # Log result
                if log_result:
                    logger.info(f"{func_name} returned: {result}")

                # Log duration
                if log_duration:
                    duration = time.perf_counter() - start_time
                    logger.info(f"{func_name} completed in {duration:.3f}s")

                return result

            except Exception as e:
                duration = time.perf_counter() - start_time
                logger.error(f"{func_name} failed after {duration:.3f}s: {e}")
                raise

        return wrapper
    return decorator


def deprecated(reason: str, alternative: Optional[str] = None) -> Callable:
    """
    Decorator to mark functions as deprecated

    Args:
        reason: Reason for deprecation
        alternative: Suggested alternative function

    Usage:
        @deprecated("Use new_function instead", alternative="new_function")
        def old_function():
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import warnings

            warning_msg = f"{func.__name__} is deprecated: {reason}"
            if alternative:
                warning_msg += f". Use {alternative} instead."

            warnings.warn(warning_msg, DeprecationWarning, stacklevel=2)
            logging.warning(warning_msg)

            return func(*args, **kwargs)

        return wrapper
    return decorator


# ============================================================================
# Context Managers for Resource Cleanup
# ============================================================================

class ErrorContext:
    """
    Context manager for error handling with cleanup

    Usage:
        with ErrorContext("Processing data", cleanup_func=close_connection):
            # Code that might fail
            process_data()
    """

    def __init__(
        self,
        operation: str,
        cleanup_func: Optional[Callable] = None,
        log_errors: bool = True,
        raise_errors: bool = True
    ):
        self.operation = operation
        self.cleanup_func = cleanup_func
        self.log_errors = log_errors
        self.raise_errors = raise_errors
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        self.logger.info(f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Run cleanup
        if self.cleanup_func:
            try:
                self.cleanup_func()
            except Exception as e:
                self.logger.error(f"Error in cleanup: {e}")

        # Handle exception
        if exc_type is not None:
            if self.log_errors:
                self.logger.error(
                    f"Error in {self.operation}: {exc_val}\n"
                    f"Traceback: {''.join(traceback.format_tb(exc_tb))}"
                )

            # Return False to re-raise, True to suppress
            return not self.raise_errors

        self.logger.info(f"Completed: {self.operation}")
        return True


# ============================================================================
# Error Reporter
# ============================================================================

class ErrorReporter:
    """Centralized error reporting"""

    def __init__(self, log_file: str = "logs/errors.log"):
        self.log_file = log_file
        self.errors = []

        # Configure file logging
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.file_handler.setFormatter(formatter)

    def report(self, error: Exception, context: Optional[dict] = None):
        """Report an error with optional context"""
        error_record = {
            'timestamp': datetime.now(),
            'error_type': type(error).__name__,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }

        self.errors.append(error_record)

        # Log to file
        logger = logging.getLogger(__name__)
        logger.addHandler(self.file_handler)
        logger.error(
            f"{error_record['error_type']}: {error_record['message']}\n"
            f"Context: {error_record['context']}\n"
            f"{error_record['traceback']}"
        )

    def get_recent_errors(self, count: int = 10):
        """Get most recent errors"""
        return self.errors[-count:]

    def clear_errors(self):
        """Clear error history"""
        self.errors.clear()


# Global error reporter instance
error_reporter = ErrorReporter()


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    # Test error handling
    @handle_errors(default_return=None, log_errors=True)
    def might_fail(should_fail: bool = False):
        if should_fail:
            raise ValueError("Something went wrong!")
        return "Success"

    # Test retry
    @retry_on_error(max_retries=3, delay=0.1)
    def flaky_function(attempt_counter: list):
        attempt_counter[0] += 1
        if attempt_counter[0] < 3:
            raise NetworkError("Network unavailable")
        return "Success after retries"

    # Test validation
    @validate_input({
        'age': lambda x: x >= 0,
        'name': lambda x: len(x) > 0
    })
    def create_user(name: str, age: int):
        return f"User {name}, age {age}"

    # Test logging
    @log_calls(log_args=True, log_duration=True)
    def important_calculation(x: int, y: int) -> int:
        return x + y

    # Run tests
    print("Testing error handling...")
    result1 = might_fail(False)
    print(f"Success case: {result1}")

    result2 = might_fail(True)
    print(f"Failure case (should be None): {result2}")

    print("\nTesting retry...")
    counter = [0]
    result3 = flaky_function(counter)
    print(f"After {counter[0]} attempts: {result3}")

    print("\nTesting validation...")
    try:
        create_user("Alice", 25)
        print("Valid input accepted")
    except ValidationError:
        print("Valid input rejected (shouldn't happen)")

    try:
        create_user("", 25)
        print("Invalid input accepted (shouldn't happen)")
    except ValidationError:
        print("Invalid input rejected ✓")

    print("\nTesting logging...")
    result4 = important_calculation(10, 20)
    print(f"Result: {result4}")

    print("\n✅ Error handling tests complete!")
