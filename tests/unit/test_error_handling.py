"""
Unit tests for error handling and reliability improvements.

Tests network failure scenarios, device disconnection handling,
resource limit scenarios, and error recovery mechanisms.
"""

import unittest
import time
import threading
import queue
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock, Mock, call
from datetime import datetime, timedelta

import requests
import psutil

from backend.utils.retry import (
    RetryConfig, retry_with_backoff, RetryState, CircuitBreaker,
    circuit_breaker, GracefulDegradation, with_graceful_degradation
)
from backend.utils.error_recovery import (
    SystemHealthMonitor, ErrorTracker, DeviceRecoveryManager,
    ResourceCleanupManager, SystemHealthStatus, ResourceMetrics,
    ErrorEvent, error_tracker, device_recovery_manager,
    resource_cleanup_manager, system_health_monitor
)
from backend.utils.exceptions import (
    DeepEchoError, AudioError, AudioDeviceError, AIProviderError,
    AIProviderConnectionError, AIProviderTimeoutError
)


class TestRetryMechanisms(unittest.TestCase):
    """Test cases for retry mechanisms and exponential backoff."""
    
    def test_retry_config_delay_calculation(self):
        """Test retry configuration delay calculation."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=1.0,
            max_delay=10.0,
            backoff_factor=2.0,
            jitter=False
        )
        
        # Test exponential backoff
        self.assertEqual(config.calculate_delay(0), 1.0)  # 1.0 * 2^0
        self.assertEqual(config.calculate_delay(1), 2.0)  # 1.0 * 2^1
        self.assertEqual(config.calculate_delay(2), 4.0)  # 1.0 * 2^2
        self.assertEqual(config.calculate_delay(3), 8.0)  # 1.0 * 2^3
        
        # Test max delay cap
        self.assertEqual(config.calculate_delay(10), 10.0)  # Capped at max_delay
    
    def test_retry_config_with_jitter(self):
        """Test retry configuration with jitter enabled."""
        config = RetryConfig(
            base_delay=1.0,
            jitter=True,
            jitter_range=0.1
        )
        
        # With jitter, delay should vary around base value
        delay1 = config.calculate_delay(0)
        delay2 = config.calculate_delay(0)
        
        # Both should be close to 1.0 but potentially different
        self.assertGreaterEqual(delay1, 0.9)
        self.assertLessEqual(delay1, 1.1)
        self.assertGreaterEqual(delay2, 0.9)
        self.assertLessEqual(delay2, 1.1)
    
    def test_retry_state_tracking(self):
        """Test retry state tracking functionality."""
        config = RetryConfig(max_attempts=3)
        state = RetryState(config)
        
        # Initial state
        self.assertEqual(state.attempt, 0)
        self.assertTrue(state.should_retry())
        self.assertIsNone(state.last_exception)
        
        # Record attempts
        error1 = Exception("First error")
        state.record_attempt(error1)
        self.assertEqual(state.attempt, 1)
        self.assertTrue(state.should_retry())
        self.assertEqual(state.last_exception, error1)
        
        error2 = Exception("Second error")
        state.record_attempt(error2)
        self.assertEqual(state.attempt, 2)
        self.assertTrue(state.should_retry())
        
        error3 = Exception("Third error")
        state.record_attempt(error3)
        self.assertEqual(state.attempt, 3)
        self.assertFalse(state.should_retry())  # Max attempts reached
    
    @patch('time.sleep')
    def test_retry_decorator_success_after_failures(self, mock_sleep):
        """Test retry decorator with success after initial failures."""
        call_count = 0
        
        @retry_with_backoff(
            exceptions=ValueError,
            config=RetryConfig(max_attempts=3, base_delay=0.1)
        )
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError(f"Attempt {call_count} failed")
            return "success"
        
        result = failing_function()
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)  # 2 retries
    
    @patch('time.sleep')
    def test_retry_decorator_all_attempts_fail(self, mock_sleep):
        """Test retry decorator when all attempts fail."""
        call_count = 0
        
        @retry_with_backoff(
            exceptions=ValueError,
            config=RetryConfig(max_attempts=3, base_delay=0.1)
        )
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"Attempt {call_count} failed")
        
        with self.assertRaises(ValueError) as context:
            always_failing_function()
        
        self.assertIn("Attempt 3 failed", str(context.exception))
        self.assertEqual(call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)
    
    def test_retry_decorator_non_retryable_exception(self):
        """Test retry decorator with non-retryable exception."""
        call_count = 0
        
        @retry_with_backoff(
            exceptions=ValueError,  # Only retry on ValueError
            config=RetryConfig(max_attempts=3)
        )
        def function_with_different_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("This should not be retried")
        
        with self.assertRaises(TypeError):
            function_with_different_error()
        
        self.assertEqual(call_count, 1)  # Should not retry
    
    def test_retry_callbacks(self):
        """Test retry decorator with callback functions."""
        retry_calls = []
        failure_calls = []
        
        def on_retry(state):
            retry_calls.append(state.attempt)
        
        def on_failure(state):
            failure_calls.append(state.attempt)
        
        @retry_with_backoff(
            exceptions=ValueError,
            config=RetryConfig(max_attempts=2, base_delay=0.01),
            on_retry=on_retry,
            on_failure=on_failure
        )
        def failing_function():
            raise ValueError("Always fails")
        
        with self.assertRaises(ValueError):
            failing_function()
        
        self.assertEqual(retry_calls, [1])  # Called once before second attempt
        self.assertEqual(failure_calls, [2])  # Called once after all attempts fail


class TestCircuitBreaker(unittest.TestCase):
    """Test cases for circuit breaker pattern."""
    
    def test_circuit_breaker_closed_state(self):
        """Test circuit breaker in closed state."""
        breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=1.0)
        
        # Should start in closed state
        self.assertEqual(breaker.state, "closed")
        
        # Successful calls should work normally
        result = breaker.call(lambda: "success")
        self.assertEqual(result, "success")
        self.assertEqual(breaker.failure_count, 0)
    
    def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1.0)
        
        # First failure
        with self.assertRaises(ValueError):
            breaker.call(lambda: exec('raise ValueError("fail")'))
        self.assertEqual(breaker.state, "closed")
        self.assertEqual(breaker.failure_count, 1)
        
        # Second failure - should open circuit
        with self.assertRaises(ValueError):
            breaker.call(lambda: exec('raise ValueError("fail")'))
        self.assertEqual(breaker.state, "open")
        self.assertEqual(breaker.failure_count, 2)
        
        # Subsequent calls should fail immediately
        with self.assertRaises(DeepEchoError) as context:
            breaker.call(lambda: "should not execute")
        self.assertIn("Circuit breaker is open", str(context.exception))
    
    def test_circuit_breaker_recovery(self):
        """Test circuit breaker recovery after timeout."""
        breaker = CircuitBreaker(failure_threshold=1, recovery_timeout=0.1)
        
        # Cause failure to open circuit
        with self.assertRaises(ValueError):
            breaker.call(lambda: exec('raise ValueError("fail")'))
        self.assertEqual(breaker.state, "open")
        
        # Wait for recovery timeout
        time.sleep(0.2)
        
        # Next call should transition to half-open
        result = breaker.call(lambda: "success")
        self.assertEqual(result, "success")
        self.assertEqual(breaker.state, "closed")  # Success resets to closed
        self.assertEqual(breaker.failure_count, 0)
    
    def test_circuit_breaker_decorator(self):
        """Test circuit breaker decorator."""
        @circuit_breaker(failure_threshold=2, recovery_timeout=0.1)
        def test_function(should_fail=False):
            if should_fail:
                raise ValueError("Intentional failure")
            return "success"
        
        # Successful calls
        self.assertEqual(test_function(), "success")
        
        # Cause failures to open circuit
        with self.assertRaises(ValueError):
            test_function(should_fail=True)
        with self.assertRaises(ValueError):
            test_function(should_fail=True)
        
        # Circuit should be open now
        with self.assertRaises(DeepEchoError):
            test_function()
        
        # Access circuit breaker instance
        self.assertEqual(test_function.circuit_breaker.state, "open")


class TestGracefulDegradation(unittest.TestCase):
    """Test cases for graceful degradation patterns."""
    
    def test_graceful_degradation_primary_success(self):
        """Test graceful degradation when primary function succeeds."""
        degradation = GracefulDegradation("test")
        degradation.add_fallback(lambda: "fallback1", "First fallback")
        degradation.add_fallback(lambda: "fallback2", "Second fallback")
        
        result = degradation.execute_with_fallbacks(lambda: "primary")
        self.assertEqual(result, "primary")
    
    def test_graceful_degradation_fallback_chain(self):
        """Test graceful degradation fallback chain."""
        degradation = GracefulDegradation("test")
        degradation.add_fallback(lambda: exec('raise ValueError("fallback1 fails")'), "First fallback")
        degradation.add_fallback(lambda: "fallback2 success", "Second fallback")
        
        # Primary fails, first fallback fails, second fallback succeeds
        result = degradation.execute_with_fallbacks(
            lambda: exec('raise RuntimeError("primary fails")')
        )
        self.assertEqual(result, "fallback2 success")
    
    def test_graceful_degradation_all_fail(self):
        """Test graceful degradation when all functions fail."""
        degradation = GracefulDegradation("test")
        degradation.add_fallback(lambda: exec('raise ValueError("fallback fails")'), "Fallback")
        
        with self.assertRaises(DeepEchoError) as context:
            degradation.execute_with_fallbacks(
                lambda: exec('raise RuntimeError("primary fails")')
            )
        
        self.assertIn("All functions failed for test", str(context.exception))
    
    def test_graceful_degradation_decorator(self):
        """Test graceful degradation decorator."""
        def fallback1():
            raise ValueError("Fallback1 fails")
        
        def fallback2():
            return "fallback2 result"
        
        @with_graceful_degradation(
            fallbacks=[(fallback1, "First fallback"), (fallback2, "Second fallback")],
            name="decorated_function"
        )
        def primary_function(should_fail=False):
            if should_fail:
                raise RuntimeError("Primary fails")
            return "primary result"
        
        # Primary succeeds
        self.assertEqual(primary_function(), "primary result")
        
        # Primary fails, fallback chain executes
        self.assertEqual(primary_function(should_fail=True), "fallback2 result")


class TestSystemHealthMonitor(unittest.TestCase):
    """Test cases for system health monitoring."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.monitor = SystemHealthMonitor(
            cpu_threshold=80.0,
            memory_threshold=85.0,
            check_interval=0.1
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        if self.monitor.is_monitoring:
            self.monitor.stop_monitoring()
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_connections')
    @patch('psutil.Process')
    def test_collect_metrics(self, mock_process, mock_net, mock_disk, mock_memory, mock_cpu):
        """Test system metrics collection."""
        # Mock system metrics
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(percent=60.0, available=2048*1024*1024)
        mock_disk.return_value = Mock(used=500*1024*1024*1024, total=1000*1024*1024*1024)
        mock_net.return_value = [Mock(), Mock(), Mock()]  # 3 connections
        mock_process.return_value.num_threads.return_value = 8
        
        metrics = self.monitor._collect_metrics()
        
        self.assertEqual(metrics.cpu_percent, 45.5)
        self.assertEqual(metrics.memory_percent, 60.0)
        self.assertEqual(metrics.memory_available_mb, 2048.0)
        self.assertEqual(metrics.disk_usage_percent, 50.0)
        self.assertEqual(metrics.network_connections, 3)
        self.assertEqual(metrics.thread_count, 8)
        self.assertIsInstance(metrics.timestamp, datetime)
    
    def test_assess_health_healthy(self):
        """Test health assessment for healthy system."""
        metrics = ResourceMetrics(
            cpu_percent=50.0,
            memory_percent=60.0,
            memory_available_mb=1024.0,
            disk_usage_percent=70.0,
            network_connections=5,
            thread_count=10,
            timestamp=datetime.now()
        )
        
        status = self.monitor._assess_health(metrics)
        self.assertEqual(status, SystemHealthStatus.HEALTHY)
    
    def test_assess_health_degraded(self):
        """Test health assessment for degraded system."""
        metrics = ResourceMetrics(
            cpu_percent=85.0,  # Above threshold
            memory_percent=90.0,  # Above threshold
            memory_available_mb=400.0,  # Low but not critical
            disk_usage_percent=95.0,  # Above threshold
            network_connections=5,
            thread_count=10,
            timestamp=datetime.now()
        )
        
        status = self.monitor._assess_health(metrics)
        self.assertEqual(status, SystemHealthStatus.DEGRADED)
    
    def test_assess_health_critical(self):
        """Test health assessment for critical system."""
        metrics = ResourceMetrics(
            cpu_percent=98.0,  # Critical
            memory_percent=97.0,  # Critical
            memory_available_mb=50.0,  # Critical
            disk_usage_percent=99.0,  # Critical
            network_connections=5,
            thread_count=10,
            timestamp=datetime.now()
        )
        
        status = self.monitor._assess_health(metrics)
        self.assertEqual(status, SystemHealthStatus.CRITICAL)
    
    def test_health_monitoring_callbacks(self):
        """Test health monitoring with status change callbacks."""
        callback_calls = []
        
        def health_callback(status, metrics):
            callback_calls.append((status, metrics.cpu_percent))
        
        self.monitor.add_health_callback(health_callback)
        
        # Mock changing health status
        with patch.object(self.monitor, '_collect_metrics') as mock_collect:
            with patch.object(self.monitor, '_assess_health') as mock_assess:
                # First check - healthy
                mock_collect.return_value = Mock(cpu_percent=50.0)
                mock_assess.return_value = SystemHealthStatus.HEALTHY
                
                self.monitor.start_monitoring()
                time.sleep(0.2)  # Let it run briefly
                
                # Change to degraded
                mock_assess.return_value = SystemHealthStatus.DEGRADED
                time.sleep(0.2)
                
                self.monitor.stop_monitoring()
        
        # Should have received callback for status change
        self.assertGreater(len(callback_calls), 0)


class TestErrorTracker(unittest.TestCase):
    """Test cases for error tracking and analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.tracker = ErrorTracker(max_events=100)
    
    def test_record_error_basic(self):
        """Test basic error recording."""
        error = ValueError("Test error")
        event = self.tracker.record_error(error, "test_component")
        
        self.assertEqual(event.error_type, "ValueError")
        self.assertEqual(event.error_message, "Test error")
        self.assertEqual(event.component, "test_component")
        self.assertEqual(event.severity, "error")
        self.assertFalse(event.recovery_attempted)
        
        # Check tracking data
        self.assertEqual(len(self.tracker.error_events), 1)
        self.assertEqual(self.tracker.error_counts["ValueError"], 1)
        self.assertIn("test_component", self.tracker.component_errors)
    
    def test_record_multiple_errors(self):
        """Test recording multiple errors."""
        errors = [
            (ValueError("Error 1"), "component_a"),
            (TypeError("Error 2"), "component_b"),
            (ValueError("Error 3"), "component_a"),
        ]
        
        for error, component in errors:
            self.tracker.record_error(error, component)
        
        # Check counts
        self.assertEqual(self.tracker.error_counts["ValueError"], 2)
        self.assertEqual(self.tracker.error_counts["TypeError"], 1)
        
        # Check component errors
        self.assertEqual(len(self.tracker.component_errors["component_a"]), 2)
        self.assertEqual(len(self.tracker.component_errors["component_b"]), 1)
    
    def test_record_recovery(self):
        """Test recording recovery attempts."""
        error = RuntimeError("Test error")
        event = self.tracker.record_error(error, "test_component")
        
        # Record successful recovery
        self.tracker.record_recovery(event, successful=True, duration=2.5)
        
        self.assertTrue(event.recovery_attempted)
        self.assertTrue(event.recovery_successful)
        self.assertEqual(event.recovery_duration, 2.5)
    
    def test_error_statistics(self):
        """Test error statistics generation."""
        # Record various errors
        errors = [
            (ValueError("Error 1"), "comp_a", "error"),
            (ValueError("Error 2"), "comp_a", "warning"),
            (TypeError("Error 3"), "comp_b", "error"),
        ]
        
        events = []
        for error, component, severity in errors:
            event = self.tracker.record_error(error, component, severity)
            events.append(event)
        
        # Record some recoveries
        self.tracker.record_recovery(events[0], successful=True, duration=1.0)
        self.tracker.record_recovery(events[1], successful=False, duration=3.0)
        
        # Get statistics
        stats = self.tracker.get_error_statistics()
        
        self.assertEqual(stats["total_errors"], 3)
        self.assertEqual(stats["error_types"]["ValueError"], 2)
        self.assertEqual(stats["error_types"]["TypeError"], 1)
        self.assertEqual(stats["recovery_stats"]["attempted"], 2)
        self.assertEqual(stats["recovery_stats"]["successful"], 1)
        self.assertEqual(stats["recovery_rate"], 0.5)
    
    def test_error_statistics_time_window(self):
        """Test error statistics with time window."""
        # Record old error
        old_error = ValueError("Old error")
        old_event = self.tracker.record_error(old_error, "component")
        old_event.timestamp = datetime.now() - timedelta(hours=2)
        
        # Record recent error
        recent_error = TypeError("Recent error")
        self.tracker.record_error(recent_error, "component")
        
        # Get statistics for last hour
        stats = self.tracker.get_error_statistics(time_window=timedelta(hours=1))
        
        # Should only include recent error
        self.assertEqual(stats["total_errors"], 1)
        self.assertEqual(stats["error_types"]["TypeError"], 1)
        self.assertNotIn("ValueError", stats["error_types"])
    
    def test_frequent_errors(self):
        """Test getting frequent error types."""
        # Record errors with different frequencies
        for _ in range(5):
            self.tracker.record_error(ValueError("Common error"), "component")
        
        for _ in range(3):
            self.tracker.record_error(TypeError("Less common"), "component")
        
        self.tracker.record_error(RuntimeError("Rare error"), "component")
        
        frequent = self.tracker.get_frequent_errors(limit=2)
        
        self.assertEqual(len(frequent), 2)
        self.assertEqual(frequent[0], ("ValueError", 5))
        self.assertEqual(frequent[1], ("TypeError", 3))


class TestDeviceRecoveryManager(unittest.TestCase):
    """Test cases for device recovery management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = DeviceRecoveryManager()
    
    def test_register_device(self):
        """Test device registration."""
        def recovery_strategy(device_id, error):
            return True
        
        self.manager.register_device(
            "test_device",
            recovery_strategy,
            {"type": "audio", "index": 0}
        )
        
        self.assertIn("test_device", self.manager.recovery_strategies)
        self.assertIn("test_device", self.manager.device_states)
        self.assertIn("test_device", self.manager.circuit_breakers)
        self.assertEqual(self.manager.device_states["test_device"]["type"], "audio")
    
    def test_successful_device_recovery(self):
        """Test successful device recovery."""
        recovery_calls = []
        
        def recovery_strategy(device_id, error):
            recovery_calls.append((device_id, str(error)))
            return True
        
        self.manager.register_device("test_device", recovery_strategy)
        
        error = AudioDeviceError("Device disconnected")
        success = self.manager.attempt_device_recovery("test_device", error)
        
        self.assertTrue(success)
        self.assertEqual(len(recovery_calls), 1)
        self.assertEqual(recovery_calls[0][0], "test_device")
        self.assertIn("Device disconnected", recovery_calls[0][1])
    
    def test_failed_device_recovery(self):
        """Test failed device recovery."""
        def recovery_strategy(device_id, error):
            raise RuntimeError("Recovery failed")
        
        self.manager.register_device("test_device", recovery_strategy)
        
        error = AudioDeviceError("Device disconnected")
        success = self.manager.attempt_device_recovery("test_device", error)
        
        self.assertFalse(success)
    
    def test_device_recovery_circuit_breaker(self):
        """Test device recovery with circuit breaker protection."""
        failure_count = 0
        
        def failing_recovery_strategy(device_id, error):
            nonlocal failure_count
            failure_count += 1
            raise RuntimeError(f"Recovery attempt {failure_count} failed")
        
        self.manager.register_device("test_device", failing_recovery_strategy)
        
        error = AudioDeviceError("Device disconnected")
        
        # First few attempts should call recovery strategy
        for i in range(3):
            success = self.manager.attempt_device_recovery("test_device", error)
            self.assertFalse(success)
        
        # Circuit breaker should be open now
        breaker = self.manager.circuit_breakers["test_device"]
        self.assertEqual(breaker.state, "open")
        
        # Further attempts should fail immediately without calling strategy
        old_failure_count = failure_count
        success = self.manager.attempt_device_recovery("test_device", error)
        self.assertFalse(success)
        self.assertEqual(failure_count, old_failure_count)  # Strategy not called
    
    def test_update_device_state(self):
        """Test updating device state."""
        self.manager.register_device("test_device", lambda d, e: True, {"initial": "value"})
        
        self.manager.update_device_state("test_device", {"updated": "new_value", "count": 42})
        
        state = self.manager.get_device_state("test_device")
        self.assertEqual(state["initial"], "value")
        self.assertEqual(state["updated"], "new_value")
        self.assertEqual(state["count"], 42)
    
    def test_recovery_status(self):
        """Test getting recovery status."""
        self.manager.register_device("device1", lambda d, e: True, {"type": "audio"})
        self.manager.register_device("device2", lambda d, e: True, {"type": "network"})
        
        status = self.manager.get_recovery_status()
        
        self.assertIn("device1", status)
        self.assertIn("device2", status)
        self.assertIn("circuit_breaker_state", status["device1"])
        self.assertIn("device_state", status["device1"])


class TestResourceCleanupManager(unittest.TestCase):
    """Test cases for resource cleanup management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = ResourceCleanupManager()
    
    def test_register_cleanup_handler(self):
        """Test registering cleanup handlers."""
        cleanup_calls = []
        
        def cleanup_handler():
            cleanup_calls.append("cleaned")
        
        self.manager.register_cleanup_handler(cleanup_handler)
        
        # Perform cleanup
        results = self.manager.perform_cleanup(force=True)
        
        self.assertEqual(results["handlers_executed"], 1)
        self.assertEqual(len(cleanup_calls), 1)
        self.assertEqual(cleanup_calls[0], "cleaned")
    
    def test_multiple_cleanup_handlers(self):
        """Test multiple cleanup handlers."""
        cleanup_order = []
        
        def handler1():
            cleanup_order.append("handler1")
        
        def handler2():
            cleanup_order.append("handler2")
        
        def handler3():
            raise RuntimeError("Handler3 fails")
        
        self.manager.register_cleanup_handler(handler1)
        self.manager.register_cleanup_handler(handler2)
        self.manager.register_cleanup_handler(handler3)
        
        results = self.manager.perform_cleanup(force=True)
        
        # Should execute successful handlers and record errors
        self.assertEqual(results["handlers_executed"], 2)
        self.assertEqual(len(results["errors"]), 1)
        self.assertIn("Handler3 fails", results["errors"][0])
        self.assertEqual(cleanup_order, ["handler1", "handler2"])
    
    def test_resource_monitors(self):
        """Test resource monitoring."""
        def monitor1():
            return {"queue_size": 150, "memory_mb": 512}
        
        def monitor2():
            return {"connections": 25}
        
        self.manager.register_resource_monitor("monitor1", monitor1)
        self.manager.register_resource_monitor("monitor2", monitor2)
        
        usage = self.manager.get_resource_usage()
        
        self.assertIn("monitor1", usage)
        self.assertIn("monitor2", usage)
        self.assertEqual(usage["monitor1"]["queue_size"], 150)
        self.assertEqual(usage["monitor2"]["connections"], 25)
    
    @patch('psutil.virtual_memory')
    def test_cleanup_threshold_checking(self, mock_memory):
        """Test cleanup threshold checking."""
        # Mock high memory usage
        mock_memory.return_value = Mock(percent=95.0)
        
        self.manager.set_cleanup_threshold("memory_percent", 90.0)
        
        # Should trigger cleanup due to high memory
        self.assertTrue(self.manager._should_cleanup())
        
        # Mock normal memory usage
        mock_memory.return_value = Mock(percent=70.0)
        
        # Should not trigger cleanup
        self.assertFalse(self.manager._should_cleanup())
    
    def test_cleanup_with_resource_monitor_thresholds(self):
        """Test cleanup based on resource monitor thresholds."""
        def queue_monitor():
            return {"size": 1500}  # High queue size
        
        self.manager.register_resource_monitor("queue", queue_monitor)
        self.manager.set_cleanup_threshold("queue_size", 1000)
        
        # Should trigger cleanup due to high queue size
        self.assertTrue(self.manager._should_cleanup())


class TestNetworkFailureScenarios(unittest.TestCase):
    """Test cases for network failure scenarios."""
    
    @patch('requests.post')
    def test_ai_provider_connection_timeout(self, mock_post):
        """Test AI provider handling of connection timeouts."""
        from backend.ai.providers.deepseek_provider import DeepSeekProvider
        
        # Mock timeout exception
        mock_post.side_effect = requests.exceptions.Timeout("Connection timed out")
        
        provider = DeepSeekProvider("test-key")
        
        with self.assertRaises(AIProviderTimeoutError):
            provider.generate_response("test prompt")
        
        # Should have attempted retries
        self.assertGreater(mock_post.call_count, 1)
    
    @patch('requests.post')
    def test_ai_provider_connection_error(self, mock_post):
        """Test AI provider handling of connection errors."""
        from backend.ai.providers.deepseek_provider import DeepSeekProvider
        
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError("Network unreachable")
        
        provider = DeepSeekProvider("test-key")
        
        with self.assertRaises(AIProviderConnectionError):
            provider.generate_response("test prompt")
        
        # Should have attempted retries
        self.assertGreater(mock_post.call_count, 1)
    
    @patch('requests.post')
    def test_ai_provider_rate_limiting(self, mock_post):
        """Test AI provider handling of rate limiting."""
        from backend.ai.providers.deepseek_provider import DeepSeekProvider
        
        # Mock rate limit response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        mock_post.return_value = mock_response
        
        provider = DeepSeekProvider("test-key")
        
        with self.assertRaises(AIProviderError):
            provider.generate_response("test prompt")
    
    @patch('requests.post')
    def test_ai_provider_server_error_recovery(self, mock_post):
        """Test AI provider recovery from server errors."""
        from backend.ai.providers.deepseek_provider import DeepSeekProvider
        
        # Mock server error followed by success
        error_response = Mock()
        error_response.status_code = 500
        error_response.text = "Internal server error"
        
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {
            "choices": [{"message": {"content": "Success after retry"}}]
        }
        
        mock_post.side_effect = [error_response, success_response]
        
        provider = DeepSeekProvider("test-key")
        result = provider.generate_response("test prompt")
        
        self.assertEqual(result, "Success after retry")
        self.assertEqual(mock_post.call_count, 2)


class TestDeviceDisconnectionHandling(unittest.TestCase):
    """Test cases for device disconnection handling."""
    
    @patch('backend.audio.recorder.sr.Microphone')
    def test_microphone_disconnection_recovery(self, mock_microphone):
        """Test microphone disconnection and recovery."""
        from backend.audio.recorder import DefaultMicRecorder
        
        # Mock initial successful creation
        mock_source = Mock()
        mock_microphone.return_value = mock_source
        
        recorder = DefaultMicRecorder()
        
        # Test recovery method
        success = recorder._recover_microphone("default_microphone", AudioDeviceError("Device lost"))
        
        # Should attempt to recreate microphone
        self.assertTrue(success)
        self.assertGreater(mock_microphone.call_count, 1)
    
    @patch('backend.audio_system.get_default_speaker')
    @patch('backend.audio.recorder.sr.Microphone')
    def test_speaker_disconnection_recovery(self, mock_microphone, mock_get_speaker):
        """Test speaker disconnection and recovery."""
        from backend.audio.recorder import DefaultSpeakerRecorder
        
        # Mock speaker info
        speaker_info = {
            "index": 1,
            "name": "Test Speaker",
            "defaultSampleRate": 44100,
            "maxInputChannels": 2
        }
        mock_get_speaker.return_value = speaker_info
        
        # Mock microphone source
        mock_source = Mock()
        mock_microphone.return_value = mock_source
        
        recorder = DefaultSpeakerRecorder()
        
        # Test recovery method
        success = recorder._recover_speaker("default_speaker", AudioDeviceError("Device lost"))
        
        # Should attempt to recreate speaker source
        self.assertTrue(success)
        self.assertGreater(mock_get_speaker.call_count, 1)
        self.assertGreater(mock_microphone.call_count, 1)
    
    def test_device_recovery_manager_integration(self):
        """Test device recovery manager integration."""
        recovery_attempts = []
        
        def mock_recovery(device_id, error):
            recovery_attempts.append((device_id, str(error)))
            return len(recovery_attempts) <= 2  # Succeed on first two attempts
        
        device_recovery_manager.register_device("test_audio_device", mock_recovery)
        
        # Simulate device failures
        error1 = AudioDeviceError("Connection lost")
        success1 = device_recovery_manager.attempt_device_recovery("test_audio_device", error1)
        self.assertTrue(success1)
        
        error2 = AudioDeviceError("Device busy")
        success2 = device_recovery_manager.attempt_device_recovery("test_audio_device", error2)
        self.assertTrue(success2)
        
        # Third attempt should fail (based on mock logic)
        error3 = AudioDeviceError("Hardware failure")
        success3 = device_recovery_manager.attempt_device_recovery("test_audio_device", error3)
        self.assertFalse(success3)
        
        self.assertEqual(len(recovery_attempts), 3)


class TestResourceLimitScenarios(unittest.TestCase):
    """Test cases for resource limit scenarios."""
    
    @patch('psutil.virtual_memory')
    def test_memory_pressure_handling(self, mock_memory):
        """Test handling of memory pressure situations."""
        # Mock high memory usage
        mock_memory.return_value = Mock(
            percent=95.0,
            available=100 * 1024 * 1024  # 100MB available
        )
        
        monitor = SystemHealthMonitor(memory_threshold=90.0)
        metrics = monitor._collect_metrics()
        status = monitor._assess_health(metrics)
        
        self.assertEqual(status, SystemHealthStatus.CRITICAL)
        self.assertEqual(metrics.memory_percent, 95.0)
        self.assertEqual(metrics.memory_available_mb, 100.0)
    
    @patch('queue.Queue.put')
    def test_queue_overflow_handling(self, mock_put):
        """Test handling of queue overflow situations."""
        from backend.audio.transcriber import AudioTranscriber
        from backend.audio.models import LocalWhisperModel
        
        # Mock queue that raises exception when full
        mock_put.side_effect = queue.Full("Queue is full")
        
        # Create transcriber with mocked components
        mock_mic_source = Mock()
        mock_mic_source.SAMPLE_RATE = 16000
        mock_mic_source.SAMPLE_WIDTH = 2
        mock_mic_source.channels = 1
        
        mock_speaker_source = Mock()
        mock_speaker_source.SAMPLE_RATE = 44100
        mock_speaker_source.SAMPLE_WIDTH = 2
        mock_speaker_source.channels = 2
        
        mock_model = Mock(spec=LocalWhisperModel)
        
        transcriber = AudioTranscriber(mock_mic_source, mock_speaker_source, mock_model)
        
        # Test queue metrics monitoring
        metrics = transcriber._get_queue_metrics()
        
        self.assertIn("transcript_entries_you", metrics)
        self.assertIn("transcript_entries_speaker", metrics)
        self.assertIn("is_running", metrics)
    
    def test_resource_cleanup_on_limits(self):
        """Test resource cleanup when limits are reached."""
        cleanup_calls = []
        
        def cleanup_handler():
            cleanup_calls.append("cleanup_performed")
        
        resource_cleanup_manager.register_cleanup_handler(cleanup_handler)
        
        # Force cleanup
        results = resource_cleanup_manager.perform_cleanup(force=True)
        
        self.assertGreater(results["handlers_executed"], 0)
        self.assertGreater(len(cleanup_calls), 0)
    
    @patch('tempfile.mkstemp')
    @patch('os.unlink')
    def test_temporary_file_cleanup(self, mock_unlink, mock_mkstemp):
        """Test cleanup of temporary files."""
        from backend.audio.transcriber import AudioTranscriber
        from backend.audio.models import LocalWhisperModel
        
        # Mock temporary file creation
        mock_mkstemp.return_value = (1, "/tmp/test_audio.wav")
        
        # Create transcriber
        mock_mic_source = Mock()
        mock_mic_source.SAMPLE_RATE = 16000
        mock_mic_source.SAMPLE_WIDTH = 2
        mock_mic_source.channels = 1
        
        mock_speaker_source = Mock()
        mock_speaker_source.SAMPLE_RATE = 44100
        mock_speaker_source.SAMPLE_WIDTH = 2
        mock_speaker_source.channels = 2
        
        mock_model = Mock(spec=LocalWhisperModel)
        
        transcriber = AudioTranscriber(mock_mic_source, mock_speaker_source, mock_model)
        
        # Test cleanup method
        transcriber._cleanup_temp_files()
        
        # Should not raise exceptions
        self.assertTrue(True)


class TestIntegrationErrorScenarios(unittest.TestCase):
    """Test cases for integration error scenarios."""
    
    def test_cascading_failure_prevention(self):
        """Test prevention of cascading failures."""
        # Create circuit breakers for different components
        audio_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        ai_breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)
        
        # Simulate audio system failure
        with self.assertRaises(AudioError):
            audio_breaker.call(lambda: exec('raise AudioError("Audio system failed")'))
        with self.assertRaises(AudioError):
            audio_breaker.call(lambda: exec('raise AudioError("Audio system failed")'))
        
        # Audio circuit should be open
        self.assertEqual(audio_breaker.state, "open")
        
        # AI system should still be functional
        result = ai_breaker.call(lambda: "AI system working")
        self.assertEqual(result, "AI system working")
        self.assertEqual(ai_breaker.state, "closed")
    
    def test_error_correlation_tracking(self):
        """Test tracking of correlated errors across components."""
        # Record errors in different components around the same time
        base_time = datetime.now()
        
        # Audio component errors
        audio_error1 = error_tracker.record_error(
            AudioDeviceError("Microphone disconnected"), 
            "audio_recorder"
        )
        audio_error1.timestamp = base_time
        
        # AI component error (potentially related)
        ai_error = error_tracker.record_error(
            AIProviderConnectionError("Network timeout"),
            "ai_provider"
        )
        ai_error.timestamp = base_time + timedelta(seconds=5)
        
        # Get statistics for recent time window
        stats = error_tracker.get_error_statistics(time_window=timedelta(minutes=1))
        
        # Should capture both errors
        self.assertEqual(stats["total_errors"], 2)
        self.assertIn("audio_recorder", stats["component_stats"])
        self.assertIn("ai_provider", stats["component_stats"])
    
    def test_system_degradation_levels(self):
        """Test different levels of system degradation."""
        # Test graceful degradation chain
        def primary_transcription():
            raise AudioTranscriptionError("Primary transcription failed")
        
        def fallback_transcription():
            return "fallback transcription result"
        
        def emergency_fallback():
            return "emergency fallback - basic functionality"
        
        degradation = GracefulDegradation("transcription_system")
        degradation.add_fallback(fallback_transcription, "Fallback transcription")
        degradation.add_fallback(emergency_fallback, "Emergency fallback")
        
        result = degradation.execute_with_fallbacks(primary_transcription)
        self.assertEqual(result, "fallback transcription result")


if __name__ == '__main__':
    unittest.main()