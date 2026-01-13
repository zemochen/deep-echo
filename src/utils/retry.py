"""
Retry mechanism utilities with exponential backoff.

This module provides decorators and utilities for implementing retry logic
with exponential backoff, jitter, and comprehensive error handling.
"""

import time
import random
import logging
import functools
from typing import Callable, Type, Union, Tuple, Optional, Any
from datetime import datetime, timedelta

from .exceptions import DeepEchoError
from .logger import get_logger

logger = get_logger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
        jitter_range: float = 0.1
    ):
        """
        Initialize retry configuration.
        
        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Base delay in seconds before first retry
            max_delay: Maximum delay in seconds between retries
            backoff_factor: Exponential backoff multiplier
            jitter: Whether to add random jitter to delays
            jitter_range: Range of jitter as fraction of delay (0.0-1.0)
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.jitter_range = jitter_range
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for a given attempt number.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential backoff delay
        delay = self.base_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter and self.jitter_range > 0:
            jitter_amount = delay * self.jitter_range
            jitter = random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay + jitter)
        
        return delay


class RetryState:
    """Tracks state of retry attempts."""
    
    def __init__(self, config: RetryConfig):
        """
        Initialize retry state.
        
        Args:
            config: Retry configuration
        """
        self.config = config
        self.attempt = 0
        self.start_time = datetime.now()
        self.last_exception: Optional[Exception] = None
        self.total_delay = 0.0
    
    def should_retry(self) -> bool:
        """
        Check if another retry attempt should be made.
        
        Returns:
            True if retry should be attempted
        """
        return self.attempt < self.config.max_attempts
    
    def record_attempt(self, exception: Optional[Exception] = None) -> None:
        """
        Record an attempt and its result.
        
        Args:
            exception: Exception that occurred, if any
        """
        self.attempt += 1
        self.last_exception = exception
    
    def get_next_delay(self) -> float:
        """
        Get delay before next retry attempt.
        
        Returns:
            Delay in seconds
        """
        delay = self.config.calculate_delay(self.attempt - 1)
        self.total_delay += delay
        return delay
    
    def get_summary(self) -> dict:
        """
        Get summary of retry attempts.
        
        Returns:
            Dictionary with retry statistics
        """
        elapsed = datetime.now() - self.start_time
        return {
            "attempts": self.attempt,
            "elapsed_time": elapsed.total_seconds(),
            "total_delay": self.total_delay,
            "last_exception": str(self.last_exception) if self.last_exception else None
        }


def retry_with_backoff(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[RetryState], None]] = None,
    on_failure: Optional[Callable[[RetryState], None]] = None
) -> Callable:
    """
    Decorator that adds retry logic with exponential backoff.
    
    Args:
        exceptions: Exception types to retry on
        config: Retry configuration (uses default if None)
        on_retry: Callback function called before each retry
        on_failure: Callback function called when all retries fail
        
    Returns:
        Decorated function with retry logic
        
    Example:
        @retry_with_backoff(
            exceptions=(ConnectionError, TimeoutError),
            config=RetryConfig(max_attempts=5, base_delay=2.0)
        )
        def api_call():
            # Function that might fail
            pass
    """
    if config is None:
        config = RetryConfig()
    
    if not isinstance(exceptions, tuple):
        exceptions = (exceptions,)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            state = RetryState(config)
            
            while True:
                try:
                    result = func(*args, **kwargs)
                    
                    # Log successful execution after retries
                    if state.attempt > 0:
                        summary = state.get_summary()
                        logger.info(
                            f"Function {func.__name__} succeeded after {state.attempt} attempts "
                            f"(elapsed: {summary['elapsed_time']:.2f}s)"
                        )
                    
                    return result
                    
                except exceptions as e:
                    state.record_attempt(e)
                    
                    if not state.should_retry():
                        # All retries exhausted
                        summary = state.get_summary()
                        logger.error(
                            f"Function {func.__name__} failed after {state.attempt} attempts "
                            f"(elapsed: {summary['elapsed_time']:.2f}s): {e}"
                        )
                        
                        if on_failure:
                            try:
                                on_failure(state)
                            except Exception as callback_error:
                                logger.error(f"Error in failure callback: {callback_error}")
                        
                        raise e
                    
                    # Calculate delay and wait
                    delay = state.get_next_delay()
                    
                    logger.warning(
                        f"Function {func.__name__} failed (attempt {state.attempt}/{config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    if on_retry:
                        try:
                            on_retry(state)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")
                    
                    time.sleep(delay)
                
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"Function {func.__name__} failed with non-retryable exception: {e}")
                    raise e
        
        return wrapper
    return decorator


def retry_async_with_backoff(
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[RetryState], None]] = None,
    on_failure: Optional[Callable[[RetryState], None]] = None
) -> Callable:
    """
    Async version of retry decorator with exponential backoff.
    
    Args:
        exceptions: Exception types to retry on
        config: Retry configuration (uses default if None)
        on_retry: Callback function called before each retry
        on_failure: Callback function called when all retries fail
        
    Returns:
        Decorated async function with retry logic
    """
    import asyncio
    
    if config is None:
        config = RetryConfig()
    
    if not isinstance(exceptions, tuple):
        exceptions = (exceptions,)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            state = RetryState(config)
            
            while True:
                try:
                    result = await func(*args, **kwargs)
                    
                    # Log successful execution after retries
                    if state.attempt > 0:
                        summary = state.get_summary()
                        logger.info(
                            f"Async function {func.__name__} succeeded after {state.attempt} attempts "
                            f"(elapsed: {summary['elapsed_time']:.2f}s)"
                        )
                    
                    return result
                    
                except exceptions as e:
                    state.record_attempt(e)
                    
                    if not state.should_retry():
                        # All retries exhausted
                        summary = state.get_summary()
                        logger.error(
                            f"Async function {func.__name__} failed after {state.attempt} attempts "
                            f"(elapsed: {summary['elapsed_time']:.2f}s): {e}"
                        )
                        
                        if on_failure:
                            try:
                                on_failure(state)
                            except Exception as callback_error:
                                logger.error(f"Error in failure callback: {callback_error}")
                        
                        raise e
                    
                    # Calculate delay and wait
                    delay = state.get_next_delay()
                    
                    logger.warning(
                        f"Async function {func.__name__} failed (attempt {state.attempt}/{config.max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )
                    
                    if on_retry:
                        try:
                            on_retry(state)
                        except Exception as callback_error:
                            logger.error(f"Error in retry callback: {callback_error}")
                    
                    await asyncio.sleep(delay)
                
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"Async function {func.__name__} failed with non-retryable exception: {e}")
                    raise e
        
        return wrapper
    return decorator


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for graceful degradation.
    
    Prevents cascading failures by temporarily disabling failing operations
    and allowing them to recover.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds before attempting recovery
            expected_exception: Exception type that triggers circuit breaker
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half-open
        
        logger.info(f"Circuit breaker initialized with threshold={failure_threshold}, timeout={recovery_timeout}s")
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                logger.info("Circuit breaker transitioning to half-open state")
            else:
                raise DeepEchoError(
                    f"Circuit breaker is open. Last failure: {self.last_failure_time}. "
                    f"Will retry after {self.recovery_timeout}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt to reset."""
        if self.last_failure_time is None:
            return True
        
        elapsed = datetime.now() - self.last_failure_time
        return elapsed.total_seconds() >= self.recovery_timeout
    
    def _on_success(self) -> None:
        """Handle successful function execution."""
        if self.state == "half-open":
            self.state = "closed"
            self.failure_count = 0
            logger.info("Circuit breaker reset to closed state")
    
    def _on_failure(self) -> None:
        """Handle failed function execution."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Will attempt recovery in {self.recovery_timeout}s"
            )
    
    def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        self.state = "closed"
        self.failure_count = 0
        self.last_failure_time = None
        logger.info("Circuit breaker manually reset")
    
    def get_state(self) -> dict:
        """
        Get current circuit breaker state.
        
        Returns:
            Dictionary with current state information
        """
        return {
            "state": self.state,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


def circuit_breaker(
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    expected_exception: Type[Exception] = Exception
) -> Callable:
    """
    Decorator that adds circuit breaker pattern to a function.
    
    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time in seconds before attempting recovery
        expected_exception: Exception type that triggers circuit breaker
        
    Returns:
        Decorated function with circuit breaker logic
    """
    breaker = CircuitBreaker(failure_threshold, recovery_timeout, expected_exception)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return breaker.call(func, *args, **kwargs)
        
        # Attach circuit breaker instance for external access
        wrapper.circuit_breaker = breaker
        return wrapper
    
    return decorator


class GracefulDegradation:
    """
    Implements graceful degradation patterns for system resilience.
    
    Provides fallback mechanisms when primary operations fail.
    """
    
    def __init__(self, name: str):
        """
        Initialize graceful degradation handler.
        
        Args:
            name: Name for logging and identification
        """
        self.name = name
        self.fallback_functions = []
        self.logger = get_logger(f"{__name__}.{name}")
    
    def add_fallback(self, func: Callable, description: str = "") -> None:
        """
        Add a fallback function.
        
        Args:
            func: Fallback function to execute
            description: Description of the fallback
        """
        self.fallback_functions.append((func, description))
        self.logger.info(f"Added fallback: {description or func.__name__}")
    
    def execute_with_fallbacks(self, primary_func: Callable, *args, **kwargs) -> Any:
        """
        Execute primary function with fallback chain.
        
        Args:
            primary_func: Primary function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Result from primary function or fallback
            
        Raises:
            Exception: If all functions (primary + fallbacks) fail
        """
        # Try primary function first
        try:
            self.logger.debug(f"Executing primary function: {primary_func.__name__}")
            return primary_func(*args, **kwargs)
        except Exception as e:
            self.logger.warning(f"Primary function {primary_func.__name__} failed: {e}")
        
        # Try fallback functions in order
        for i, (fallback_func, description) in enumerate(self.fallback_functions):
            try:
                self.logger.info(f"Attempting fallback {i+1}: {description or fallback_func.__name__}")
                return fallback_func(*args, **kwargs)
            except Exception as e:
                self.logger.warning(f"Fallback {i+1} failed: {e}")
        
        # All functions failed
        self.logger.error(f"All functions failed for {self.name}")
        raise DeepEchoError(f"All functions failed for {self.name}")


def with_graceful_degradation(
    fallbacks: list,
    name: str = "operation"
) -> Callable:
    """
    Decorator that adds graceful degradation to a function.
    
    Args:
        fallbacks: List of (function, description) tuples for fallbacks
        name: Name for logging and identification
        
    Returns:
        Decorated function with graceful degradation
    """
    degradation = GracefulDegradation(name)
    
    for fallback in fallbacks:
        if isinstance(fallback, tuple):
            func, description = fallback
            degradation.add_fallback(func, description)
        else:
            degradation.add_fallback(fallback)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            return degradation.execute_with_fallbacks(func, *args, **kwargs)
        
        # Attach degradation instance for external access
        wrapper.graceful_degradation = degradation
        return wrapper
    
    return decorator