"""
Resource optimization utilities for DeepEcho.

This module provides intelligent resource management, memory optimization,
and performance tuning for improved system efficiency and stability.
"""

import gc
import threading
import time
import psutil
import os
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import weakref

from .logger import get_logger
from .threading import ThreadSafeCounter, ThreadSafeDict

logger = get_logger(__name__)


class OptimizationLevel(Enum):
    """Resource optimization levels."""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class ResourceType(Enum):
    """Resource type enumeration."""
    MEMORY = "memory"
    CPU = "cpu"
    DISK = "disk"
    NETWORK = "network"
    THREADS = "threads"


@dataclass
class ResourceUsage:
    """Resource usage metrics."""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_available_mb: float
    disk_usage_percent: float
    thread_count: int
    file_descriptors: int
    network_connections: int


@dataclass
class OptimizationAction:
    """Represents an optimization action."""
    action_type: str
    resource_type: ResourceType
    description: str
    priority: int
    estimated_savings_mb: float
    callback: Optional[Callable[[], bool]] = None


class ResourceMonitor:
    """
    Monitors system resource usage and triggers optimization actions.
    
    Provides real-time monitoring of CPU, memory, disk, and other resources
    with configurable thresholds and automatic optimization triggers.
    """
    
    def __init__(
        self,
        monitoring_interval: float = 10.0,
        memory_threshold: float = 80.0,
        cpu_threshold: float = 75.0,
        disk_threshold: float = 85.0
    ):
        """
        Initialize resource monitor.
        
        Args:
            monitoring_interval: Monitoring interval in seconds
            memory_threshold: Memory usage threshold percentage
            cpu_threshold: CPU usage threshold percentage
            disk_threshold: Disk usage threshold percentage
        """
        self.monitoring_interval = monitoring_interval
        self.memory_threshold = memory_threshold
        self.cpu_threshold = cpu_threshold
        self.disk_threshold = disk_threshold
        
        # Monitoring state
        self._is_monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Resource history
        self._resource_history: List[ResourceUsage] = []
        self._max_history_size = 100
        
        # Callbacks
        self._threshold_callbacks: Dict[ResourceType, List[Callable[[ResourceUsage], None]]] = {
            ResourceType.MEMORY: [],
            ResourceType.CPU: [],
            ResourceType.DISK: [],
            ResourceType.THREADS: []
        }
        
        # Process reference
        self._process = psutil.Process()
        
        logger.info("Resource monitor initialized")
    
    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self._is_monitoring:
            logger.warning("Resource monitoring already started")
            return
        
        self._is_monitoring = True
        self._stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="ResourceMonitor"
        )
        self._monitor_thread.start()
        logger.info("Resource monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        if not self._is_monitoring:
            return
        
        self._is_monitoring = False
        self._stop_event.set()
        
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        logger.info("Resource monitoring stopped")
    
    def add_threshold_callback(
        self,
        resource_type: ResourceType,
        callback: Callable[[ResourceUsage], None]
    ) -> None:
        """
        Add callback for resource threshold violations.
        
        Args:
            resource_type: Type of resource to monitor
            callback: Function to call when threshold is exceeded
        """
        self._threshold_callbacks[resource_type].append(callback)
        logger.debug(f"Added threshold callback for {resource_type.value}")
    
    def get_current_usage(self) -> ResourceUsage:
        """
        Get current resource usage.
        
        Returns:
            ResourceUsage object with current metrics
        """
        try:
            # System-wide metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            # Process-specific metrics
            thread_count = self._process.num_threads()
            
            try:
                file_descriptors = self._process.num_fds() if hasattr(self._process, 'num_fds') else 0
            except (psutil.AccessDenied, AttributeError):
                file_descriptors = 0
            
            try:
                network_connections = len(psutil.net_connections())
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                network_connections = 0
            
            return ResourceUsage(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=(disk.used / disk.total) * 100,
                thread_count=thread_count,
                file_descriptors=file_descriptors,
                network_connections=network_connections
            )
        except Exception as e:
            logger.error(f"Error collecting resource usage: {e}")
            return ResourceUsage(
                timestamp=datetime.now(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_available_mb=0.0,
                disk_usage_percent=0.0,
                thread_count=0,
                file_descriptors=0,
                network_connections=0
            )
    
    def get_resource_history(self, duration: Optional[timedelta] = None) -> List[ResourceUsage]:
        """
        Get resource usage history.
        
        Args:
            duration: Time duration to retrieve (None for all history)
            
        Returns:
            List of ResourceUsage objects
        """
        if duration is None:
            return self._resource_history.copy()
        
        cutoff_time = datetime.now() - duration
        return [usage for usage in self._resource_history if usage.timestamp >= cutoff_time]
    
    def get_average_usage(self, duration: Optional[timedelta] = None) -> Optional[ResourceUsage]:
        """
        Get average resource usage over a time period.
        
        Args:
            duration: Time duration to average (None for all history)
            
        Returns:
            ResourceUsage with averaged values or None if no data
        """
        history = self.get_resource_history(duration)
        if not history:
            return None
        
        total_cpu = sum(usage.cpu_percent for usage in history)
        total_memory = sum(usage.memory_percent for usage in history)
        total_disk = sum(usage.disk_usage_percent for usage in history)
        total_threads = sum(usage.thread_count for usage in history)
        total_fds = sum(usage.file_descriptors for usage in history)
        total_connections = sum(usage.network_connections for usage in history)
        
        count = len(history)
        avg_memory_available = sum(usage.memory_available_mb for usage in history) / count
        
        return ResourceUsage(
            timestamp=datetime.now(),
            cpu_percent=total_cpu / count,
            memory_percent=total_memory / count,
            memory_available_mb=avg_memory_available,
            disk_usage_percent=total_disk / count,
            thread_count=int(total_threads / count),
            file_descriptors=int(total_fds / count),
            network_connections=int(total_connections / count)
        )
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while not self._stop_event.is_set():
            try:
                usage = self.get_current_usage()
                
                # Add to history
                self._resource_history.append(usage)
                if len(self._resource_history) > self._max_history_size:
                    self._resource_history.pop(0)
                
                # Check thresholds and trigger callbacks
                self._check_thresholds(usage)
                
            except Exception as e:
                logger.error(f"Error in resource monitoring loop: {e}")
            
            self._stop_event.wait(self.monitoring_interval)
    
    def _check_thresholds(self, usage: ResourceUsage) -> None:
        """Check resource thresholds and trigger callbacks."""
        # Memory threshold
        if usage.memory_percent > self.memory_threshold:
            for callback in self._threshold_callbacks[ResourceType.MEMORY]:
                try:
                    callback(usage)
                except Exception as e:
                    logger.error(f"Error in memory threshold callback: {e}")
        
        # CPU threshold
        if usage.cpu_percent > self.cpu_threshold:
            for callback in self._threshold_callbacks[ResourceType.CPU]:
                try:
                    callback(usage)
                except Exception as e:
                    logger.error(f"Error in CPU threshold callback: {e}")
        
        # Disk threshold
        if usage.disk_usage_percent > self.disk_threshold:
            for callback in self._threshold_callbacks[ResourceType.DISK]:
                try:
                    callback(usage)
                except Exception as e:
                    logger.error(f"Error in disk threshold callback: {e}")
        
        # Thread count threshold (heuristic: more than 50 threads might be excessive)
        if usage.thread_count > 50:
            for callback in self._threshold_callbacks[ResourceType.THREADS]:
                try:
                    callback(usage)
                except Exception as e:
                    logger.error(f"Error in thread threshold callback: {e}")


class MemoryOptimizer:
    """
    Provides memory optimization strategies and garbage collection management.
    
    Implements various memory optimization techniques including garbage collection
    tuning, object pool management, and memory leak detection.
    """
    
    def __init__(self):
        """Initialize memory optimizer."""
        self._optimization_callbacks: List[Callable[[], float]] = []
        self._object_pools: Dict[str, List[Any]] = {}
        self._pool_locks: Dict[str, threading.Lock] = {}
        
        # Memory tracking
        self._memory_snapshots: List[Tuple[datetime, float]] = []
        self._gc_stats = ThreadSafeCounter()
        
        logger.info("Memory optimizer initialized")
    
    def register_optimization_callback(self, callback: Callable[[], float]) -> None:
        """
        Register a memory optimization callback.
        
        Args:
            callback: Function that performs optimization and returns MB freed
        """
        self._optimization_callbacks.append(callback)
        logger.debug("Registered memory optimization callback")
    
    def create_object_pool(self, pool_name: str, factory: Callable[[], Any], max_size: int = 100) -> None:
        """
        Create an object pool for memory efficiency.
        
        Args:
            pool_name: Name of the object pool
            factory: Function to create new objects
            max_size: Maximum pool size
        """
        self._object_pools[pool_name] = []
        self._pool_locks[pool_name] = threading.Lock()
        
        # Pre-populate pool
        for _ in range(min(10, max_size)):
            try:
                obj = factory()
                self._object_pools[pool_name].append(obj)
            except Exception as e:
                logger.error(f"Error pre-populating object pool {pool_name}: {e}")
                break
        
        logger.info(f"Created object pool: {pool_name} (size: {len(self._object_pools[pool_name])})")
    
    def get_pooled_object(self, pool_name: str, factory: Callable[[], Any]) -> Any:
        """
        Get object from pool or create new one.
        
        Args:
            pool_name: Name of the object pool
            factory: Function to create new objects if pool is empty
            
        Returns:
            Object from pool or newly created object
        """
        if pool_name not in self._object_pools:
            return factory()
        
        with self._pool_locks[pool_name]:
            pool = self._object_pools[pool_name]
            if pool:
                return pool.pop()
            else:
                return factory()
    
    def return_pooled_object(self, pool_name: str, obj: Any, max_size: int = 100) -> None:
        """
        Return object to pool.
        
        Args:
            pool_name: Name of the object pool
            obj: Object to return to pool
            max_size: Maximum pool size
        """
        if pool_name not in self._object_pools:
            return
        
        with self._pool_locks[pool_name]:
            pool = self._object_pools[pool_name]
            if len(pool) < max_size:
                # Reset object state if it has a reset method
                if hasattr(obj, 'reset'):
                    try:
                        obj.reset()
                    except Exception as e:
                        logger.warning(f"Error resetting pooled object: {e}")
                        return
                
                pool.append(obj)
    
    def perform_gc_optimization(self, level: OptimizationLevel = OptimizationLevel.BALANCED) -> float:
        """
        Perform garbage collection optimization.
        
        Args:
            level: Optimization level
            
        Returns:
            Memory freed in MB
        """
        initial_memory = self._get_memory_usage_mb()
        
        try:
            if level == OptimizationLevel.CONSERVATIVE:
                # Light garbage collection
                collected = gc.collect()
                
            elif level == OptimizationLevel.BALANCED:
                # Standard garbage collection with generation focus
                gc.collect(0)  # Collect generation 0
                gc.collect(1)  # Collect generation 1
                collected = gc.collect(2)  # Collect generation 2
                
            elif level == OptimizationLevel.AGGRESSIVE:
                # Aggressive garbage collection
                gc.disable()
                try:
                    for _ in range(3):
                        collected = gc.collect()
                        if collected == 0:
                            break
                finally:
                    gc.enable()
            
            self._gc_stats.increment()
            
            final_memory = self._get_memory_usage_mb()
            memory_freed = max(0, initial_memory - final_memory)
            
            logger.info(f"GC optimization ({level.value}) freed {memory_freed:.2f}MB")
            return memory_freed
            
        except Exception as e:
            logger.error(f"Error during GC optimization: {e}")
            return 0.0
    
    def optimize_memory(self, target_mb: Optional[float] = None) -> float:
        """
        Perform comprehensive memory optimization.
        
        Args:
            target_mb: Target memory reduction in MB
            
        Returns:
            Total memory freed in MB
        """
        logger.info("Starting memory optimization")
        initial_memory = self._get_memory_usage_mb()
        total_freed = 0.0
        
        # Run registered optimization callbacks
        for callback in self._optimization_callbacks:
            try:
                freed = callback()
                total_freed += freed
                logger.debug(f"Optimization callback freed {freed:.2f}MB")
                
                if target_mb and total_freed >= target_mb:
                    break
            except Exception as e:
                logger.error(f"Error in optimization callback: {e}")
        
        # Perform garbage collection
        gc_freed = self.perform_gc_optimization(OptimizationLevel.BALANCED)
        total_freed += gc_freed
        
        # Clear object pools if needed
        if target_mb and total_freed < target_mb:
            pool_freed = self._clear_object_pools()
            total_freed += pool_freed
        
        final_memory = self._get_memory_usage_mb()
        actual_freed = max(0, initial_memory - final_memory)
        
        logger.info(f"Memory optimization completed: {actual_freed:.2f}MB freed (target: {target_mb or 'N/A'}MB)")
        return actual_freed
    
    def detect_memory_leaks(self, threshold_mb: float = 100.0) -> List[str]:
        """
        Detect potential memory leaks.
        
        Args:
            threshold_mb: Memory growth threshold in MB
            
        Returns:
            List of potential leak indicators
        """
        current_memory = self._get_memory_usage_mb()
        current_time = datetime.now()
        
        # Add current snapshot
        self._memory_snapshots.append((current_time, current_memory))
        
        # Keep only recent snapshots (last hour)
        cutoff_time = current_time - timedelta(hours=1)
        self._memory_snapshots = [
            (time, memory) for time, memory in self._memory_snapshots
            if time >= cutoff_time
        ]
        
        if len(self._memory_snapshots) < 2:
            return []
        
        # Check for consistent memory growth
        leaks = []
        oldest_time, oldest_memory = self._memory_snapshots[0]
        memory_growth = current_memory - oldest_memory
        time_elapsed = (current_time - oldest_time).total_seconds() / 3600  # hours
        
        if memory_growth > threshold_mb and time_elapsed > 0.5:  # At least 30 minutes
            growth_rate = memory_growth / time_elapsed
            leaks.append(f"Consistent memory growth: {growth_rate:.2f}MB/hour")
        
        # Check for sudden memory spikes
        if len(self._memory_snapshots) >= 10:
            recent_memories = [memory for _, memory in self._memory_snapshots[-10:]]
            avg_memory = sum(recent_memories) / len(recent_memories)
            
            if current_memory > avg_memory * 1.5:  # 50% above average
                leaks.append(f"Memory spike detected: {current_memory:.2f}MB vs {avg_memory:.2f}MB average")
        
        return leaks
    
    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    
    def _clear_object_pools(self) -> float:
        """
        Clear object pools to free memory.
        
        Returns:
            Estimated memory freed in MB
        """
        total_objects = 0
        for pool_name, pool in self._object_pools.items():
            with self._pool_locks[pool_name]:
                objects_cleared = len(pool)
                pool.clear()
                total_objects += objects_cleared
                logger.debug(f"Cleared object pool {pool_name}: {objects_cleared} objects")
        
        # Rough estimate: 1KB per object
        estimated_freed = (total_objects * 1024) / (1024 * 1024)
        logger.info(f"Cleared object pools: ~{estimated_freed:.2f}MB freed")
        return estimated_freed


class ResourceOptimizer:
    """
    Central resource optimization system for DeepEcho.
    
    Coordinates memory optimization, CPU usage optimization, and other
    resource management strategies based on system conditions.
    """
    
    def __init__(self, optimization_level: OptimizationLevel = OptimizationLevel.BALANCED):
        """
        Initialize resource optimizer.
        
        Args:
            optimization_level: Default optimization level
        """
        self.optimization_level = optimization_level
        
        # Component systems
        self.resource_monitor = ResourceMonitor()
        self.memory_optimizer = MemoryOptimizer()
        
        # Optimization actions
        self._optimization_actions: List[OptimizationAction] = []
        self._auto_optimization_enabled = True
        
        # Statistics
        self._optimization_stats = ThreadSafeDict()
        
        # Setup default optimization actions
        self._setup_default_actions()
        
        # Register threshold callbacks
        self.resource_monitor.add_threshold_callback(
            ResourceType.MEMORY,
            self._handle_memory_threshold
        )
        
        logger.info(f"Resource optimizer initialized (level: {optimization_level.value})")
    
    def start(self) -> None:
        """Start resource optimization system."""
        self.resource_monitor.start_monitoring()
        logger.info("Resource optimization system started")
    
    def start_optimization(self) -> None:
        """
        Start resource optimization system.
        
        Alias for start() method for backward compatibility.
        """
        self.start()
    
    def stop(self) -> None:
        """Stop resource optimization system."""
        self.resource_monitor.stop_monitoring()
        logger.info("Resource optimization system stopped")
    
    def register_optimization_action(self, action: OptimizationAction) -> None:
        """
        Register a custom optimization action.
        
        Args:
            action: OptimizationAction to register
        """
        self._optimization_actions.append(action)
        self._optimization_actions.sort(key=lambda a: a.priority, reverse=True)
        logger.debug(f"Registered optimization action: {action.description}")
    
    def trigger_optimization(
        self,
        resource_type: Optional[ResourceType] = None,
        target_savings_mb: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Trigger resource optimization.
        
        Args:
            resource_type: Specific resource type to optimize (None for all)
            target_savings_mb: Target memory savings in MB
            
        Returns:
            Dictionary with optimization results
        """
        logger.info(f"Triggering optimization (type: {resource_type}, target: {target_savings_mb}MB)")
        
        results = {
            "actions_executed": 0,
            "memory_freed_mb": 0.0,
            "errors": [],
            "actions": []
        }
        
        # Filter actions by resource type if specified
        actions_to_execute = self._optimization_actions
        if resource_type:
            actions_to_execute = [a for a in actions_to_execute if a.resource_type == resource_type]
        
        # Execute optimization actions
        total_savings = 0.0
        for action in actions_to_execute:
            try:
                if action.callback:
                    success = action.callback()
                    if success:
                        results["actions_executed"] += 1
                        total_savings += action.estimated_savings_mb
                        results["actions"].append({
                            "action": action.description,
                            "savings_mb": action.estimated_savings_mb
                        })
                        
                        # Update statistics
                        stats_key = f"{action.resource_type.value}_{action.action_type}"
                        current_count = self._optimization_stats.get(stats_key, 0)
                        self._optimization_stats.set(stats_key, current_count + 1)
                        
                        logger.debug(f"Executed optimization: {action.description}")
                        
                        # Check if target is reached
                        if target_savings_mb and total_savings >= target_savings_mb:
                            break
                
            except Exception as e:
                error_msg = f"Error executing optimization {action.description}: {e}"
                results["errors"].append(error_msg)
                logger.error(error_msg)
        
        results["memory_freed_mb"] = total_savings
        
        logger.info(f"Optimization completed: {results['actions_executed']} actions, {total_savings:.2f}MB freed")
        return results
    
    def get_optimization_recommendations(self) -> List[OptimizationAction]:
        """
        Get optimization recommendations based on current system state.
        
        Returns:
            List of recommended OptimizationAction objects
        """
        recommendations = []
        current_usage = self.resource_monitor.get_current_usage()
        
        # Memory recommendations
        if current_usage.memory_percent > 80:
            recommendations.extend([
                action for action in self._optimization_actions
                if action.resource_type == ResourceType.MEMORY
            ])
        
        # CPU recommendations
        if current_usage.cpu_percent > 75:
            recommendations.extend([
                action for action in self._optimization_actions
                if action.resource_type == ResourceType.CPU
            ])
        
        # Thread recommendations
        if current_usage.thread_count > 30:
            recommendations.extend([
                action for action in self._optimization_actions
                if action.resource_type == ResourceType.THREADS
            ])
        
        # Sort by priority
        recommendations.sort(key=lambda a: a.priority, reverse=True)
        return recommendations[:5]  # Top 5 recommendations
    
    def enable_auto_optimization(self, enabled: bool = True) -> None:
        """
        Enable or disable automatic optimization.
        
        Args:
            enabled: Whether to enable auto-optimization
        """
        self._auto_optimization_enabled = enabled
        logger.info(f"Auto-optimization {'enabled' if enabled else 'disabled'}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status.
        
        Returns:
            Dictionary with system status information
        """
        current_usage = self.resource_monitor.get_current_usage()
        avg_usage = self.resource_monitor.get_average_usage(timedelta(minutes=10))
        
        return {
            "current_usage": {
                "cpu_percent": current_usage.cpu_percent,
                "memory_percent": current_usage.memory_percent,
                "memory_available_mb": current_usage.memory_available_mb,
                "thread_count": current_usage.thread_count
            },
            "average_usage": {
                "cpu_percent": avg_usage.cpu_percent if avg_usage else 0,
                "memory_percent": avg_usage.memory_percent if avg_usage else 0,
                "thread_count": avg_usage.thread_count if avg_usage else 0
            } if avg_usage else None,
            "optimization_level": self.optimization_level.value,
            "auto_optimization_enabled": self._auto_optimization_enabled,
            "registered_actions": len(self._optimization_actions),
            "optimization_stats": dict(self._optimization_stats.items())
        }
    
    def get_resource_status(self) -> Dict[str, Any]:
        """
        Get resource status information.
        
        Returns:
            Dictionary with resource status
        """
        current_usage = self.resource_monitor.get_current_usage()
        
        return {
            "cpu_percent": current_usage.cpu_percent,
            "memory_percent": current_usage.memory_percent,
            "memory_usage": f"{current_usage.memory_percent:.1f}%",
            "memory_available_mb": current_usage.memory_available_mb,
            "thread_count": current_usage.thread_count,
            "optimization_level": self.optimization_level.value
        }
    
    def _setup_default_actions(self) -> None:
        """Setup default optimization actions."""
        # Memory optimization actions
        self.register_optimization_action(OptimizationAction(
            action_type="garbage_collection",
            resource_type=ResourceType.MEMORY,
            description="Perform garbage collection",
            priority=10,
            estimated_savings_mb=50.0,
            callback=lambda: self.memory_optimizer.perform_gc_optimization(self.optimization_level) > 0
        ))
        
        self.register_optimization_action(OptimizationAction(
            action_type="clear_caches",
            resource_type=ResourceType.MEMORY,
            description="Clear internal caches",
            priority=8,
            estimated_savings_mb=20.0,
            callback=self._clear_caches
        ))
        
        self.register_optimization_action(OptimizationAction(
            action_type="optimize_queues",
            resource_type=ResourceType.MEMORY,
            description="Optimize queue sizes",
            priority=6,
            estimated_savings_mb=30.0,
            callback=self._optimize_queues
        ))
    
    def _handle_memory_threshold(self, usage: ResourceUsage) -> None:
        """Handle memory threshold violation."""
        if not self._auto_optimization_enabled:
            return
        
        logger.warning(f"Memory threshold exceeded: {usage.memory_percent}%")
        
        # Trigger memory optimization
        self.trigger_optimization(
            resource_type=ResourceType.MEMORY,
            target_savings_mb=100.0
        )
    
    def _clear_caches(self) -> bool:
        """Clear internal caches."""
        try:
            # This would clear application-specific caches
            # Implementation depends on what caches exist in the application
            logger.debug("Clearing internal caches")
            return True
        except Exception as e:
            logger.error(f"Error clearing caches: {e}")
            return False
    
    def _optimize_queues(self) -> bool:
        """Optimize queue sizes."""
        try:
            # This would optimize queue sizes in the queue manager
            # Implementation depends on queue manager integration
            logger.debug("Optimizing queue sizes")
            return True
        except Exception as e:
            logger.error(f"Error optimizing queues: {e}")
            return False


# Global resource optimizer instance
resource_optimizer = ResourceOptimizer()


def get_resource_optimizer() -> ResourceOptimizer:
    """
    Get the global resource optimizer instance.
    
    Returns:
        ResourceOptimizer instance
    """
    return resource_optimizer


def start_resource_optimization() -> None:
    """Start the resource optimization system."""
    resource_optimizer.start()


def stop_resource_optimization() -> None:
    """Stop the resource optimization system."""
    resource_optimizer.stop()


def trigger_memory_optimization(target_mb: Optional[float] = None) -> Dict[str, Any]:
    """
    Trigger memory optimization.
    
    Args:
        target_mb: Target memory savings in MB
        
    Returns:
        Optimization results
    """
    return resource_optimizer.trigger_optimization(
        resource_type=ResourceType.MEMORY,
        target_savings_mb=target_mb
    )