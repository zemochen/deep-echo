"""
Performance tests for resource usage.

Tests memory usage, CPU usage, and long-term stability to ensure
the system operates efficiently and doesn't leak resources.

Requirements: 11.1-11.6
"""

import pytest
import time
import gc
import psutil
import os
import json
import threading
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from backend.ipc.message_handler import MessageHandler
from backend.ipc.event_emitter import EventEmitter, get_event_emitter


def get_process_memory_mb():
    """Get current process memory usage in MB."""
    try:
        process = psutil.Process()
        return process.memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


def get_process_cpu_percent(interval=0.1):
    """Get current process CPU usage percentage."""
    try:
        process = psutil.Process()
        return process.cpu_percent(interval=interval)
    except Exception:
        return 0.0


class TestMemoryUsage:
    """Test memory usage and leak detection."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def test_baseline_memory_usage(self, message_handler):
        """Test baseline memory usage of message handler."""
        # Force garbage collection
        gc.collect()
        time.sleep(0.1)
        
        initial_memory = get_process_memory_mb()
        
        # Execute some commands
        for i in range(10):
            command = {
                "command": "ping",
                "params": {},
                "id": f"baseline_{i}"
            }
            response_str = message_handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            assert response["status"] == "success"
        
        # Force garbage collection
        gc.collect()
        time.sleep(0.1)
        
        final_memory = get_process_memory_mb()
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be minimal (< 10MB for 10 commands)
        assert memory_increase < 10, \
            f"Memory increase {memory_increase:.2f}MB should be < 10MB for baseline operations"
        
        print(f"\nBaseline memory: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, increase={memory_increase:.2f}MB")
    
    def test_memory_leak_detection(self, message_handler):
        """Test for memory leaks over repeated operations."""
        gc.collect()
        time.sleep(0.1)
        
        initial_memory = get_process_memory_mb()
        memory_samples = [initial_memory]
        
        # Execute many commands
        for i in range(100):
            command = {
                "command": "ping",
                "params": {},
                "id": f"leak_test_{i}"
            }
            response_str = message_handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            assert response["status"] == "success"
            
            # Sample memory every 20 commands
            if i % 20 == 0:
                gc.collect()
                time.sleep(0.05)
                memory_samples.append(get_process_memory_mb())
        
        # Force final garbage collection
        gc.collect()
        time.sleep(0.1)
        final_memory = get_process_memory_mb()
        memory_samples.append(final_memory)
        
        # Calculate memory growth trend
        memory_growth = final_memory - initial_memory
        
        # Memory should not grow significantly (< 20MB for 100 commands)
        assert memory_growth < 20, \
            f"Memory growth {memory_growth:.2f}MB should be < 20MB for 100 commands"
        
        # Check that memory doesn't continuously increase
        # Compare first half vs second half
        mid_point = len(memory_samples) // 2
        first_half_avg = sum(memory_samples[:mid_point]) / mid_point
        second_half_avg = sum(memory_samples[mid_point:]) / (len(memory_samples) - mid_point)
        
        growth_rate = (second_half_avg - first_half_avg) / first_half_avg if first_half_avg > 0 else 0
        
        # Growth rate should be reasonable (< 50%)
        assert growth_rate < 0.5, \
            f"Memory growth rate {growth_rate:.2%} should be < 50%"
        
        print(f"\nMemory leak test: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, growth={memory_growth:.2f}MB, growth_rate={growth_rate:.2%}")
    
    def test_memory_usage_with_events(self):
        """Test memory usage with event emission."""
        event_emitter = get_event_emitter()
        event_emitter.start()
        
        try:
            gc.collect()
            time.sleep(0.1)
            
            initial_memory = get_process_memory_mb()
            
            received_events = []
            
            def event_handler(event_data):
                received_events.append(event_data)
            
            event_emitter.add_listener("memory-test-event", event_handler)
            
            # Emit many events
            for i in range(200):
                event_data = {
                    "id": f"event_{i}",
                    "timestamp": time.time(),
                    "data": f"test data {i}"
                }
                event_emitter.emit("memory-test-event", event_data)
            
            # Wait for events to be processed
            time.sleep(0.5)
            
            # Force garbage collection
            gc.collect()
            time.sleep(0.1)
            
            final_memory = get_process_memory_mb()
            memory_increase = final_memory - initial_memory
            
            # Memory increase should be reasonable (< 30MB for 200 events)
            assert memory_increase < 30, \
                f"Memory increase {memory_increase:.2f}MB should be < 30MB for 200 events"
            
            # Verify events were received
            assert len(received_events) > 0, "Should have received some events"
            
            print(f"\nEvent memory test: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, increase={memory_increase:.2f}MB, events_received={len(received_events)}")
        
        finally:
            event_emitter.stop()
    
    def test_memory_cleanup_after_operations(self, message_handler):
        """Test that memory is properly cleaned up after operations."""
        gc.collect()
        time.sleep(0.1)
        
        baseline_memory = get_process_memory_mb()
        
        # Perform operations that allocate memory
        for i in range(50):
            command = {
                "command": "get_config",
                "params": {},
                "id": f"cleanup_test_{i}"
            }
            response_str = message_handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            assert response["status"] == "success"
        
        # Measure memory after operations
        after_ops_memory = get_process_memory_mb()
        
        # Force cleanup
        gc.collect()
        time.sleep(0.2)
        
        # Measure memory after cleanup
        after_cleanup_memory = get_process_memory_mb()
        
        # Memory after cleanup should be close to baseline
        memory_retained = after_cleanup_memory - baseline_memory
        
        # Retained memory should be minimal (< 15MB)
        assert memory_retained < 15, \
            f"Retained memory {memory_retained:.2f}MB should be < 15MB after cleanup"
        
        print(f"\nMemory cleanup test: baseline={baseline_memory:.2f}MB, after_ops={after_ops_memory:.2f}MB, after_cleanup={after_cleanup_memory:.2f}MB, retained={memory_retained:.2f}MB")


class TestCPUUsage:
    """Test CPU usage and efficiency."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def test_idle_cpu_usage(self, message_handler):
        """Test CPU usage during idle periods."""
        # Let system settle
        time.sleep(0.5)
        
        # Measure CPU during idle
        cpu_samples = []
        for _ in range(5):
            cpu_percent = get_process_cpu_percent(interval=0.2)
            cpu_samples.append(cpu_percent)
            time.sleep(0.1)
        
        avg_cpu = sum(cpu_samples) / len(cpu_samples)
        max_cpu = max(cpu_samples)
        
        # Idle CPU should be low (< 5% average, < 15% max)
        assert avg_cpu < 5.0, f"Average idle CPU {avg_cpu:.2f}% should be < 5%"
        assert max_cpu < 15.0, f"Maximum idle CPU {max_cpu:.2f}% should be < 15%"
        
        print(f"\nIdle CPU usage: avg={avg_cpu:.2f}%, max={max_cpu:.2f}%")
    
    def test_cpu_usage_under_load(self, message_handler):
        """Test CPU usage under command load."""
        # Execute commands continuously
        start_time = time.time()
        command_count = 0
        
        while time.time() - start_time < 2.0:
            command = {
                "command": "ping",
                "params": {},
                "id": f"load_test_{command_count}"
            }
            response_str = message_handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            assert response["status"] == "success"
            command_count += 1
        
        # Measure CPU after load
        cpu_percent = get_process_cpu_percent(interval=0.5)
        
        # CPU usage should be reasonable even under load (< 50%)
        assert cpu_percent < 50.0, f"CPU usage under load {cpu_percent:.2f}% should be < 50%"
        
        print(f"\nCPU under load: {cpu_percent:.2f}% for {command_count} commands in 2s")
    
    def test_cpu_recovery_after_load(self, message_handler):
        """Test that CPU usage returns to normal after load."""
        # Create load
        for i in range(50):
            command = {
                "command": "get_system_info",
                "params": {},
                "id": f"recovery_test_{i}"
            }
            response_str = message_handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            assert response["status"] == "success"
        
        # Measure CPU immediately after load
        cpu_after_load = get_process_cpu_percent(interval=0.2)
        
        # Wait for recovery
        time.sleep(1.0)
        
        # Measure CPU after recovery period
        cpu_after_recovery = get_process_cpu_percent(interval=0.2)
        
        # CPU should decrease after recovery period
        # After recovery should be lower than immediately after load
        assert cpu_after_recovery <= cpu_after_load + 5.0, \
            f"CPU after recovery {cpu_after_recovery:.2f}% should not be higher than after load {cpu_after_load:.2f}%"
        
        print(f"\nCPU recovery: after_load={cpu_after_load:.2f}%, after_recovery={cpu_after_recovery:.2f}%")


class TestLongTermStability:
    """Test long-term stability and resource management."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def test_sustained_operation_stability(self, message_handler):
        """Test stability over sustained operations."""
        gc.collect()
        time.sleep(0.1)
        
        initial_memory = get_process_memory_mb()
        memory_samples = []
        error_count = 0
        success_count = 0
        
        # Run for 5 seconds with continuous operations
        start_time = time.time()
        iteration = 0
        
        while time.time() - start_time < 5.0:
            command = {
                "command": "ping",
                "params": {},
                "id": f"sustained_{iteration}"
            }
            
            try:
                response_str = message_handler.handle_message(json.dumps(command))
                response = json.loads(response_str)
                
                if response["status"] == "success":
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error during sustained operation: {e}")
            
            iteration += 1
            
            # Sample memory periodically
            if iteration % 50 == 0:
                memory_samples.append(get_process_memory_mb())
            
            time.sleep(0.01)  # Small delay between operations
        
        # Final measurements
        gc.collect()
        time.sleep(0.1)
        final_memory = get_process_memory_mb()
        
        # Calculate statistics
        total_operations = success_count + error_count
        success_rate = success_count / total_operations if total_operations > 0 else 0
        memory_growth = final_memory - initial_memory
        
        # Assertions
        assert success_rate > 0.95, f"Success rate {success_rate:.2%} should be > 95%"
        assert memory_growth < 50, f"Memory growth {memory_growth:.2f}MB should be < 50MB over sustained operations"
        assert error_count < total_operations * 0.05, f"Error count {error_count} should be < 5% of total operations"
        
        print(f"\nSustained operation: operations={total_operations}, success_rate={success_rate:.2%}, memory_growth={memory_growth:.2f}MB, errors={error_count}")
    
    def test_concurrent_operations_stability(self, message_handler):
        """Test stability under concurrent operations."""
        results = []
        errors = []
        lock = threading.Lock()
        
        def execute_commands(thread_id, num_commands):
            for i in range(num_commands):
                try:
                    command = {
                        "command": "ping",
                        "params": {},
                        "id": f"concurrent_{thread_id}_{i}"
                    }
                    response_str = message_handler.handle_message(json.dumps(command))
                    response = json.loads(response_str)
                    
                    with lock:
                        results.append(response)
                except Exception as e:
                    with lock:
                        errors.append(str(e))
        
        # Create multiple threads
        threads = []
        num_threads = 5
        commands_per_thread = 20
        
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=execute_commands, args=(i, commands_per_thread))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=10.0)
        
        execution_time = time.time() - start_time
        
        # Calculate statistics
        total_expected = num_threads * commands_per_thread
        success_count = sum(1 for r in results if r.get("status") == "success")
        success_rate = success_count / total_expected if total_expected > 0 else 0
        
        # Assertions
        assert len(results) >= total_expected * 0.9, \
            f"Should complete at least 90% of operations, got {len(results)}/{total_expected}"
        assert success_rate > 0.9, \
            f"Success rate {success_rate:.2%} should be > 90% under concurrent load"
        assert len(errors) < total_expected * 0.1, \
            f"Error count {len(errors)} should be < 10% of total operations"
        
        print(f"\nConcurrent stability: threads={num_threads}, operations={len(results)}/{total_expected}, success_rate={success_rate:.2%}, time={execution_time:.2f}s, errors={len(errors)}")
    
    def test_event_system_stability(self):
        """Test event system stability over time."""
        event_emitter = get_event_emitter()
        event_emitter.start()
        
        try:
            received_events = []
            errors = []
            
            def event_handler(event_data):
                try:
                    received_events.append(event_data)
                except Exception as e:
                    errors.append(str(e))
            
            event_emitter.add_listener("stability-test", event_handler)
            
            # Emit events continuously for 3 seconds
            start_time = time.time()
            emitted_count = 0
            
            while time.time() - start_time < 3.0:
                event_data = {
                    "id": f"stability_event_{emitted_count}",
                    "timestamp": time.time(),
                    "data": "test"
                }
                event_emitter.emit("stability-test", event_data)
                emitted_count += 1
                time.sleep(0.01)
            
            # Wait for events to be processed
            time.sleep(0.5)
            
            # Calculate statistics
            delivery_rate = len(received_events) / emitted_count if emitted_count > 0 else 0
            
            # Assertions
            assert delivery_rate > 0.8, \
                f"Event delivery rate {delivery_rate:.2%} should be > 80%"
            assert len(errors) == 0, \
                f"Should have no errors in event handling, got {len(errors)}"
            
            print(f"\nEvent system stability: emitted={emitted_count}, received={len(received_events)}, delivery_rate={delivery_rate:.2%}, errors={len(errors)}")
        
        finally:
            event_emitter.stop()
    
    def test_resource_cleanup_on_shutdown(self, message_handler):
        """Test that resources are properly cleaned up on shutdown."""
        gc.collect()
        time.sleep(0.1)
        
        initial_memory = get_process_memory_mb()
        
        # Perform operations
        for i in range(30):
            command = {
                "command": "get_config",
                "params": {},
                "id": f"shutdown_test_{i}"
            }
            response_str = message_handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            assert response["status"] == "success"
        
        # Cleanup
        message_handler.cleanup()
        
        # Force garbage collection
        gc.collect()
        time.sleep(0.2)
        
        final_memory = get_process_memory_mb()
        memory_retained = final_memory - initial_memory
        
        # Memory should be mostly cleaned up (< 20MB retained)
        assert memory_retained < 20, \
            f"Retained memory {memory_retained:.2f}MB should be < 20MB after cleanup"
        
        print(f"\nShutdown cleanup: initial={initial_memory:.2f}MB, final={final_memory:.2f}MB, retained={memory_retained:.2f}MB")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
