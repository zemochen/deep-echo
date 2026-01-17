"""
Advanced threading utilities for DeepEcho Real-time Voice AI Assistant.

This module provides optimized thread management, synchronization utilities,
and thread-safe resource sharing for improved performance and stability.
"""

import threading
import queue
import time
import weakref
import gc
from typing import Dict, List, Optional, Callable, Any, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, Future
import psutil
import os

from .logger import get_logger
from .exceptions import DeepEchoError

logger = get_logger(__name__)


class ThreadState(Enum):
    """Thread state enumeration."""
    CREATED = "created"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class ThreadPriority(Enum):
    """Thread priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ThreadMetrics:
    """Thread performance metrics."""
    thread_id: str
    name: str
    state: ThreadState
    cpu_time: float
    memory_usage_mb: float
    queue_size: int
    processed_items: int
    error_count: int
    last_activity: datetime
    uptime: timedelta


class ThreadSafeCounter:
    """Thread-safe counter with atomic operations."""
    
    def __init__(self, initial_value: int = 0):
        """
        Initialize thread-safe counter.
        
        Args:
            initial_value: Initial counter value
        """
        self._value = initial_value
        self._lock = threading.RLock()
    
    def increment(self, amount: int = 1) -> int:
        """
        Atomically increment counter.
        
        Args:
            amount: Amount to increment
            
        Returns:
            New counter value
        """
        with self._lock:
            self._value += amount
            return self._value
    
    def decrement(self, amount: int = 1) -> int:
        """
        Atomically decrement counter.
        
        Args:
            amount: Amount to decrement
            
        Returns:
            New counter value
        """
        with self._lock:
            self._value -= amount
            return self._value
    
    def get(self) -> int:
        """
        Get current counter value.
        
        Returns:
            Current value
        """
        with self._lock:
            return self._value
    
    def set(self, value: int) -> int:
        """
        Set counter value.
        
        Args:
            value: New value
            
        Returns:
            New counter value
        """
        with self._lock:
            self._value = value
            return self._value
    
    def compare_and_swap(self, expected: int, new_value: int) -> bool:
        """
        Atomically compare and swap counter value.
        
        Args:
            expected: Expected current value
            new_value: New value to set if current equals expected
            
        Returns:
            True if swap was successful
        """
        with self._lock:
            if self._value == expected:
                self._value = new_value
                return True
            return False


class ThreadSafeDict:
    """Thread-safe dictionary with atomic operations."""
    
    def __init__(self):
        """Initialize thread-safe dictionary."""
        self._data: Dict[Any, Any] = {}
        self._lock = threading.RLock()
    
    def get(self, key: Any, default: Any = None) -> Any:
        """
        Get value by key.
        
        Args:
            key: Dictionary key
            default: Default value if key not found
            
        Returns:
            Value or default
        """
        with self._lock:
            return self._data.get(key, default)
    
    def set(self, key: Any, value: Any) -> None:
        """
        Set key-value pair.
        
        Args:
            key: Dictionary key
            value: Value to set
        """
        with self._lock:
            self._data[key] = value
    
    def update(self, updates: Dict[Any, Any]) -> None:
        """
        Update multiple key-value pairs atomically.
        
        Args:
            updates: Dictionary of updates to apply
        """
        with self._lock:
            self._data.update(updates)
    
    def pop(self, key: Any, default: Any = None) -> Any:
        """
        Remove and return value by key.
        
        Args:
            key: Dictionary key
            default: Default value if key not found
            
        Returns:
            Removed value or default
        """
        with self._lock:
            return self._data.pop(key, default)
    
    def keys(self) -> List[Any]:
        """
        Get all keys.
        
        Returns:
            List of keys
        """
        with self._lock:
            return list(self._data.keys())
    
    def values(self) -> List[Any]:
        """
        Get all values.
        
        Returns:
            List of values
        """
        with self._lock:
            return list(self._data.values())
    
    def items(self) -> List[Tuple[Any, Any]]:
        """
        Get all key-value pairs.
        
        Returns:
            List of (key, value) tuples
        """
        with self._lock:
            return list(self._data.items())
    
    def clear(self) -> None:
        """Clear all data."""
        with self._lock:
            self._data.clear()
    
    def size(self) -> int:
        """
        Get dictionary size.
        
        Returns:
            Number of items
        """
        with self._lock:
            return len(self._data)


class ManagedThread:
    """
    Enhanced thread wrapper with lifecycle management and monitoring.
    
    Provides better control over thread execution, resource cleanup,
    and performance monitoring.
    """
    
    def __init__(
        self,
        target: Callable,
        name: str,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        daemon: bool = True,
        priority: ThreadPriority = ThreadPriority.NORMAL,
        max_queue_size: int = 1000,
        heartbeat_interval: float = 30.0
    ):
        """
        Initialize managed thread.
        
        Args:
            target: Target function to execute
            name: Thread name
            args: Target function arguments
            kwargs: Target function keyword arguments
            daemon: Whether thread should be daemon
            priority: Thread priority level
            max_queue_size: Maximum queue size for monitoring
            heartbeat_interval: Heartbeat interval in seconds
        """
        self.target = target
        self.name = name
        self.args = args
        self.kwargs = kwargs or {}
        self.daemon = daemon
        self.priority = priority
        self.max_queue_size = max_queue_size
        self.heartbeat_interval = heartbeat_interval
        
        # Thread management
        self._thread: Optional[threading.Thread] = None
        self._state = ThreadState.CREATED
        self._stop_event = threading.Event()
        self._heartbeat_event = threading.Event()
        
        # Metrics
        self._start_time: Optional[datetime] = None
        self._processed_items = ThreadSafeCounter()
        self._error_count = ThreadSafeCounter()
        self._last_activity = datetime.now()
        
        # Resource monitoring
        self._process = psutil.Process()
        self._initial_cpu_time = 0.0
        
        logger.debug(f"Created managed thread: {name}")
    
    def start(self) -> bool:
        """
        Start the managed thread.
        
        Returns:
            True if thread started successfully
        """
        if self._state != ThreadState.CREATED:
            logger.warning(f"Thread {self.name} cannot be started from state {self._state}")
            return False
        
        try:
            self._state = ThreadState.STARTING
            self._start_time = datetime.now()
            self._initial_cpu_time = self._process.cpu_times().user + self._process.cpu_times().system
            
            # Create and start thread
            self._thread = threading.Thread(
                target=self._run_wrapper,
                name=self.name,
                daemon=self.daemon
            )
            self._thread.start()
            
            # Wait for thread to actually start
            start_timeout = 5.0
            start_time = time.time()
            while self._state == ThreadState.STARTING and (time.time() - start_time) < start_timeout:
                time.sleep(0.1)
            
            if self._state == ThreadState.RUNNING:
                logger.info(f"Thread {self.name} started successfully")
                return True
            else:
                logger.error(f"Thread {self.name} failed to start within timeout")
                return False
                
        except Exception as e:
            self._state = ThreadState.ERROR
            logger.error(f"Failed to start thread {self.name}: {e}")
            return False
    
    def stop(self, timeout: float = 5.0) -> bool:
        """
        Stop the managed thread gracefully.
        
        Args:
            timeout: Maximum time to wait for thread to stop
            
        Returns:
            True if thread stopped successfully
        """
        if self._state not in [ThreadState.RUNNING, ThreadState.STARTING]:
            logger.debug(f"Thread {self.name} already stopped or stopping")
            return True
        
        try:
            self._state = ThreadState.STOPPING
            self._stop_event.set()
            
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=timeout)
                
                if self._thread.is_alive():
                    logger.warning(f"Thread {self.name} did not stop within timeout")
                    return False
            
            self._state = ThreadState.STOPPED
            logger.info(f"Thread {self.name} stopped successfully")
            return True
            
        except Exception as e:
            self._state = ThreadState.ERROR
            logger.error(f"Error stopping thread {self.name}: {e}")
            return False
    
    def _run_wrapper(self) -> None:
        """Wrapper for target function with monitoring and error handling."""
        try:
            self._state = ThreadState.RUNNING
            logger.debug(f"Thread {self.name} entering run loop")
            
            # Start heartbeat monitoring
            heartbeat_thread = threading.Thread(
                target=self._heartbeat_loop,
                daemon=True,
                name=f"{self.name}_heartbeat"
            )
            heartbeat_thread.start()
            
            # Execute target function
            self.target(*self.args, **self.kwargs)
            
        except Exception as e:
            self._error_count.increment()
            self._state = ThreadState.ERROR
            logger.error(f"Thread {self.name} encountered error: {e}")
        finally:
            if self._state != ThreadState.STOPPING:
                self._state = ThreadState.STOPPED
            logger.debug(f"Thread {self.name} exiting")
    
    def _heartbeat_loop(self) -> None:
        """Heartbeat monitoring loop."""
        while not self._stop_event.is_set() and self._state == ThreadState.RUNNING:
            self._heartbeat_event.set()
            self._last_activity = datetime.now()
            self._stop_event.wait(self.heartbeat_interval)
    
    def is_alive(self) -> bool:
        """
        Check if thread is alive.
        
        Returns:
            True if thread is running
        """
        return self._thread is not None and self._thread.is_alive()
    
    def get_state(self) -> ThreadState:
        """
        Get current thread state.
        
        Returns:
            Current ThreadState
        """
        return self._state
    
    def get_metrics(self) -> ThreadMetrics:
        """
        Get thread performance metrics.
        
        Returns:
            ThreadMetrics object with current metrics
        """
        try:
            # Calculate CPU time
            current_cpu_time = self._process.cpu_times().user + self._process.cpu_times().system
            cpu_time = current_cpu_time - self._initial_cpu_time
            
            # Calculate memory usage
            memory_info = self._process.memory_info()
            memory_usage_mb = memory_info.rss / (1024 * 1024)
            
            # Calculate uptime
            uptime = datetime.now() - self._start_time if self._start_time else timedelta(0)
            
            return ThreadMetrics(
                thread_id=str(self._thread.ident) if self._thread else "unknown",
                name=self.name,
                state=self._state,
                cpu_time=cpu_time,
                memory_usage_mb=memory_usage_mb,
                queue_size=0,  # Will be updated by queue monitoring
                processed_items=self._processed_items.get(),
                error_count=self._error_count.get(),
                last_activity=self._last_activity,
                uptime=uptime
            )
        except Exception as e:
            logger.error(f"Error collecting metrics for thread {self.name}: {e}")
            return ThreadMetrics(
                thread_id="unknown",
                name=self.name,
                state=self._state,
                cpu_time=0.0,
                memory_usage_mb=0.0,
                queue_size=0,
                processed_items=0,
                error_count=0,
                last_activity=self._last_activity,
                uptime=timedelta(0)
            )
    
    def increment_processed_items(self, count: int = 1) -> None:
        """
        Increment processed items counter.
        
        Args:
            count: Number of items processed
        """
        self._processed_items.increment(count)
        self._last_activity = datetime.now()
    
    def increment_error_count(self, count: int = 1) -> None:
        """
        Increment error counter.
        
        Args:
            count: Number of errors
        """
        self._error_count.increment(count)
    
    def should_stop(self) -> bool:
        """
        Check if thread should stop.
        
        Returns:
            True if stop was requested
        """
        return self._stop_event.is_set()


class ThreadManager:
    """
    Central thread management system for DeepEcho.
    
    Provides lifecycle management, monitoring, and resource optimization
    for all application threads.
    """
    
    def __init__(self, max_threads: int = 20):
        """
        Initialize thread manager.
        
        Args:
            max_threads: Maximum number of managed threads
        """
        self.max_threads = max_threads
        self._threads: Dict[str, ManagedThread] = {}
        self._thread_pool = ThreadPoolExecutor(max_workers=max_threads, thread_name_prefix="DeepEcho")
        self._lock = threading.RLock()
        
        # Monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_stop_event = threading.Event()
        self._monitor_interval = 30.0
        
        # Resource management
        self._resource_limits = {
            "max_memory_mb": 1000,
            "max_cpu_percent": 80,
            "max_queue_size": 1000
        }
        
        logger.info(f"Thread manager initialized with max_threads={max_threads}")
    
    def create_thread(
        self,
        name: str,
        target: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        daemon: bool = True,
        priority: ThreadPriority = ThreadPriority.NORMAL,
        auto_start: bool = True
    ) -> Optional[ManagedThread]:
        """
        Create a new managed thread.
        
        Args:
            name: Thread name (must be unique)
            target: Target function to execute
            args: Target function arguments
            kwargs: Target function keyword arguments
            daemon: Whether thread should be daemon
            priority: Thread priority level
            auto_start: Whether to start thread immediately
            
        Returns:
            ManagedThread instance or None if creation failed
        """
        with self._lock:
            if name in self._threads:
                logger.error(f"Thread with name '{name}' already exists")
                return None
            
            if len(self._threads) >= self.max_threads:
                logger.error(f"Maximum thread limit ({self.max_threads}) reached")
                return None
            
            try:
                thread = ManagedThread(
                    target=target,
                    name=name,
                    args=args,
                    kwargs=kwargs,
                    daemon=daemon,
                    priority=priority
                )
                
                self._threads[name] = thread
                
                if auto_start:
                    if not thread.start():
                        del self._threads[name]
                        return None
                
                logger.info(f"Created thread: {name}")
                return thread
                
            except Exception as e:
                logger.error(f"Failed to create thread {name}: {e}")
                return None
    
    def start_thread(self, name: str) -> bool:
        """
        Start a managed thread by name.
        
        Args:
            name: Thread name
            
        Returns:
            True if thread started successfully
        """
        with self._lock:
            thread = self._threads.get(name)
            if not thread:
                logger.error(f"Thread '{name}' not found")
                return False
            
            return thread.start()
    
    def stop_thread(self, name: str, timeout: float = 5.0) -> bool:
        """
        Stop a managed thread by name.
        
        Args:
            name: Thread name
            timeout: Maximum time to wait for thread to stop
            
        Returns:
            True if thread stopped successfully
        """
        with self._lock:
            thread = self._threads.get(name)
            if not thread:
                logger.error(f"Thread '{name}' not found")
                return False
            
            return thread.stop(timeout)
    
    def remove_thread(self, name: str) -> bool:
        """
        Remove a managed thread.
        
        Args:
            name: Thread name
            
        Returns:
            True if thread was removed
        """
        with self._lock:
            thread = self._threads.get(name)
            if not thread:
                logger.error(f"Thread '{name}' not found")
                return False
            
            # Stop thread if running
            if thread.is_alive():
                thread.stop()
            
            del self._threads[name]
            logger.info(f"Removed thread: {name}")
            return True
    
    def get_thread(self, name: str) -> Optional[ManagedThread]:
        """
        Get managed thread by name.
        
        Args:
            name: Thread name
            
        Returns:
            ManagedThread instance or None if not found
        """
        with self._lock:
            return self._threads.get(name)
    
    def list_threads(self) -> List[str]:
        """
        Get list of all managed thread names.
        
        Returns:
            List of thread names
        """
        with self._lock:
            return list(self._threads.keys())
    
    def get_thread_metrics(self, name: Optional[str] = None) -> Union[ThreadMetrics, Dict[str, ThreadMetrics]]:
        """
        Get thread metrics.
        
        Args:
            name: Thread name (None for all threads)
            
        Returns:
            ThreadMetrics for specific thread or dict of all metrics
        """
        with self._lock:
            if name:
                thread = self._threads.get(name)
                if thread:
                    return thread.get_metrics()
                else:
                    raise ValueError(f"Thread '{name}' not found")
            else:
                return {name: thread.get_metrics() for name, thread in self._threads.items()}
    
    def start_monitoring(self) -> None:
        """Start thread monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Thread monitoring already started")
            return
        
        self._monitor_stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ThreadManager_Monitor"
        )
        self._monitor_thread.start()
        logger.info("Thread monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop thread monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_stop_event.set()
            self._monitor_thread.join(timeout=2.0)
        logger.info("Thread monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Thread monitoring loop."""
        while not self._monitor_stop_event.is_set():
            try:
                self._check_thread_health()
                self._optimize_resources()
                self._cleanup_dead_threads()
            except Exception as e:
                logger.error(f"Error in thread monitoring: {e}")
            
            self._monitor_stop_event.wait(self._monitor_interval)
    
    def _check_thread_health(self) -> None:
        """Check health of all managed threads."""
        with self._lock:
            for name, thread in self._threads.items():
                try:
                    metrics = thread.get_metrics()
                    
                    # Check for resource limits
                    if metrics.memory_usage_mb > self._resource_limits["max_memory_mb"]:
                        logger.warning(f"Thread {name} exceeds memory limit: {metrics.memory_usage_mb}MB")
                    
                    # Check for stalled threads
                    time_since_activity = datetime.now() - metrics.last_activity
                    if time_since_activity > timedelta(minutes=5):
                        logger.warning(f"Thread {name} appears stalled: {time_since_activity}")
                    
                    # Check error rates
                    if metrics.error_count > 10:
                        logger.warning(f"Thread {name} has high error count: {metrics.error_count}")
                        
                except Exception as e:
                    logger.error(f"Error checking health of thread {name}: {e}")
    
    def _optimize_resources(self) -> None:
        """Optimize resource usage across threads."""
        try:
            # Get system resource usage
            memory = psutil.virtual_memory()
            cpu_percent = psutil.cpu_percent()
            
            # If system resources are high, consider thread optimization
            if memory.percent > 85 or cpu_percent > 80:
                logger.info("High system resource usage detected, optimizing threads")
                self._reduce_thread_activity()
            
        except Exception as e:
            logger.error(f"Error optimizing resources: {e}")
    
    def _reduce_thread_activity(self) -> None:
        """Reduce thread activity to conserve resources."""
        with self._lock:
            # Prioritize threads by priority level
            priority_threads = []
            for name, thread in self._threads.items():
                priority_threads.append((thread.priority.value, name, thread))
            
            # Sort by priority (highest first)
            priority_threads.sort(key=lambda x: x[0], reverse=True)
            
            # Keep high priority threads running, consider pausing low priority ones
            for priority, name, thread in priority_threads:
                if priority <= ThreadPriority.LOW.value:
                    logger.debug(f"Considering resource optimization for low priority thread: {name}")
                    # Could implement thread pausing/throttling here
    
    def _cleanup_dead_threads(self) -> None:
        """Clean up threads that have died unexpectedly."""
        with self._lock:
            dead_threads = []
            for name, thread in self._threads.items():
                if thread.get_state() in [ThreadState.STOPPED, ThreadState.ERROR] and not thread.is_alive():
                    dead_threads.append(name)
            
            for name in dead_threads:
                logger.info(f"Cleaning up dead thread: {name}")
                del self._threads[name]
    
    def stop_all_threads(self, timeout: float = 10.0) -> bool:
        """
        Stop all managed threads.
        
        Args:
            timeout: Maximum time to wait for all threads to stop
            
        Returns:
            True if all threads stopped successfully
        """
        logger.info("Stopping all managed threads")
        
        with self._lock:
            threads_to_stop = list(self._threads.values())
        
        # Stop monitoring first
        self.stop_monitoring()
        
        # Stop all threads
        success = True
        for thread in threads_to_stop:
            if not thread.stop(timeout / len(threads_to_stop)):
                success = False
                logger.warning(f"Thread {thread.name} did not stop gracefully")
        
        # Shutdown thread pool
        self._thread_pool.shutdown(wait=True)
        
        logger.info(f"All threads stop completed: {'success' if success else 'with warnings'}")
        return success
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with system status information
        """
        with self._lock:
            thread_states = {}
            total_memory = 0
            total_errors = 0
            
            for name, thread in self._threads.items():
                metrics = thread.get_metrics()
                thread_states[name] = {
                    "state": metrics.state.value,
                    "memory_mb": metrics.memory_usage_mb,
                    "errors": metrics.error_count,
                    "uptime": str(metrics.uptime)
                }
                total_memory += metrics.memory_usage_mb
                total_errors += metrics.error_count
            
            return {
                "total_threads": len(self._threads),
                "max_threads": self.max_threads,
                "total_memory_mb": total_memory,
                "total_errors": total_errors,
                "thread_states": thread_states,
                "monitoring_active": self._monitor_thread is not None and self._monitor_thread.is_alive()
            }
    
    def get_thread_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all managed threads.
        
        Returns:
            Dictionary mapping thread names to their status information
        """
        with self._lock:
            status = {}
            for name, thread in self._threads.items():
                metrics = thread.get_metrics()
                status[name] = {
                    "alive": thread.is_alive(),
                    "state": metrics.state.value,
                    "memory_mb": metrics.memory_usage_mb,
                    "errors": metrics.error_count,
                    "uptime": str(metrics.uptime),
                    "processed_items": metrics.processed_items
                }
            return status


# Global thread manager instance
thread_manager = ThreadManager()


def get_thread_manager() -> ThreadManager:
    """
    Get the global thread manager instance.
    
    Returns:
        ThreadManager instance
    """
    return thread_manager


def create_daemon_thread(
    name: str,
    target: Callable,
    args: tuple = (),
    kwargs: Optional[Dict] = None,
    priority: ThreadPriority = ThreadPriority.NORMAL
) -> Optional[ManagedThread]:
    """
    Create a daemon thread with proper management.
    
    Args:
        name: Thread name
        target: Target function
        args: Function arguments
        kwargs: Function keyword arguments
        priority: Thread priority
        
    Returns:
        ManagedThread instance or None if creation failed
    """
    return thread_manager.create_thread(
        name=name,
        target=target,
        args=args,
        kwargs=kwargs,
        daemon=True,
        priority=priority,
        auto_start=True
    )


def shutdown_threading_system() -> None:
    """Shutdown the threading system gracefully."""
    logger.info("Shutting down threading system")
    thread_manager.stop_all_threads()
    logger.info("Threading system shutdown complete")