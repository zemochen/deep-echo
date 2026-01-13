"""
Error recovery utilities for system resilience.

This module provides comprehensive error recovery strategies including
device reconnection, resource cleanup, and system health monitoring.
"""

import time
import threading
import logging
import psutil
import os
from typing import Dict, List, Callable, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .exceptions import (
    DeepEchoError, AudioError, AudioDeviceError, 
    AIProviderError, ConfigurationError
)
from .logger import get_logger
from .retry import RetryConfig, retry_with_backoff, CircuitBreaker

logger = get_logger(__name__)


class SystemHealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    FAILED = "failed"


@dataclass
class ResourceMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    network_connections: int
    thread_count: int
    timestamp: datetime


@dataclass
class ErrorEvent:
    """Represents an error event for tracking and analysis."""
    timestamp: datetime
    error_type: str
    error_message: str
    component: str
    severity: str
    recovery_attempted: bool = False
    recovery_successful: bool = False
    recovery_duration: Optional[float] = None


class SystemHealthMonitor:
    """
    Monitors system health and resource usage.
    
    Tracks CPU, memory, disk usage and provides alerts when
    thresholds are exceeded.
    """
    
    def __init__(
        self,
        cpu_threshold: float = 80.0,
        memory_threshold: float = 85.0,
        disk_threshold: float = 90.0,
        check_interval: float = 30.0
    ):
        """
        Initialize system health monitor.
        
        Args:
            cpu_threshold: CPU usage threshold percentage
            memory_threshold: Memory usage threshold percentage
            disk_threshold: Disk usage threshold percentage
            check_interval: Health check interval in seconds
        """
        self.cpu_threshold = cpu_threshold
        self.memory_threshold = memory_threshold
        self.disk_threshold = disk_threshold
        self.check_interval = check_interval
        
        self.is_monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.health_callbacks: List[Callable[[SystemHealthStatus, ResourceMetrics], None]] = []
        self.last_metrics: Optional[ResourceMetrics] = None
        self.current_status = SystemHealthStatus.HEALTHY
        
        logger.info("System health monitor initialized")
    
    def add_health_callback(self, callback: Callable[[SystemHealthStatus, ResourceMetrics], None]) -> None:
        """
        Add callback for health status changes.
        
        Args:
            callback: Function to call when health status changes
        """
        self.health_callbacks.append(callback)
    
    def start_monitoring(self) -> None:
        """Start continuous health monitoring."""
        if self.is_monitoring:
            logger.warning("Health monitoring already started")
            return
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="SystemHealthMonitor"
        )
        self.monitor_thread.start()
        logger.info("System health monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self.is_monitoring = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1.0)
        logger.info("System health monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                metrics = self._collect_metrics()
                status = self._assess_health(metrics)
                
                if status != self.current_status:
                    logger.info(f"System health status changed: {self.current_status.value} -> {status.value}")
                    self.current_status = status
                    
                    # Notify callbacks
                    for callback in self.health_callbacks:
                        try:
                            callback(status, metrics)
                        except Exception as e:
                            logger.error(f"Error in health callback: {e}")
                
                self.last_metrics = metrics
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _collect_metrics(self) -> ResourceMetrics:
        """Collect current system metrics."""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_available_mb = memory.available / (1024 * 1024)
            
            # Disk usage (current directory)
            disk = psutil.disk_usage('.')
            disk_usage_percent = (disk.used / disk.total) * 100
            
            # Network connections
            network_connections = len(psutil.net_connections())
            
            # Thread count for current process
            process = psutil.Process()
            thread_count = process.num_threads()
            
            return ResourceMetrics(
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_available_mb=memory_available_mb,
                disk_usage_percent=disk_usage_percent,
                network_connections=network_connections,
                thread_count=thread_count,
                timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            # Return default metrics on error
            return ResourceMetrics(
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                network_connections=0,
                thread_count=0,
                timestamp=datetime.now()
            )
    
    def _assess_health(self, metrics: ResourceMetrics) -> SystemHealthStatus:
        """
        Assess system health based on metrics.
        
        Args:
            metrics: Current system metrics
            
        Returns:
            System health status
        """
        critical_issues = 0
        degraded_issues = 0
        
        # Check CPU usage
        if metrics.cpu_percent > self.cpu_threshold:
            if metrics.cpu_percent > 95:
                critical_issues += 1
            else:
                degraded_issues += 1
        
        # Check memory usage
        if metrics.memory_percent > self.memory_threshold:
            if metrics.memory_percent > 95:
                critical_issues += 1
            else:
                degraded_issues += 1
        
        # Check disk usage
        if metrics.disk_usage_percent > self.disk_threshold:
            if metrics.disk_usage_percent > 98:
                critical_issues += 1
            else:
                degraded_issues += 1
        
        # Check available memory
        if metrics.memory_available_mb < 100:  # Less than 100MB available
            critical_issues += 1
        elif metrics.memory_available_mb < 500:  # Less than 500MB available
            degraded_issues += 1
        
        # Determine overall status
        if critical_issues > 0:
            return SystemHealthStatus.CRITICAL
        elif degraded_issues > 0:
            return SystemHealthStatus.DEGRADED
        else:
            return SystemHealthStatus.HEALTHY
    
    def get_current_metrics(self) -> Optional[ResourceMetrics]:
        """
        Get the most recent system metrics.
        
        Returns:
            Latest ResourceMetrics or None if not available
        """
        return self.last_metrics
    
    def get_health_status(self) -> SystemHealthStatus:
        """
        Get current system health status.
        
        Returns:
            Current SystemHealthStatus
        """
        return self.current_status


class ErrorTracker:
    """
    Tracks and analyzes error patterns for system reliability.
    
    Maintains history of errors and provides insights for
    proactive error handling.
    """
    
    def __init__(self, max_events: int = 1000):
        """
        Initialize error tracker.
        
        Args:
            max_events: Maximum number of error events to track
        """
        self.max_events = max_events
        self.error_events: List[ErrorEvent] = []
        self.error_counts: Dict[str, int] = {}
        self.component_errors: Dict[str, List[ErrorEvent]] = {}
        self._lock = threading.RLock()
        
        logger.info("Error tracker initialized")
    
    def record_error(
        self,
        error: Exception,
        component: str,
        severity: str = "error"
    ) -> ErrorEvent:
        """
        Record an error event.
        
        Args:
            error: Exception that occurred
            component: Component where error occurred
            severity: Error severity level
            
        Returns:
            Created ErrorEvent
        """
        with self._lock:
            error_type = type(error).__name__
            error_message = str(error)
            
            event = ErrorEvent(
                timestamp=datetime.now(),
                error_type=error_type,
                error_message=error_message,
                component=component,
                severity=severity
            )
            
            # Add to events list
            self.error_events.append(event)
            if len(self.error_events) > self.max_events:
                self.error_events.pop(0)
            
            # Update counts
            self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
            
            # Update component errors
            if component not in self.component_errors:
                self.component_errors[component] = []
            self.component_errors[component].append(event)
            
            logger.debug(f"Recorded error: {error_type} in {component}")
            return event
    
    def record_recovery(self, event: ErrorEvent, successful: bool, duration: float) -> None:
        """
        Record recovery attempt for an error event.
        
        Args:
            event: Original error event
            successful: Whether recovery was successful
            duration: Recovery duration in seconds
        """
        with self._lock:
            event.recovery_attempted = True
            event.recovery_successful = successful
            event.recovery_duration = duration
            
            logger.debug(f"Recorded recovery: {successful} in {duration:.2f}s for {event.error_type}")
    
    def get_error_statistics(self, time_window: Optional[timedelta] = None) -> Dict[str, Any]:
        """
        Get error statistics for analysis.
        
        Args:
            time_window: Time window to analyze (None for all time)
            
        Returns:
            Dictionary with error statistics
        """
        with self._lock:
            events = self.error_events
            
            if time_window:
                cutoff_time = datetime.now() - time_window
                events = [e for e in events if e.timestamp >= cutoff_time]
            
            if not events:
                return {"total_errors": 0}
            
            # Calculate statistics
            total_errors = len(events)
            error_types = {}
            component_stats = {}
            recovery_stats = {"attempted": 0, "successful": 0}
            
            for event in events:
                # Error type counts
                error_types[event.error_type] = error_types.get(event.error_type, 0) + 1
                
                # Component stats
                if event.component not in component_stats:
                    component_stats[event.component] = {"count": 0, "recoveries": 0}
                component_stats[event.component]["count"] += 1
                
                # Recovery stats
                if event.recovery_attempted:
                    recovery_stats["attempted"] += 1
                    if event.recovery_successful:
                        recovery_stats["successful"] += 1
                        component_stats[event.component]["recoveries"] += 1
            
            # Calculate rates
            recovery_rate = (
                recovery_stats["successful"] / recovery_stats["attempted"]
                if recovery_stats["attempted"] > 0 else 0
            )
            
            return {
                "total_errors": total_errors,
                "error_types": error_types,
                "component_stats": component_stats,
                "recovery_stats": recovery_stats,
                "recovery_rate": recovery_rate,
                "time_window": str(time_window) if time_window else "all_time"
            }
    
    def get_frequent_errors(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        Get most frequent error types.
        
        Args:
            limit: Maximum number of error types to return
            
        Returns:
            List of (error_type, count) tuples sorted by frequency
        """
        with self._lock:
            sorted_errors = sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )
            return sorted_errors[:limit]


class DeviceRecoveryManager:
    """
    Manages device reconnection and recovery strategies.
    
    Handles audio device disconnections and attempts automatic
    reconnection with appropriate fallback strategies.
    """
    
    def __init__(self):
        """Initialize device recovery manager."""
        self.recovery_strategies: Dict[str, Callable] = {}
        self.device_states: Dict[str, Dict[str, Any]] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self._lock = threading.RLock()
        
        logger.info("Device recovery manager initialized")
    
    def register_device(
        self,
        device_id: str,
        recovery_strategy: Callable,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a device with recovery strategy.
        
        Args:
            device_id: Unique device identifier
            recovery_strategy: Function to call for device recovery
            initial_state: Initial device state information
        """
        with self._lock:
            self.recovery_strategies[device_id] = recovery_strategy
            self.device_states[device_id] = initial_state or {}
            self.circuit_breakers[device_id] = CircuitBreaker(
                failure_threshold=3,
                recovery_timeout=30.0,
                expected_exception=AudioDeviceError
            )
            
            logger.info(f"Registered device for recovery: {device_id}")
    
    def attempt_device_recovery(self, device_id: str, error: Exception) -> bool:
        """
        Attempt to recover a failed device.
        
        Args:
            device_id: Device identifier
            error: Error that caused the failure
            
        Returns:
            True if recovery was successful
        """
        with self._lock:
            if device_id not in self.recovery_strategies:
                logger.error(f"No recovery strategy registered for device: {device_id}")
                return False
            
            recovery_strategy = self.recovery_strategies[device_id]
            circuit_breaker = self.circuit_breakers[device_id]
            
            try:
                logger.info(f"Attempting recovery for device: {device_id}")
                start_time = time.time()
                
                # Use circuit breaker to prevent repeated failures
                result = circuit_breaker.call(recovery_strategy, device_id, error)
                
                recovery_time = time.time() - start_time
                logger.info(f"Device recovery successful for {device_id} in {recovery_time:.2f}s")
                
                return True
                
            except Exception as recovery_error:
                logger.error(f"Device recovery failed for {device_id}: {recovery_error}")
                return False
    
    def get_device_state(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current device state.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device state dictionary or None if not found
        """
        with self._lock:
            return self.device_states.get(device_id)
    
    def update_device_state(self, device_id: str, state_updates: Dict[str, Any]) -> None:
        """
        Update device state information.
        
        Args:
            device_id: Device identifier
            state_updates: State updates to apply
        """
        with self._lock:
            if device_id in self.device_states:
                self.device_states[device_id].update(state_updates)
            else:
                self.device_states[device_id] = state_updates
    
    def get_recovery_status(self) -> Dict[str, Any]:
        """
        Get recovery status for all devices.
        
        Returns:
            Dictionary with recovery status information
        """
        with self._lock:
            status = {}
            for device_id in self.recovery_strategies:
                circuit_breaker = self.circuit_breakers[device_id]
                status[device_id] = {
                    "circuit_breaker_state": circuit_breaker.get_state(),
                    "device_state": self.device_states.get(device_id, {})
                }
            return status


class ResourceCleanupManager:
    """
    Manages resource cleanup and memory optimization.
    
    Provides utilities for cleaning up resources, managing memory usage,
    and preventing resource leaks.
    """
    
    def __init__(self):
        """Initialize resource cleanup manager."""
        self.cleanup_handlers: List[Callable[[], None]] = []
        self.resource_monitors: Dict[str, Callable[[], Dict[str, Any]]] = {}
        self.cleanup_thresholds = {
            "memory_percent": 90.0,
            "queue_size": 1000,
            "file_handles": 100
        }
        
        logger.info("Resource cleanup manager initialized")
    
    def register_cleanup_handler(self, handler: Callable[[], None]) -> None:
        """
        Register a cleanup handler function.
        
        Args:
            handler: Function to call during cleanup
        """
        self.cleanup_handlers.append(handler)
        logger.debug(f"Registered cleanup handler: {handler.__name__}")
    
    def register_resource_monitor(self, name: str, monitor: Callable[[], Dict[str, Any]]) -> None:
        """
        Register a resource monitor function.
        
        Args:
            name: Monitor name
            monitor: Function that returns resource usage information
        """
        self.resource_monitors[name] = monitor
        logger.debug(f"Registered resource monitor: {name}")
    
    def perform_cleanup(self, force: bool = False) -> Dict[str, Any]:
        """
        Perform resource cleanup.
        
        Args:
            force: Force cleanup regardless of thresholds
            
        Returns:
            Dictionary with cleanup results
        """
        logger.info("Starting resource cleanup")
        cleanup_results = {"handlers_executed": 0, "errors": []}
        
        # Check if cleanup is needed (unless forced)
        if not force and not self._should_cleanup():
            logger.debug("Cleanup not needed based on current thresholds")
            return cleanup_results
        
        # Execute cleanup handlers
        for handler in self.cleanup_handlers:
            try:
                handler()
                cleanup_results["handlers_executed"] += 1
                logger.debug(f"Executed cleanup handler: {handler.__name__}")
            except Exception as e:
                error_msg = f"Cleanup handler {handler.__name__} failed: {e}"
                logger.error(error_msg)
                cleanup_results["errors"].append(error_msg)
        
        logger.info(f"Resource cleanup completed: {cleanup_results['handlers_executed']} handlers executed")
        return cleanup_results
    
    def _should_cleanup(self) -> bool:
        """
        Check if cleanup should be performed based on thresholds.
        
        Returns:
            True if cleanup is needed
        """
        try:
            # Check memory usage
            memory = psutil.virtual_memory()
            if memory.percent > self.cleanup_thresholds["memory_percent"]:
                logger.info(f"Memory usage {memory.percent}% exceeds threshold")
                return True
            
            # Check resource monitors
            for name, monitor in self.resource_monitors.items():
                try:
                    resource_info = monitor()
                    # Check if any monitored resource exceeds thresholds
                    for key, value in resource_info.items():
                        threshold_key = f"{name}_{key}"
                        if threshold_key in self.cleanup_thresholds:
                            if value > self.cleanup_thresholds[threshold_key]:
                                logger.info(f"Resource {threshold_key} value {value} exceeds threshold")
                                return True
                except Exception as e:
                    logger.warning(f"Resource monitor {name} failed: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking cleanup thresholds: {e}")
            return False
    
    def set_cleanup_threshold(self, key: str, value: float) -> None:
        """
        Set cleanup threshold for a resource.
        
        Args:
            key: Threshold key
            value: Threshold value
        """
        self.cleanup_thresholds[key] = value
        logger.debug(f"Set cleanup threshold {key} = {value}")
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage from all monitors.
        
        Returns:
            Dictionary with resource usage information
        """
        usage = {}
        
        # System resources
        try:
            memory = psutil.virtual_memory()
            usage["system"] = {
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "cpu_percent": psutil.cpu_percent()
            }
        except Exception as e:
            logger.error(f"Failed to get system resource usage: {e}")
            usage["system"] = {"error": str(e)}
        
        # Custom resource monitors
        for name, monitor in self.resource_monitors.items():
            try:
                usage[name] = monitor()
            except Exception as e:
                logger.error(f"Resource monitor {name} failed: {e}")
                usage[name] = {"error": str(e)}
        
        return usage


# Global instances for easy access
system_health_monitor = SystemHealthMonitor()
error_tracker = ErrorTracker()
device_recovery_manager = DeviceRecoveryManager()
resource_cleanup_manager = ResourceCleanupManager()


def initialize_error_recovery() -> None:
    """Initialize error recovery system with default configuration."""
    logger.info("Initializing error recovery system")
    
    # Start system health monitoring
    system_health_monitor.start_monitoring()
    
    # Register default cleanup handlers
    resource_cleanup_manager.register_cleanup_handler(_cleanup_temp_files)
    resource_cleanup_manager.register_cleanup_handler(_cleanup_log_files)
    
    logger.info("Error recovery system initialized")


def shutdown_error_recovery() -> None:
    """Shutdown error recovery system and cleanup resources."""
    logger.info("Shutting down error recovery system")
    
    # Stop monitoring
    system_health_monitor.stop_monitoring()
    
    # Perform final cleanup
    resource_cleanup_manager.perform_cleanup(force=True)
    
    logger.info("Error recovery system shutdown complete")


def _cleanup_temp_files() -> None:
    """Cleanup temporary files."""
    import tempfile
    import glob
    
    temp_dir = tempfile.gettempdir()
    pattern = os.path.join(temp_dir, "deepecho_*.wav")
    
    try:
        temp_files = glob.glob(pattern)
        for file_path in temp_files:
            try:
                os.unlink(file_path)
                logger.debug(f"Cleaned up temp file: {file_path}")
            except OSError:
                pass  # File may already be deleted
    except Exception as e:
        logger.warning(f"Error cleaning temp files: {e}")


def _cleanup_log_files() -> None:
    """Cleanup old log files."""
    import glob
    
    try:
        log_pattern = "./transcript_log/transcript_*.txt"
        log_files = glob.glob(log_pattern)
        
        # Keep only the last 7 days of logs
        cutoff_date = datetime.now() - timedelta(days=7)
        
        for log_file in log_files:
            try:
                file_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_time < cutoff_date:
                    os.unlink(log_file)
                    logger.debug(f"Cleaned up old log file: {log_file}")
            except OSError:
                pass  # File may already be deleted
    except Exception as e:
        logger.warning(f"Error cleaning log files: {e}")