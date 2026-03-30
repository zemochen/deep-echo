"""
Cross-Platform Tests for Frontend-Backend Separation.

Tests platform-specific functionality and consistent behavior across
Windows and macOS for the Tauri-based architecture.

Requirements: 10.1-10.6
"""

import pytest
import platform
import json
import sys
from pathlib import Path
from unittest.mock import patch, Mock

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from backend.ipc.message_handler import MessageHandler
from backend.ipc.event_emitter import EventEmitter
from backend.ipc.ipc_server import IPCServer


class TestPlatformDetection:
    """Test platform detection and configuration."""
    
    def test_current_platform_detection(self):
        """Test detection of current platform."""
        current_platform = platform.system()
        
        # Should detect one of the supported platforms
        assert current_platform in ["Windows", "Darwin", "Linux"]
        
    @patch('platform.system')
    def test_windows_platform_behavior(self, mock_platform):
        """Test Windows platform behavior."""
        mock_platform.return_value = "Windows"
        
        # Verify platform is detected as Windows
        assert platform.system() == "Windows"
        
        # Message handler should work on Windows
        handler = MessageHandler()
        assert handler is not None
        
    @patch('platform.system')
    def test_macos_platform_behavior(self, mock_platform):
        """Test macOS platform behavior."""
        mock_platform.return_value = "Darwin"
        
        # Verify platform is detected as macOS
        assert platform.system() == "Darwin"
        
        # Message handler should work on macOS
        handler = MessageHandler()
        assert handler is not None


class TestCrossPlatformCommandExecution:
    """Test command execution across platforms."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def test_ping_command_cross_platform(self, message_handler):
        """Test ping command works on all platforms."""
        command = {
            "command": "ping",
            "params": {},
            "id": "cross_ping"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        assert response["id"] == "cross_ping"
        
    def test_get_config_cross_platform(self, message_handler):
        """Test get_config command works on all platforms."""
        command = {
            "command": "get_config",
            "params": {},
            "id": "cross_config"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        assert "data" in response
        
        # Config structure should be consistent across platforms
        config_data = response["data"]
        assert "audio" in config_data
        assert "ai" in config_data
        assert "ui" in config_data
        
    def test_get_system_info_cross_platform(self, message_handler):
        """Test get_system_info command works on all platforms."""
        command = {
            "command": "get_system_info",
            "params": {},
            "id": "cross_sysinfo"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        assert "data" in response
        
    def test_get_audio_devices_cross_platform(self, message_handler):
        """Test get_audio_devices command works on all platforms."""
        command = {
            "command": "get_audio_devices",
            "params": {},
            "id": "cross_devices"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        assert "data" in response
        
        # Device list structure should be consistent
        devices_data = response["data"]
        assert "microphones" in devices_data
        assert "speakers" in devices_data


class TestCrossPlatformEventEmission:
    """Test event emission across platforms."""
    
    @pytest.fixture
    def event_emitter(self):
        """Create event emitter for testing."""
        emitter = EventEmitter()
        emitter.start()
        yield emitter
        emitter.stop()
    
    def test_event_emission_cross_platform(self, event_emitter):
        """Test event emission works on all platforms."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
        
        event_emitter.add_listener("test-event", event_handler)
        
        # Emit test event
        test_data = {"message": "cross-platform test"}
        success = event_emitter.emit("test-event", test_data)
        
        assert success
        
        # Wait for event processing
        import time
        time.sleep(0.2)
        
        # Event should be received
        assert len(received_events) == 1
        assert received_events[0]["message"] == "cross-platform test"
    
    def test_multiple_events_cross_platform(self, event_emitter):
        """Test multiple event types work on all platforms."""
        received_events = {}
        
        def create_handler(event_type):
            def handler(event_data):
                if event_type not in received_events:
                    received_events[event_type] = []
                received_events[event_type].append(event_data)
            return handler
        
        # Register handlers for different event types
        event_types = [
            "transcript-updated",
            "response-generated",
            "status-changed",
            "error-occurred"
        ]
        
        for event_type in event_types:
            event_emitter.add_listener(event_type, create_handler(event_type))
        
        # Emit events
        for event_type in event_types:
            event_emitter.emit(event_type, {"type": event_type})
        
        # Wait for processing
        import time
        time.sleep(0.3)
        
        # All events should be received
        assert len(received_events) == len(event_types)
        for event_type in event_types:
            assert event_type in received_events
            assert len(received_events[event_type]) == 1


class TestCrossPlatformIPCServer:
    """Test IPC server across platforms."""
    
    def test_ipc_server_initialization_cross_platform(self):
        """Test IPC server initializes on all platforms."""
        server = IPCServer(host="127.0.0.1", port=0)
        
        assert server is not None
        assert server.host == "127.0.0.1"
        assert not server.is_running()
        
        # Cleanup
        if server.is_running():
            server.stop()
    
    def test_ipc_server_status_cross_platform(self):
        """Test IPC server status reporting on all platforms."""
        server = IPCServer(host="127.0.0.1", port=0)
        
        status = server.get_status()
        
        assert isinstance(status, dict)
        assert "running" in status
        assert "host" in status
        assert "port" in status
        assert "connected_clients" in status
        
        # Cleanup
        if server.is_running():
            server.stop()


class TestCrossPlatformPathHandling:
    """Test path handling across platforms."""
    
    def test_path_normalization(self):
        """Test path normalization works on all platforms."""
        from pathlib import Path
        
        # Test path creation
        test_path = Path("test") / "path" / "file.txt"
        
        assert isinstance(test_path, Path)
        assert test_path.name == "file.txt"
        assert test_path.suffix == ".txt"
        
    def test_config_path_handling(self):
        """Test configuration path handling on all platforms."""
        from backend.config.config_manager import get_config_manager
        
        config_manager = get_config_manager()
        config_file = config_manager.config_file
        
        # Config file path should be valid
        assert isinstance(config_file, (str, Path))
        
        # Convert to Path for platform-independent handling
        config_path = Path(config_file)
        assert config_path.suffix in [".json", ".yaml", ".yml", ""]


class TestCrossPlatformDataSerialization:
    """Test data serialization across platforms."""
    
    def test_json_serialization_cross_platform(self):
        """Test JSON serialization works consistently."""
        test_data = {
            "command": "test",
            "params": {"key": "value"},
            "id": "test_001"
        }
        
        # Serialize
        json_str = json.dumps(test_data)
        
        # Deserialize
        parsed_data = json.loads(json_str)
        
        # Should match original
        assert parsed_data == test_data
        
    def test_message_format_cross_platform(self):
        """Test message format is consistent across platforms."""
        handler = MessageHandler()
        
        command = {
            "command": "ping",
            "params": {},
            "id": "format_test"
        }
        
        response_str = handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        # Response format should be consistent
        assert "status" in response
        assert "id" in response
        assert "timestamp" in response
        
        # Cleanup
        try:
            handler.cleanup()
        except:
            pass


class TestCrossPlatformErrorHandling:
    """Test error handling across platforms."""
    
    def test_error_response_format_cross_platform(self):
        """Test error response format is consistent."""
        handler = MessageHandler()
        
        # Send invalid command
        command = {
            "command": "invalid_command",
            "params": {},
            "id": "error_test"
        }
        
        response_str = handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        # Error format should be consistent
        assert response["status"] == "error"
        assert "error" in response
        assert "id" in response
        assert "timestamp" in response
        
        # Cleanup
        try:
            handler.cleanup()
        except:
            pass
    
    def test_exception_handling_cross_platform(self):
        """Test exception handling is consistent."""
        handler = MessageHandler()
        
        # Send malformed JSON
        malformed_message = "not valid json"
        
        response_str = handler.handle_message(malformed_message)
        response = json.loads(response_str)
        
        # Should handle gracefully on all platforms
        assert response["status"] == "error"
        assert "error" in response
        
        # Cleanup
        try:
            handler.cleanup()
        except:
            pass


class TestCrossPlatformPerformance:
    """Test performance characteristics across platforms."""
    
    def test_command_execution_performance(self):
        """Test command execution performance is reasonable."""
        import time
        
        handler = MessageHandler()
        
        command = {
            "command": "ping",
            "params": {},
            "id": "perf_test"
        }
        
        # Measure execution time
        start_time = time.time()
        
        for i in range(100):
            command["id"] = f"perf_test_{i}"
            response_str = handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            assert response["status"] == "success"
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly on all platforms
        assert duration < 5.0  # 100 commands in less than 5 seconds
        
        # Cleanup
        try:
            handler.cleanup()
        except:
            pass
    
    def test_event_emission_performance(self):
        """Test event emission performance is reasonable."""
        import time
        
        emitter = EventEmitter()
        emitter.start()
        
        received_count = [0]
        
        def event_handler(event_data):
            received_count[0] += 1
        
        emitter.add_listener("perf-test", event_handler)
        
        # Emit many events
        start_time = time.time()
        
        for i in range(100):
            emitter.emit("perf-test", {"count": i})
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should emit quickly on all platforms
        assert duration < 2.0  # 100 events in less than 2 seconds
        
        # Wait for processing
        time.sleep(0.5)
        
        # Most events should be received
        assert received_count[0] >= 90  # At least 90% received
        
        # Cleanup
        emitter.stop()


class TestCrossPlatformConsistency:
    """Test behavior consistency across platforms."""
    
    def test_command_response_consistency(self):
        """Test command responses are consistent across platforms."""
        handler = MessageHandler()
        
        # Test multiple commands
        commands = [
            {"command": "ping", "params": {}, "id": "consist_1"},
            {"command": "get_config", "params": {}, "id": "consist_2"},
            {"command": "get_system_info", "params": {}, "id": "consist_3"},
        ]
        
        for command in commands:
            response_str = handler.handle_message(json.dumps(command))
            response = json.loads(response_str)
            
            # All responses should have consistent structure
            assert "status" in response
            assert "id" in response
            assert "timestamp" in response
            assert response["id"] == command["id"]
        
        # Cleanup
        try:
            handler.cleanup()
        except:
            pass
    
    def test_event_structure_consistency(self):
        """Test event structures are consistent across platforms."""
        emitter = EventEmitter()
        emitter.start()
        
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
        
        # Register for multiple event types
        event_types = ["test-1", "test-2", "test-3"]
        for event_type in event_types:
            emitter.add_listener(event_type, event_handler)
        
        # Emit events
        for event_type in event_types:
            emitter.emit(event_type, {"type": event_type, "data": "test"})
        
        # Wait for processing
        import time
        time.sleep(0.3)
        
        # All events should have consistent structure
        assert len(received_events) == len(event_types)
        for event in received_events:
            assert "type" in event
            assert "data" in event
        
        # Cleanup
        emitter.stop()


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
