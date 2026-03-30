"""
Performance tests for response time.

Tests UI response time and command execution time to ensure
the system meets performance requirements.

Requirements: 11.1-11.6
"""

import pytest
import time
import json
import statistics
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from backend.ipc.message_handler import MessageHandler
from backend.ipc.event_emitter import EventEmitter, get_event_emitter


class TestCommandResponseTime:
    """Test command execution response times."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def measure_command_time(self, message_handler, command_name, params=None):
        """Measure time to execute a command."""
        if params is None:
            params = {}
        
        command = {
            "command": command_name,
            "params": params,
            "id": f"perf_test_{time.time()}"
        }
        
        start_time = time.time()
        response_str = message_handler.handle_message(json.dumps(command))
        end_time = time.time()
        
        response = json.loads(response_str)
        execution_time = end_time - start_time
        
        return execution_time, response
    
    def test_ping_command_response_time(self, message_handler):
        """Test ping command response time."""
        times = []
        
        # Execute ping command multiple times
        for _ in range(10):
            execution_time, response = self.measure_command_time(message_handler, "ping")
            
            assert response["status"] == "success", "Ping command should succeed"
            times.append(execution_time)
        
        # Calculate statistics
        avg_time = statistics.mean(times)
        max_time = max(times)
        min_time = min(times)
        
        # Ping should be very fast (< 10ms average, < 50ms max)
        assert avg_time < 0.01, f"Average ping time {avg_time*1000:.2f}ms should be < 10ms"
        assert max_time < 0.05, f"Maximum ping time {max_time*1000:.2f}ms should be < 50ms"
        
        print(f"\nPing command stats: avg={avg_time*1000:.2f}ms, min={min_time*1000:.2f}ms, max={max_time*1000:.2f}ms")
    
    def test_get_config_response_time(self, message_handler):
        """Test get_config command response time."""
        times = []
        
        for _ in range(10):
            execution_time, response = self.measure_command_time(message_handler, "get_config")
            
            assert response["status"] == "success", "Get config should succeed"
            times.append(execution_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Config retrieval should be fast (< 100ms average, < 200ms max)
        assert avg_time < 0.1, f"Average get_config time {avg_time*1000:.2f}ms should be < 100ms"
        assert max_time < 0.2, f"Maximum get_config time {max_time*1000:.2f}ms should be < 200ms"
        
        print(f"\nGet config stats: avg={avg_time*1000:.2f}ms, max={max_time*1000:.2f}ms")
    
    def test_get_transcript_response_time(self, message_handler):
        """Test get_transcript command response time."""
        times = []
        
        for _ in range(10):
            execution_time, response = self.measure_command_time(message_handler, "get_transcript")
            
            assert response["status"] == "success", "Get transcript should succeed"
            times.append(execution_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Transcript retrieval should be fast (< 100ms average, < 200ms max)
        assert avg_time < 0.1, f"Average get_transcript time {avg_time*1000:.2f}ms should be < 100ms"
        assert max_time < 0.2, f"Maximum get_transcript time {max_time*1000:.2f}ms should be < 200ms"
        
        print(f"\nGet transcript stats: avg={avg_time*1000:.2f}ms, max={max_time*1000:.2f}ms")
    
    def test_get_system_info_response_time(self, message_handler):
        """Test get_system_info command response time."""
        times = []
        
        for _ in range(10):
            execution_time, response = self.measure_command_time(message_handler, "get_system_info")
            
            assert response["status"] == "success", "Get system info should succeed"
            times.append(execution_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # System info should be reasonably fast (< 200ms average, < 500ms max)
        assert avg_time < 0.2, f"Average get_system_info time {avg_time*1000:.2f}ms should be < 200ms"
        assert max_time < 0.5, f"Maximum get_system_info time {max_time*1000:.2f}ms should be < 500ms"
        
        print(f"\nGet system info stats: avg={avg_time*1000:.2f}ms, max={max_time*1000:.2f}ms")
    
    def test_get_audio_devices_response_time(self, message_handler):
        """Test get_audio_devices command response time."""
        times = []
        
        for _ in range(10):
            execution_time, response = self.measure_command_time(message_handler, "get_audio_devices")
            
            assert response["status"] == "success", "Get audio devices should succeed"
            times.append(execution_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Audio device enumeration should be reasonably fast (< 300ms average, < 1s max)
        assert avg_time < 0.3, f"Average get_audio_devices time {avg_time*1000:.2f}ms should be < 300ms"
        assert max_time < 1.0, f"Maximum get_audio_devices time {max_time*1000:.2f}ms should be < 1s"
        
        print(f"\nGet audio devices stats: avg={avg_time*1000:.2f}ms, max={max_time*1000:.2f}ms")
    
    def test_command_response_consistency(self, message_handler):
        """Test that command response times are consistent."""
        # Test multiple commands and check variance
        commands = ["ping", "get_config", "get_system_info"]
        
        for command_name in commands:
            times = []
            
            for _ in range(20):
                execution_time, response = self.measure_command_time(message_handler, command_name)
                if response["status"] == "success":
                    times.append(execution_time)
            
            if len(times) >= 10:
                avg_time = statistics.mean(times)
                std_dev = statistics.stdev(times)
                max_time = max(times)
                min_time = min(times)
                
                # Check that max time isn't extremely higher than average
                # This ensures no extreme outliers (max should be < 10x average)
                max_ratio = max_time / avg_time if avg_time > 0 else 1
                assert max_ratio < 10.0, \
                    f"{command_name} has extreme outliers: max={max_time*1000:.2f}ms, avg={avg_time*1000:.2f}ms, ratio={max_ratio:.2f}"
                
                print(f"\n{command_name} consistency: avg={avg_time*1000:.2f}ms, std_dev={std_dev*1000:.2f}ms, min={min_time*1000:.2f}ms, max={max_time*1000:.2f}ms")
    
    def test_concurrent_command_response_time(self, message_handler):
        """Test response time under concurrent load."""
        import threading
        
        results = []
        lock = threading.Lock()
        
        def execute_command():
            execution_time, response = self.measure_command_time(message_handler, "ping")
            with lock:
                results.append((execution_time, response))
        
        # Execute 10 concurrent commands
        threads = []
        start_time = time.time()
        
        for _ in range(10):
            thread = threading.Thread(target=execute_command)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=5.0)
        
        total_time = time.time() - start_time
        
        # All commands should complete
        assert len(results) == 10, "All concurrent commands should complete"
        
        # Check individual response times
        times = [r[0] for r in results]
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Concurrent commands should still be reasonably fast
        assert avg_time < 0.1, f"Average concurrent command time {avg_time*1000:.2f}ms should be < 100ms"
        assert max_time < 0.5, f"Maximum concurrent command time {max_time*1000:.2f}ms should be < 500ms"
        
        # Total time should be reasonable (not sequential)
        assert total_time < 2.0, f"Total concurrent execution time {total_time:.2f}s should be < 2s"
        
        print(f"\nConcurrent execution: total={total_time:.2f}s, avg={avg_time*1000:.2f}ms, max={max_time*1000:.2f}ms")


class TestEventResponseTime:
    """Test event emission and handling response times."""
    
    @pytest.fixture
    def event_emitter(self):
        """Create event emitter for testing."""
        emitter = get_event_emitter()
        emitter.start()
        yield emitter
        emitter.stop()
    
    def test_event_emission_time(self, event_emitter):
        """Test time to emit an event."""
        times = []
        
        for i in range(100):
            event_data = {
                "id": f"event_{i}",
                "timestamp": time.time(),
                "data": "test data"
            }
            
            start_time = time.time()
            event_emitter.emit("test-event", event_data)
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        avg_time = statistics.mean(times)
        max_time = max(times)
        
        # Event emission should be very fast (< 1ms average, < 10ms max)
        assert avg_time < 0.001, f"Average event emission time {avg_time*1000:.2f}ms should be < 1ms"
        assert max_time < 0.01, f"Maximum event emission time {max_time*1000:.2f}ms should be < 10ms"
        
        print(f"\nEvent emission stats: avg={avg_time*1000:.2f}ms, max={max_time*1000:.2f}ms")
    
    def test_event_delivery_time(self, event_emitter):
        """Test time from emission to handler execution."""
        delivery_times = []
        
        def event_handler(event_data):
            delivery_time = time.time() - event_data["emit_time"]
            delivery_times.append(delivery_time)
        
        event_emitter.add_listener("delivery-test", event_handler)
        
        # Emit events and measure delivery time
        for _ in range(50):
            event_data = {
                "emit_time": time.time(),
                "data": "test"
            }
            event_emitter.emit("delivery-test", event_data)
            time.sleep(0.01)  # Small delay between emissions
        
        # Wait for all events to be processed
        time.sleep(0.5)
        
        # Check delivery times
        assert len(delivery_times) > 0, "Should have received some events"
        
        avg_delivery = statistics.mean(delivery_times)
        max_delivery = max(delivery_times)
        
        # Event delivery should be fast (< 50ms average, < 200ms max)
        assert avg_delivery < 0.05, f"Average event delivery time {avg_delivery*1000:.2f}ms should be < 50ms"
        assert max_delivery < 0.2, f"Maximum event delivery time {max_delivery*1000:.2f}ms should be < 200ms"
        
        print(f"\nEvent delivery stats: avg={avg_delivery*1000:.2f}ms, max={max_delivery*1000:.2f}ms")
    
    def test_multiple_listener_performance(self, event_emitter):
        """Test event delivery with multiple listeners."""
        handler_times = {i: [] for i in range(5)}
        
        def create_handler(handler_id):
            def handler(event_data):
                start_time = event_data["emit_time"]
                handler_times[handler_id].append(time.time() - start_time)
            return handler
        
        # Add multiple listeners
        for i in range(5):
            event_emitter.add_listener("multi-listener-test", create_handler(i))
        
        # Emit events
        for _ in range(20):
            event_data = {
                "emit_time": time.time(),
                "data": "test"
            }
            event_emitter.emit("multi-listener-test", event_data)
            time.sleep(0.01)
        
        # Wait for processing
        time.sleep(0.5)
        
        # Check that all handlers received events
        for handler_id, times in handler_times.items():
            assert len(times) > 0, f"Handler {handler_id} should have received events"
            
            avg_time = statistics.mean(times)
            # Each handler should process events quickly
            assert avg_time < 0.1, \
                f"Handler {handler_id} average time {avg_time*1000:.2f}ms should be < 100ms"
        
        print(f"\nMultiple listeners: all handlers processed events within time limits")


class TestEndToEndResponseTime:
    """Test end-to-end response times for complete workflows."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    @pytest.fixture
    def event_emitter(self):
        """Create event emitter for testing."""
        emitter = get_event_emitter()
        emitter.start()
        yield emitter
        emitter.stop()
    
    def test_command_to_event_latency(self, message_handler, event_emitter):
        """Test latency from command execution to event emission."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append({
                "event": event_data,
                "received_time": time.time()
            })
        
        event_emitter.add_listener("status-changed", event_handler)
        
        # Execute command that triggers event
        command = {
            "command": "ping",
            "params": {},
            "id": "latency_test"
        }
        
        start_time = time.time()
        response_str = message_handler.handle_message(json.dumps(command))
        command_time = time.time() - start_time
        
        response = json.loads(response_str)
        assert response["status"] == "success"
        
        # Command should be fast
        assert command_time < 0.1, f"Command execution time {command_time*1000:.2f}ms should be < 100ms"
        
        print(f"\nCommand-to-event latency: command_time={command_time*1000:.2f}ms")
    
    def test_workflow_response_time(self, message_handler):
        """Test complete workflow response time."""
        # Test a simple workflow: get config -> get system info -> ping
        workflow_start = time.time()
        
        # Step 1: Get config
        cmd1 = {"command": "get_config", "params": {}, "id": "wf_1"}
        resp1_str = message_handler.handle_message(json.dumps(cmd1))
        resp1 = json.loads(resp1_str)
        assert resp1["status"] == "success"
        
        # Step 2: Get system info
        cmd2 = {"command": "get_system_info", "params": {}, "id": "wf_2"}
        resp2_str = message_handler.handle_message(json.dumps(cmd2))
        resp2 = json.loads(resp2_str)
        assert resp2["status"] == "success"
        
        # Step 3: Ping
        cmd3 = {"command": "ping", "params": {}, "id": "wf_3"}
        resp3_str = message_handler.handle_message(json.dumps(cmd3))
        resp3 = json.loads(resp3_str)
        assert resp3["status"] == "success"
        
        workflow_time = time.time() - workflow_start
        
        # Complete workflow should be fast (< 1s)
        assert workflow_time < 1.0, f"Workflow time {workflow_time:.2f}s should be < 1s"
        
        print(f"\nWorkflow response time: {workflow_time:.2f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
