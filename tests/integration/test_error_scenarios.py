"""
Integration tests for error handling scenarios.

Tests end-to-end error handling, recovery mechanisms, and system resilience
under various failure conditions.
"""

import unittest
import time
import threading
import queue
import tempfile
import shutil
import os
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta

from src.utils.error_recovery import (
    initialize_error_recovery, shutdown_error_recovery,
    system_health_monitor, error_tracker, device_recovery_manager,
    resource_cleanup_manager
)
from src.utils.exceptions import (
    AudioDeviceError, AIProviderConnectionError, AudioTranscriptionError
)


class TestEndToEndErrorRecovery(unittest.TestCase):
    """Test end-to-end error recovery scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Initialize error recovery system
        initialize_error_recovery()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Shutdown error recovery system
        shutdown_error_recovery()
    
    def test_audio_device_failure_and_recovery(self):
        """Test complete audio device failure and recovery cycle."""
        recovery_attempts = []
        
        def mock_audio_recovery(device_id, error):
            recovery_attempts.append((device_id, str(error), datetime.now()))
            # Simulate recovery taking some time
            time.sleep(0.1)
            return len(recovery_attempts) <= 2  # First two attempts succeed
        
        # Register audio device
        device_recovery_manager.register_device(
            "integration_test_mic",
            mock_audio_recovery,
            {"type": "microphone", "status": "active"}
        )
        
        # Simulate device failure
        error = AudioDeviceError("Device suddenly disconnected")
        
        # Record error and attempt recovery
        error_event = error_tracker.record_error(error, "audio_system")
        
        start_time = time.time()
        success = device_recovery_manager.attempt_device_recovery("integration_test_mic", error)
        recovery_duration = time.time() - start_time
        
        # Record recovery result
        error_tracker.record_recovery(error_event, success, recovery_duration)
        
        # Verify recovery was attempted and successful
        self.assertTrue(success)
        self.assertEqual(len(recovery_attempts), 1)
        self.assertTrue(error_event.recovery_attempted)
        self.assertTrue(error_event.recovery_successful)
        self.assertGreater(error_event.recovery_duration, 0)
    
    def test_ai_provider_failure_cascade_prevention(self):
        """Test prevention of AI provider failure cascades."""
        from src.ai.providers.deepseek_provider import DeepSeekProvider
        
        # Create provider with circuit breaker
        provider = DeepSeekProvider("test-key")
        
        # Mock network failures
        with patch('requests.post') as mock_post:
            # Simulate repeated failures
            mock_post.side_effect = AIProviderConnectionError("Network unreachable")
            
            # Multiple failure attempts should trigger circuit breaker
            for i in range(6):  # More than failure threshold
                try:
                    provider.generate_response("test prompt")
                except Exception:
                    pass  # Expected to fail
            
            # Circuit breaker should prevent further attempts
            circuit_breaker = provider.generate_response.circuit_breaker
            self.assertEqual(circuit_breaker.state, "open")
    
    def test_system_health_monitoring_integration(self):
        """Test system health monitoring with real resource changes."""
        health_changes = []
        
        def health_callback(status, metrics):
            health_changes.append((status, metrics.cpu_percent, datetime.now()))
        
        system_health_monitor.add_health_callback(health_callback)
        
        # Let monitor run briefly
        time.sleep(0.5)
        
        # Should have collected some health data
        current_metrics = system_health_monitor.get_current_metrics()
        self.assertIsNotNone(current_metrics)
        self.assertGreater(current_metrics.cpu_percent, 0)
        self.assertGreater(current_metrics.memory_percent, 0)
    
    def test_resource_cleanup_under_pressure(self):
        """Test resource cleanup under memory pressure."""
        cleanup_performed = []
        
        def test_cleanup_handler():
            cleanup_performed.append(datetime.now())
            # Simulate cleanup work
            time.sleep(0.05)
        
        resource_cleanup_manager.register_cleanup_handler(test_cleanup_handler)
        
        # Force cleanup
        results = resource_cleanup_manager.perform_cleanup(force=True)
        
        self.assertGreater(results["handlers_executed"], 0)
        self.assertEqual(len(results["errors"]), 0)
        self.assertGreater(len(cleanup_performed), 0)
    
    def test_error_tracking_and_analysis(self):
        """Test comprehensive error tracking and analysis."""
        # Simulate various error scenarios
        errors = [
            (AudioDeviceError("Microphone not found"), "audio_recorder", "critical"),
            (AIProviderConnectionError("API timeout"), "ai_provider", "error"),
            (AudioTranscriptionError("Model loading failed"), "transcriber", "error"),
            (AudioDeviceError("Speaker disconnected"), "audio_recorder", "warning"),
        ]
        
        events = []
        for error, component, severity in errors:
            event = error_tracker.record_error(error, component, severity)
            events.append(event)
        
        # Simulate some recovery attempts
        error_tracker.record_recovery(events[0], successful=True, duration=2.5)
        error_tracker.record_recovery(events[1], successful=False, duration=5.0)
        error_tracker.record_recovery(events[2], successful=True, duration=1.2)
        
        # Analyze error statistics
        stats = error_tracker.get_error_statistics()
        
        self.assertEqual(stats["total_errors"], 4)
        self.assertEqual(stats["recovery_stats"]["attempted"], 3)
        self.assertEqual(stats["recovery_stats"]["successful"], 2)
        self.assertAlmostEqual(stats["recovery_rate"], 2/3, places=2)
        
        # Check component-specific stats
        self.assertEqual(stats["component_stats"]["audio_recorder"]["count"], 2)
        self.assertEqual(stats["component_stats"]["audio_recorder"]["recoveries"], 1)
        self.assertEqual(stats["component_stats"]["ai_provider"]["count"], 1)
        self.assertEqual(stats["component_stats"]["ai_provider"]["recoveries"], 0)
    
    def test_concurrent_error_handling(self):
        """Test error handling under concurrent load."""
        errors_recorded = []
        recovery_attempts = []
        
        def concurrent_error_generator(thread_id):
            """Generate errors from multiple threads."""
            for i in range(5):
                error = AudioDeviceError(f"Thread {thread_id} error {i}")
                event = error_tracker.record_error(error, f"component_{thread_id}")
                errors_recorded.append(event)
                time.sleep(0.01)  # Small delay
        
        def concurrent_recovery_handler(device_id, error):
            """Handle recovery from multiple threads."""
            recovery_attempts.append((device_id, threading.current_thread().name))
            time.sleep(0.05)  # Simulate recovery work
            return True
        
        # Register multiple devices
        for i in range(3):
            device_recovery_manager.register_device(
                f"concurrent_device_{i}",
                concurrent_recovery_handler
            )
        
        # Start multiple error-generating threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_error_generator, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for error generation to complete
        for thread in threads:
            thread.join()
        
        # Attempt concurrent recoveries
        recovery_threads = []
        for i in range(3):
            error = AudioDeviceError(f"Concurrent recovery test {i}")
            thread = threading.Thread(
                target=device_recovery_manager.attempt_device_recovery,
                args=(f"concurrent_device_{i}", error)
            )
            recovery_threads.append(thread)
            thread.start()
        
        # Wait for recoveries to complete
        for thread in recovery_threads:
            thread.join()
        
        # Verify concurrent operations completed successfully
        self.assertEqual(len(errors_recorded), 15)  # 3 threads * 5 errors each
        self.assertEqual(len(recovery_attempts), 3)  # 3 recovery attempts
        
        # Check error statistics
        stats = error_tracker.get_error_statistics()
        self.assertGreaterEqual(stats["total_errors"], 15)


class TestFailureScenarioSimulation(unittest.TestCase):
    """Test realistic failure scenario simulations."""
    
    def setUp(self):
        """Set up test fixtures."""
        initialize_error_recovery()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutdown_error_recovery()
    
    def test_network_partition_simulation(self):
        """Simulate network partition affecting AI providers."""
        from src.ai.providers.deepseek_provider import DeepSeekProvider
        
        provider = DeepSeekProvider("test-key")
        
        # Simulate network partition - all requests fail
        with patch('requests.post') as mock_post:
            mock_post.side_effect = AIProviderConnectionError("Network partition")
            
            # Multiple requests should fail and trigger circuit breaker
            failures = 0
            for i in range(10):
                try:
                    provider.generate_response(f"Request {i}")
                except Exception:
                    failures += 1
            
            # Should have failed multiple times but stopped due to circuit breaker
            self.assertGreater(failures, 5)  # Some failures
            self.assertLess(failures, 10)    # But not all attempts due to circuit breaker
    
    def test_memory_exhaustion_simulation(self):
        """Simulate memory exhaustion scenario."""
        # Mock high memory usage
        with patch('psutil.virtual_memory') as mock_memory:
            mock_memory.return_value = Mock(
                percent=98.0,  # Very high memory usage
                available=50 * 1024 * 1024  # Only 50MB available
            )
            
            # Check system health assessment
            metrics = system_health_monitor._collect_metrics()
            status = system_health_monitor._assess_health(metrics)
            
            from src.utils.error_recovery import SystemHealthStatus
            self.assertEqual(status, SystemHealthStatus.CRITICAL)
            
            # Cleanup should be triggered
            should_cleanup = resource_cleanup_manager._should_cleanup()
            self.assertTrue(should_cleanup)
    
    def test_device_hot_unplug_simulation(self):
        """Simulate hot unplugging of audio devices."""
        device_states = []
        
        def device_state_tracker(device_id, error):
            device_states.append(("recovery_attempt", device_id, str(error)))
            # Simulate device not immediately available
            if len(device_states) < 3:
                raise AudioDeviceError("Device still not available")
            return True  # Eventually succeeds
        
        device_recovery_manager.register_device(
            "hot_unplug_device",
            device_state_tracker,
            {"status": "connected"}
        )
        
        # Simulate hot unplug
        unplug_error = AudioDeviceError("Device hot unplugged")
        
        # First recovery attempt should fail
        success1 = device_recovery_manager.attempt_device_recovery("hot_unplug_device", unplug_error)
        self.assertFalse(success1)
        
        # Second attempt should also fail
        success2 = device_recovery_manager.attempt_device_recovery("hot_unplug_device", unplug_error)
        self.assertFalse(success2)
        
        # Third attempt should succeed
        success3 = device_recovery_manager.attempt_device_recovery("hot_unplug_device", unplug_error)
        self.assertTrue(success3)
        
        self.assertEqual(len(device_states), 3)
    
    def test_cascading_failure_prevention(self):
        """Test prevention of cascading failures across components."""
        # Create multiple circuit breakers for different components
        component_states = {
            "audio": {"failures": 0, "circuit_open": False},
            "transcription": {"failures": 0, "circuit_open": False},
            "ai": {"failures": 0, "circuit_open": False}
        }
        
        def simulate_component_failure(component_name):
            """Simulate failure in a specific component."""
            component_states[component_name]["failures"] += 1
            
            # Open circuit after 3 failures
            if component_states[component_name]["failures"] >= 3:
                component_states[component_name]["circuit_open"] = True
                raise Exception(f"{component_name} circuit breaker open")
            
            raise Exception(f"{component_name} component failure")
        
        # Simulate failures in audio component
        for i in range(5):
            try:
                simulate_component_failure("audio")
            except Exception:
                pass
        
        # Audio component should have circuit open
        self.assertTrue(component_states["audio"]["circuit_open"])
        
        # Other components should still be functional
        self.assertFalse(component_states["transcription"]["circuit_open"])
        self.assertFalse(component_states["ai"]["circuit_open"])
        
        # Transcription component should still work
        try:
            simulate_component_failure("transcription")
        except Exception as e:
            self.assertNotIn("circuit breaker open", str(e))
    
    def test_resource_leak_detection(self):
        """Test detection and cleanup of resource leaks."""
        # Simulate resource leak scenario
        leaked_resources = []
        
        def leaky_operation():
            # Simulate creating resources that might leak
            resource = {"id": len(leaked_resources), "created": datetime.now()}
            leaked_resources.append(resource)
            
            # Simulate occasional cleanup failure
            if len(leaked_resources) % 3 == 0:
                raise RuntimeError("Cleanup failed")
        
        def cleanup_leaked_resources():
            # Clean up old resources
            cutoff_time = datetime.now() - timedelta(seconds=1)
            initial_count = len(leaked_resources)
            
            leaked_resources[:] = [
                r for r in leaked_resources 
                if r["created"] > cutoff_time
            ]
            
            cleaned_count = initial_count - len(leaked_resources)
            return cleaned_count
        
        resource_cleanup_manager.register_cleanup_handler(cleanup_leaked_resources)
        
        # Simulate operations that create leaks
        for i in range(10):
            try:
                leaky_operation()
            except RuntimeError:
                pass  # Expected cleanup failures
            
            time.sleep(0.01)  # Small delay
        
        # Should have accumulated some leaked resources
        self.assertGreater(len(leaked_resources), 0)
        
        # Force cleanup
        results = resource_cleanup_manager.perform_cleanup(force=True)
        
        # Should have cleaned up some resources
        self.assertGreater(results["handlers_executed"], 0)


class TestSystemResilienceUnderLoad(unittest.TestCase):
    """Test system resilience under various load conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        initialize_error_recovery()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutdown_error_recovery()
    
    def test_high_error_rate_handling(self):
        """Test system behavior under high error rates."""
        # Generate high volume of errors quickly
        error_count = 0
        start_time = time.time()
        
        for i in range(100):
            error = AudioDeviceError(f"High rate error {i}")
            error_tracker.record_error(error, "stress_test_component")
            error_count += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Verify all errors were recorded
        stats = error_tracker.get_error_statistics()
        self.assertGreaterEqual(stats["total_errors"], 100)
        
        # System should handle high error rate without crashing
        self.assertLess(duration, 5.0)  # Should complete within reasonable time
    
    def test_concurrent_recovery_operations(self):
        """Test concurrent recovery operations."""
        recovery_results = []
        recovery_lock = threading.Lock()
        
        def concurrent_recovery(device_id, error):
            # Simulate recovery work with some delay
            time.sleep(0.1)
            
            with recovery_lock:
                recovery_results.append({
                    "device_id": device_id,
                    "thread": threading.current_thread().name,
                    "timestamp": datetime.now()
                })
            
            return True
        
        # Register multiple devices
        device_count = 5
        for i in range(device_count):
            device_recovery_manager.register_device(
                f"concurrent_device_{i}",
                concurrent_recovery
            )
        
        # Start concurrent recovery operations
        threads = []
        for i in range(device_count):
            error = AudioDeviceError(f"Concurrent error {i}")
            thread = threading.Thread(
                target=device_recovery_manager.attempt_device_recovery,
                args=(f"concurrent_device_{i}", error)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all recoveries to complete
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout
        
        # Verify all recoveries completed
        self.assertEqual(len(recovery_results), device_count)
        
        # Verify recoveries happened concurrently (overlapping timestamps)
        timestamps = [r["timestamp"] for r in recovery_results]
        time_span = max(timestamps) - min(timestamps)
        self.assertLess(time_span.total_seconds(), 0.5)  # Should overlap significantly
    
    def test_system_stability_over_time(self):
        """Test system stability over extended operation."""
        # Run system operations for a period of time
        start_time = time.time()
        operation_count = 0
        error_count = 0
        
        # Simulate continuous operation
        while time.time() - start_time < 2.0:  # Run for 2 seconds
            try:
                # Simulate various operations
                if operation_count % 10 == 0:
                    # Occasional error
                    error = AudioDeviceError(f"Periodic error {error_count}")
                    error_tracker.record_error(error, "stability_test")
                    error_count += 1
                
                # Simulate normal operation
                operation_count += 1
                time.sleep(0.01)  # Small delay
                
            except Exception as e:
                # System should not crash
                self.fail(f"System crashed during stability test: {e}")
        
        # Verify system remained stable
        self.assertGreater(operation_count, 100)  # Should have performed many operations
        self.assertGreater(error_count, 5)       # Should have encountered some errors
        
        # System should still be responsive
        current_metrics = system_health_monitor.get_current_metrics()
        self.assertIsNotNone(current_metrics)
    
    def test_graceful_degradation_under_load(self):
        """Test graceful degradation under system load."""
        from src.utils.retry import GracefulDegradation
        
        # Create degradation chain for critical operation
        degradation = GracefulDegradation("load_test_operation")
        
        # Primary operation that fails under load
        def primary_operation():
            raise RuntimeError("Primary operation overloaded")
        
        # Fallback operations with decreasing quality
        def fallback_operation():
            return "fallback_result"
        
        def emergency_operation():
            return "emergency_result"
        
        degradation.add_fallback(fallback_operation, "Standard fallback")
        degradation.add_fallback(emergency_operation, "Emergency fallback")
        
        # Test degradation under load
        results = []
        for i in range(50):
            try:
                result = degradation.execute_with_fallbacks(primary_operation)
                results.append(result)
            except Exception as e:
                self.fail(f"Graceful degradation failed: {e}")
        
        # Should have fallen back to secondary operations
        self.assertEqual(len(results), 50)
        self.assertTrue(all(r in ["fallback_result", "emergency_result"] for r in results))


if __name__ == '__main__':
    unittest.main()