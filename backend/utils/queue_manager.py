"""
Advanced queue management system for DeepEcho.

This module provides optimized queue implementations with memory management,
monitoring, and automatic cleanup for improved performance and resource usage.
"""

import queue
import threading
import time
import weakref
from typing import Any, Optional, Callable, Dict, List, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import psutil

from .logger import get_logger
from .threading import ThreadSafeCounter, ThreadSafeDict

logger = get_logger(__name__)


class QueueType(Enum):
    """Queue type enumeration."""
    FIFO = "fifo"
    LIFO = "lifo"
    PRIORITY = "priority"


class QueueState(Enum):
    """Queue state enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    DRAINING = "draining"
    STOPPED = "stopped"


@dataclass
class QueueMetrics:
    """Queue performance metrics."""
    name: str
    queue_type: QueueType
    current_size: int
    max_size: int
    total_items_processed: int
    total_items_dropped: int
    average_processing_time: float
    peak_size: int
    memory_usage_mb: float
    last_activity: datetime
    state: QueueState


class ManagedQueue:
    """
    Enhanced queue with monitoring, memory management, and automatic cleanup.
    
    Provides better control over queue behavior, resource usage monitoring,
    and automatic optimization based on system conditions.
    """
    
    def __init__(
        self,
        name: str,
        maxsize: int = 1000,
        queue_type: QueueType = QueueType.FIFO,
        auto_cleanup: bool = True,
        cleanup_threshold: float = 0.8,
        max_age_seconds: float = 300.0,
        drop_policy: str = "oldest"
    ):
        """
        Initialize managed queue.
        
        Args:
            name: Queue name for identification
            maxsize: Maximum queue size (0 for unlimited)
            queue_type: Type of queue (FIFO, LIFO, PRIORITY)
            auto_cleanup: Enable automatic cleanup
            cleanup_threshold: Cleanup when queue reaches this fraction of maxsize
            max_age_seconds: Maximum age of items before cleanup
            drop_policy: Policy for dropping items ("oldest", "newest", "random")
        """
        self.name = name
        self.maxsize = maxsize
        self.queue_type = queue_type
        self.auto_cleanup = auto_cleanup
        self.cleanup_threshold = cleanup_threshold
        self.max_age_seconds = max_age_seconds
        self.drop_policy = drop_policy
        
        # Create appropriate queue type
        if queue_type == QueueType.FIFO:
            self._queue = queue.Queue(maxsize=maxsize)
        elif queue_type == QueueType.LIFO:
            self._queue = queue.LifoQueue(maxsize=maxsize)
        elif queue_type == QueueType.PRIORITY:
            self._queue = queue.PriorityQueue(maxsize=maxsize)
        else:
            raise ValueError(f"Unsupported queue type: {queue_type}")
        
        # State management
        self._state = QueueState.ACTIVE
        self._lock = threading.RLock()
        
        # Metrics tracking
        self._processed_count = ThreadSafeCounter()
        self._dropped_count = ThreadSafeCounter()
        self._peak_size = ThreadSafeCounter()
        self._processing_times: List[float] = []
        self._last_activity = datetime.now()
        
        # Item tracking for age-based cleanup
        self._item_timestamps: Dict[Any, datetime] = {}
        
        # Cleanup thread
        self._cleanup_thread: Optional[threading.Thread] = None
        self._cleanup_stop_event = threading.Event()
        
        if auto_cleanup:
            self._start_cleanup_thread()
        
        logger.debug(f"Created managed queue: {name} (type={queue_type.value}, maxsize={maxsize})")
    
    def put(
        self,
        item: Any,
        block: bool = True,
        timeout: Optional[float] = None,
        priority: int = 0
    ) -> bool:
        """
        Put item into queue with enhanced monitoring.
        
        Args:
            item: Item to put in queue
            block: Whether to block if queue is full
            timeout: Timeout for blocking put
            priority: Priority for priority queues (lower = higher priority)
            
        Returns:
            True if item was successfully added
        """
        if self._state != QueueState.ACTIVE:
            logger.warning(f"Queue {self.name} is not active (state: {self._state})")
            return False
        
        try:
            with self._lock:
                # Check if cleanup is needed before adding
                if self.auto_cleanup and self._should_cleanup():
                    self._perform_cleanup()
                
                # Prepare item for priority queue
                if self.queue_type == QueueType.PRIORITY:
                    queue_item = (priority, time.time(), item)  # Use timestamp for tie-breaking
                else:
                    queue_item = item
                
                # Try to put item
                self._queue.put(queue_item, block=block, timeout=timeout)
                
                # Track item timestamp for age-based cleanup
                self._item_timestamps[id(item)] = datetime.now()
                
                # Update metrics
                current_size = self._queue.qsize()
                if current_size > self._peak_size.get():
                    self._peak_size.set(current_size)
                
                self._last_activity = datetime.now()
                
                logger.debug(f"Added item to queue {self.name} (size: {current_size})")
                return True
                
        except queue.Full:
            # Handle full queue based on drop policy
            if not block:
                dropped = self._handle_full_queue(item, priority)
                if dropped:
                    self._dropped_count.increment()
                    logger.warning(f"Dropped item from full queue {self.name}")
                return dropped
            else:
                logger.warning(f"Queue {self.name} is full and blocking")
                return False
        except Exception as e:
            logger.error(f"Error putting item in queue {self.name}: {e}")
            return False
    
    def get(
        self,
        block: bool = True,
        timeout: Optional[float] = None
    ) -> Tuple[bool, Any]:
        """
        Get item from queue with enhanced monitoring.
        
        Args:
            block: Whether to block if queue is empty
            timeout: Timeout for blocking get
            
        Returns:
            Tuple of (success, item)
        """
        if self._state == QueueState.STOPPED:
            return False, None
        
        try:
            start_time = time.time()
            queue_item = self._queue.get(block=block, timeout=timeout)
            processing_time = time.time() - start_time
            
            # Extract actual item from priority queue wrapper
            if self.queue_type == QueueType.PRIORITY:
                _, _, actual_item = queue_item
            else:
                actual_item = queue_item
            
            # Update metrics
            with self._lock:
                self._processed_count.increment()
                self._processing_times.append(processing_time)
                
                # Keep only recent processing times for average calculation
                if len(self._processing_times) > 100:
                    self._processing_times = self._processing_times[-50:]
                
                # Remove timestamp tracking
                item_id = id(actual_item)
                self._item_timestamps.pop(item_id, None)
                
                self._last_activity = datetime.now()
            
            logger.debug(f"Retrieved item from queue {self.name} (size: {self._queue.qsize()})")
            return True, actual_item
            
        except queue.Empty:
            return False, None
        except Exception as e:
            logger.error(f"Error getting item from queue {self.name}: {e}")
            return False, None
    
    def get_nowait(self) -> Tuple[bool, Any]:
        """
        Get item from queue without blocking.
        
        Returns:
            Tuple of (success, item)
        """
        return self.get(block=False)
    
    def put_nowait(self, item: Any, priority: int = 0) -> bool:
        """
        Put item in queue without blocking.
        
        Args:
            item: Item to put
            priority: Priority for priority queues
            
        Returns:
            True if item was added successfully
        """
        return self.put(item, block=False, priority=priority)
    
    def size(self) -> int:
        """
        Get current queue size.
        
        Returns:
            Number of items in queue
        """
        return self._queue.qsize()
    
    def empty(self) -> bool:
        """
        Check if queue is empty.
        
        Returns:
            True if queue is empty
        """
        return self._queue.empty()
    
    def full(self) -> bool:
        """
        Check if queue is full.
        
        Returns:
            True if queue is full
        """
        return self._queue.full()
    
    def clear(self) -> int:
        """
        Clear all items from queue.
        
        Returns:
            Number of items removed
        """
        with self._lock:
            removed_count = 0
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    removed_count += 1
                except queue.Empty:
                    break
            
            self._item_timestamps.clear()
            logger.info(f"Cleared {removed_count} items from queue {self.name}")
            return removed_count
    
    def pause(self) -> None:
        """Pause queue operations."""
        with self._lock:
            if self._state == QueueState.ACTIVE:
                self._state = QueueState.PAUSED
                logger.info(f"Paused queue {self.name}")
    
    def resume(self) -> None:
        """Resume queue operations."""
        with self._lock:
            if self._state == QueueState.PAUSED:
                self._state = QueueState.ACTIVE
                logger.info(f"Resumed queue {self.name}")
    
    def drain(self, timeout: float = 30.0) -> List[Any]:
        """
        Drain all items from queue.
        
        Args:
            timeout: Maximum time to wait for draining
            
        Returns:
            List of drained items
        """
        with self._lock:
            self._state = QueueState.DRAINING
            
        drained_items = []
        start_time = time.time()
        
        while not self._queue.empty() and (time.time() - start_time) < timeout:
            success, item = self.get_nowait()
            if success:
                drained_items.append(item)
            else:
                break
        
        logger.info(f"Drained {len(drained_items)} items from queue {self.name}")
        return drained_items
    
    def stop(self) -> None:
        """Stop queue and cleanup resources."""
        with self._lock:
            self._state = QueueState.STOPPED
            
            # Stop cleanup thread
            if self._cleanup_thread and self._cleanup_thread.is_alive():
                self._cleanup_stop_event.set()
                self._cleanup_thread.join(timeout=2.0)
            
            logger.info(f"Stopped queue {self.name}")
    
    def get_metrics(self) -> QueueMetrics:
        """
        Get queue performance metrics.
        
        Returns:
            QueueMetrics object with current metrics
        """
        with self._lock:
            # Calculate average processing time
            avg_processing_time = (
                sum(self._processing_times) / len(self._processing_times)
                if self._processing_times else 0.0
            )
            
            # Estimate memory usage
            try:
                import sys
                queue_size = self._queue.qsize()
                estimated_memory = queue_size * sys.getsizeof(object()) / (1024 * 1024)  # MB
            except:
                estimated_memory = 0.0
            
            return QueueMetrics(
                name=self.name,
                queue_type=self.queue_type,
                current_size=self._queue.qsize(),
                max_size=self.maxsize,
                total_items_processed=self._processed_count.get(),
                total_items_dropped=self._dropped_count.get(),
                average_processing_time=avg_processing_time,
                peak_size=self._peak_size.get(),
                memory_usage_mb=estimated_memory,
                last_activity=self._last_activity,
                state=self._state
            )
    
    def _should_cleanup(self) -> bool:
        """Check if cleanup should be performed."""
        if not self.auto_cleanup:
            return False
        
        current_size = self._queue.qsize()
        
        # Check size threshold
        if self.maxsize > 0 and current_size >= (self.maxsize * self.cleanup_threshold):
            return True
        
        # Check age threshold
        if self.max_age_seconds > 0:
            cutoff_time = datetime.now() - timedelta(seconds=self.max_age_seconds)
            old_items = sum(1 for ts in self._item_timestamps.values() if ts < cutoff_time)
            if old_items > 0:
                return True
        
        return False
    
    def _perform_cleanup(self) -> int:
        """
        Perform queue cleanup.
        
        Returns:
            Number of items removed
        """
        removed_count = 0
        
        # Age-based cleanup
        if self.max_age_seconds > 0:
            cutoff_time = datetime.now() - timedelta(seconds=self.max_age_seconds)
            old_item_ids = [
                item_id for item_id, timestamp in self._item_timestamps.items()
                if timestamp < cutoff_time
            ]
            
            # Remove old items (this is approximate since we can't easily remove specific items from queue)
            for _ in old_item_ids[:min(len(old_item_ids), 10)]:  # Limit cleanup batch size
                try:
                    self._queue.get_nowait()
                    removed_count += 1
                except queue.Empty:
                    break
        
        # Size-based cleanup
        if self.maxsize > 0:
            target_size = int(self.maxsize * 0.7)  # Reduce to 70% of max size
            current_size = self._queue.qsize()
            
            if current_size > target_size:
                items_to_remove = current_size - target_size
                for _ in range(items_to_remove):
                    try:
                        self._queue.get_nowait()
                        removed_count += 1
                    except queue.Empty:
                        break
        
        if removed_count > 0:
            self._dropped_count.increment(removed_count)
            logger.info(f"Cleaned up {removed_count} items from queue {self.name}")
        
        return removed_count
    
    def _handle_full_queue(self, item: Any, priority: int = 0) -> bool:
        """
        Handle full queue based on drop policy.
        
        Args:
            item: New item to add
            priority: Item priority
            
        Returns:
            True if item was added (by dropping another item)
        """
        if self.drop_policy == "oldest":
            # Drop oldest item and add new one
            try:
                self._queue.get_nowait()
                return self.put_nowait(item, priority)
            except queue.Empty:
                return False
        elif self.drop_policy == "newest":
            # Drop the new item
            return False
        else:
            # Default: drop new item
            return False
    
    def _start_cleanup_thread(self) -> None:
        """Start background cleanup thread."""
        self._cleanup_stop_event.clear()
        self._cleanup_thread = threading.Thread(
            target=self._cleanup_loop,
            daemon=True,
            name=f"QueueCleanup_{self.name}"
        )
        self._cleanup_thread.start()
    
    def _cleanup_loop(self) -> None:
        """Background cleanup loop."""
        while not self._cleanup_stop_event.is_set():
            try:
                if self._should_cleanup():
                    self._perform_cleanup()
            except Exception as e:
                logger.error(f"Error in cleanup loop for queue {self.name}: {e}")
            
            # Wait before next cleanup check
            self._cleanup_stop_event.wait(30.0)  # Check every 30 seconds


class QueueManager:
    """
    Central queue management system for DeepEcho.
    
    Provides centralized management, monitoring, and optimization
    of all application queues.
    """
    
    def __init__(self):
        """Initialize queue manager."""
        self._queues: Dict[str, ManagedQueue] = {}
        self._lock = threading.RLock()
        
        # Global monitoring
        self._monitor_thread: Optional[threading.Thread] = None
        self._monitor_stop_event = threading.Event()
        self._monitor_interval = 60.0  # Monitor every minute
        
        # Resource limits
        self._global_memory_limit_mb = 500  # 500MB total for all queues
        
        logger.info("Queue manager initialized")
    
    def create_queue(
        self,
        name: str,
        maxsize: int = 1000,
        queue_type: QueueType = QueueType.FIFO,
        auto_cleanup: bool = True,
        **kwargs
    ) -> Optional[ManagedQueue]:
        """
        Create a new managed queue.
        
        Args:
            name: Queue name (must be unique)
            maxsize: Maximum queue size
            queue_type: Type of queue
            auto_cleanup: Enable automatic cleanup
            **kwargs: Additional queue parameters
            
        Returns:
            ManagedQueue instance or None if creation failed
        """
        with self._lock:
            if name in self._queues:
                logger.error(f"Queue with name '{name}' already exists")
                return None
            
            try:
                managed_queue = ManagedQueue(
                    name=name,
                    maxsize=maxsize,
                    queue_type=queue_type,
                    auto_cleanup=auto_cleanup,
                    **kwargs
                )
                
                self._queues[name] = managed_queue
                logger.info(f"Created queue: {name}")
                return managed_queue
                
            except Exception as e:
                logger.error(f"Failed to create queue {name}: {e}")
                return None
    
    def get_queue(self, name: str) -> Optional[ManagedQueue]:
        """
        Get managed queue by name.
        
        Args:
            name: Queue name
            
        Returns:
            ManagedQueue instance or None if not found
        """
        with self._lock:
            return self._queues.get(name)
    
    def remove_queue(self, name: str) -> bool:
        """
        Remove a managed queue.
        
        Args:
            name: Queue name
            
        Returns:
            True if queue was removed
        """
        with self._lock:
            managed_queue = self._queues.get(name)
            if not managed_queue:
                logger.error(f"Queue '{name}' not found")
                return False
            
            # Stop and cleanup queue
            managed_queue.stop()
            del self._queues[name]
            
            logger.info(f"Removed queue: {name}")
            return True
    
    def list_queues(self) -> List[str]:
        """
        Get list of all managed queue names.
        
        Returns:
            List of queue names
        """
        with self._lock:
            return list(self._queues.keys())
    
    def get_queue_metrics(self, name: Optional[str] = None) -> Union[QueueMetrics, Dict[str, QueueMetrics]]:
        """
        Get queue metrics.
        
        Args:
            name: Queue name (None for all queues)
            
        Returns:
            QueueMetrics for specific queue or dict of all metrics
        """
        with self._lock:
            if name:
                managed_queue = self._queues.get(name)
                if managed_queue:
                    return managed_queue.get_metrics()
                else:
                    raise ValueError(f"Queue '{name}' not found")
            else:
                return {name: q.get_metrics() for name, q in self._queues.items()}
    
    def start_monitoring(self) -> None:
        """Start global queue monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            logger.warning("Queue monitoring already started")
            return
        
        self._monitor_stop_event.clear()
        self._monitor_thread = threading.Thread(
            target=self._monitor_loop,
            daemon=True,
            name="QueueManager_Monitor"
        )
        self._monitor_thread.start()
        logger.info("Queue monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop global queue monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_stop_event.set()
            self._monitor_thread.join(timeout=2.0)
        logger.info("Queue monitoring stopped")
    
    def _monitor_loop(self) -> None:
        """Global queue monitoring loop."""
        while not self._monitor_stop_event.is_set():
            try:
                self._check_global_memory_usage()
                self._optimize_queue_performance()
                self._cleanup_inactive_queues()
            except Exception as e:
                logger.error(f"Error in queue monitoring: {e}")
            
            self._monitor_stop_event.wait(self._monitor_interval)
    
    def _check_global_memory_usage(self) -> None:
        """Check global memory usage across all queues."""
        with self._lock:
            total_memory = 0
            for managed_queue in self._queues.values():
                metrics = managed_queue.get_metrics()
                total_memory += metrics.memory_usage_mb
            
            if total_memory > self._global_memory_limit_mb:
                logger.warning(f"Global queue memory usage exceeds limit: {total_memory}MB")
                self._reduce_memory_usage()
    
    def _reduce_memory_usage(self) -> None:
        """Reduce memory usage across queues."""
        with self._lock:
            # Get queues sorted by memory usage (highest first)
            queue_memory = []
            for name, managed_queue in self._queues.items():
                metrics = managed_queue.get_metrics()
                queue_memory.append((metrics.memory_usage_mb, name, managed_queue))
            
            queue_memory.sort(reverse=True)
            
            # Cleanup largest queues first
            for memory_mb, name, managed_queue in queue_memory[:3]:  # Top 3 memory users
                if memory_mb > 50:  # Only cleanup queues using significant memory
                    logger.info(f"Performing memory cleanup on queue {name} ({memory_mb}MB)")
                    managed_queue._perform_cleanup()
    
    def _optimize_queue_performance(self) -> None:
        """Optimize queue performance based on usage patterns."""
        with self._lock:
            for name, managed_queue in self._queues.items():
                try:
                    metrics = managed_queue.get_metrics()
                    
                    # Adjust cleanup thresholds based on usage
                    if metrics.average_processing_time > 1.0:  # Slow processing
                        # Reduce queue size to prevent backlog
                        if managed_queue.maxsize > 100:
                            logger.debug(f"Optimizing queue {name} for slow processing")
                    
                    # Check for stalled queues
                    time_since_activity = datetime.now() - metrics.last_activity
                    if time_since_activity > timedelta(minutes=10) and metrics.current_size > 0:
                        logger.warning(f"Queue {name} appears stalled, forcing cleanup")
                        managed_queue._perform_cleanup()
                        
                except Exception as e:
                    logger.error(f"Error optimizing queue {name}: {e}")
    
    def _cleanup_inactive_queues(self) -> None:
        """Clean up queues that have been inactive for a long time."""
        with self._lock:
            inactive_queues = []
            cutoff_time = datetime.now() - timedelta(hours=1)
            
            for name, managed_queue in self._queues.items():
                try:
                    metrics = managed_queue.get_metrics()
                    if (metrics.last_activity < cutoff_time and 
                        metrics.current_size == 0 and 
                        metrics.state == QueueState.ACTIVE):
                        inactive_queues.append(name)
                except Exception as e:
                    logger.error(f"Error checking queue {name} activity: {e}")
            
            # Pause inactive queues to save resources
            for name in inactive_queues:
                logger.info(f"Pausing inactive queue: {name}")
                self._queues[name].pause()
    
    def stop_all_queues(self) -> None:
        """Stop all managed queues."""
        logger.info("Stopping all managed queues")
        
        # Stop monitoring first
        self.stop_monitoring()
        
        with self._lock:
            for managed_queue in self._queues.values():
                managed_queue.stop()
            
            self._queues.clear()
        
        logger.info("All queues stopped")
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive queue system status.
        
        Returns:
            Dictionary with system status information
        """
        with self._lock:
            total_memory = 0
            total_items = 0
            total_processed = 0
            queue_states = {}
            
            for name, managed_queue in self._queues.items():
                metrics = managed_queue.get_metrics()
                queue_states[name] = {
                    "size": metrics.current_size,
                    "memory_mb": metrics.memory_usage_mb,
                    "processed": metrics.total_items_processed,
                    "state": metrics.state.value
                }
                total_memory += metrics.memory_usage_mb
                total_items += metrics.current_size
                total_processed += metrics.total_items_processed
            
            return {
                "total_queues": len(self._queues),
                "total_items": total_items,
                "total_memory_mb": total_memory,
                "total_processed": total_processed,
                "memory_limit_mb": self._global_memory_limit_mb,
                "monitoring_active": self._monitor_thread is not None and self._monitor_thread.is_alive(),
                "queue_states": queue_states
            }
    
    def get_queue_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all managed queues.
        
        Returns:
            Dictionary mapping queue names to their status information
        """
        with self._lock:
            status = {}
            for name, managed_queue in self._queues.items():
                metrics = managed_queue.get_metrics()
                status[name] = {
                    "size": metrics.current_size,
                    "max_size": metrics.max_size,
                    "memory_mb": metrics.memory_usage_mb,
                    "processed": metrics.total_items_processed,
                    "dropped": metrics.total_items_dropped,
                    "state": metrics.state.value,
                    "type": managed_queue.queue_type.value
                }
            return status


# Global queue manager instance
queue_manager = QueueManager()


def get_queue_manager() -> QueueManager:
    """
    Get the global queue manager instance.
    
    Returns:
        QueueManager instance
    """
    return queue_manager


def create_managed_queue(
    name: str,
    maxsize: int = 1000,
    queue_type: QueueType = QueueType.FIFO,
    auto_cleanup: bool = True
) -> Optional[ManagedQueue]:
    """
    Create a managed queue with default settings.
    
    Args:
        name: Queue name
        maxsize: Maximum queue size
        queue_type: Type of queue
        auto_cleanup: Enable automatic cleanup
        
    Returns:
        ManagedQueue instance or None if creation failed
    """
    return queue_manager.create_queue(
        name=name,
        maxsize=maxsize,
        queue_type=queue_type,
        auto_cleanup=auto_cleanup
    )


def shutdown_queue_system() -> None:
    """Shutdown the queue system gracefully."""
    logger.info("Shutting down queue system")
    queue_manager.stop_all_queues()
    logger.info("Queue system shutdown complete")