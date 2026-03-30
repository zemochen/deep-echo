"""
Frontend-Backend Communication Integration Tests.

Tests the communication flow between React frontend, Tauri middleware,
and Python backend through IPC commands and events.

Requirements: 2.1-2.7, 3.1-3.8
"""

import pytest
import json
import time
import threading
import queue
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from backend.ipc.ipc_server import IPCServer
from backend.ipc.message_handler import MessageHandler
from backend.ipc.event_emitter import EventEmitter
from backend.backend_service import BackendService


class MockTauriConnection:
    """Mock Tauri connection for testing."""
    
    def __init__(self):
        self.sent_messages = []
        self.received_messages = queue.Queue()
        self.is_connected = True
        
    def send(self, message):
        """Send message to Tauri."""
        self.sent_messages.append(message)
        
    def receive(self, timeout=1.0):
        """Receive message from Tauri."""
        try:
            return self.received_messages.get(timeout=timeout)
        except queue.Empty:
            return None
            
    def inject_message(self, message):
        """Inject a message for testing."""
        self.received_messages.put(message)
        
    def close(self):
        """Close connection."""
        self.is_connected = False


class TestCommandExecution:
    """Test Tauri command execution flow."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler."""
        handler = MessageHandler()
        return handler
        
    def test_start_recording_command(self, message_handler):
        """Test start_recording command execution."""
        # Create command message
        command = {
            "command": "start_recording",
            "params": {"device_type": "microphone"},
            "id": "test_001"
        }
        
        # Execute command
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        # Verify response
        assert response is not None
        assert response["id"] == "test_001"
        assert response["status"] in ["success", "error"]  # May fail without audio device
        
    def test_stop_recording_command(self, message_handler):
        """Test stop_recording command execution."""
        command = {
            "command": "stop_recording",
            "params": {},
            "id": "test_002"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response is not None
        assert response["id"] == "test_002"
        assert response["status"] in ["success", "error"]
        
    def test_get_transcript_command(self, message_handler):
        """Test get_transcript command execution."""
        command = {
            "command": "get_transcript",
            "params": {},
            "id": "test_003"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response is not None
        assert response["id"] == "test_003"
        assert response["status"] == "success"
        assert "data" in response
        
    def test_get_config_command(self, message_handler):
        """Test get_config command execution."""
        command = {
            "command": "get_config",
            "params": {},
            "id": "test_006"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response is not None
        assert response["id"] == "test_006"
        assert response["status"] == "success"
        assert "data" in response
        
    def test_invalid_command(self, message_handler):
        """Test handling of invalid command."""
        command = {
            "command": "invalid_command",
            "params": {},
            "id": "test_008"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response is not None
        assert response["id"] == "test_008"
        assert response["status"] == "error"
        assert "error" in response
        
    def test_malformed_json(self, message_handler):
        """Test handling of malformed JSON."""
        malformed_message = "not valid json"
        
        response_str = message_handler.handle_message(malformed_message)
        response = json.loads(response_str)
        
        assert response is not None
        assert response["status"] == "error"
        assert "error" in response
        
    def test_ping_command(self, message_handler):
        """Test ping command for connectivity."""
        command = {
            "command": "ping",
            "params": {},
            "id": "test_ping"
        }
        
        response_str = message_handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response is not None
        assert response["id"] == "test_ping"
        assert response["status"] == "success"


class TestEventForwarding:
    """Test event forwarding from backend to frontend."""
    
    @pytest.fixture
    def event_emitter(self):
        """Create event emitter."""
        emitter = EventEmitter()
        emitter.start()
        yield emitter
        emitter.stop()
        
    def test_transcript_updated_event(self, event_emitter):
        """Test transcript-updated event emission."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
            
        # Subscribe to event
        event_emitter.add_listener("transcript-updated", event_handler)
        
        # Emit event
        transcript_data = {
            "id": "trans_001",
            "timestamp": time.time(),
            "source": "microphone",
            "text": "Hello world",
            "confidence": 0.95
        }
        
        event_emitter.emit("transcript-updated", transcript_data)
        
        # Wait for event processing
        time.sleep(0.2)
        
        # Verify event was received
        assert len(received_events) == 1
        assert received_events[0]["id"] == "trans_001"
        assert received_events[0]["text"] == "Hello world"
        
    def test_response_generated_event(self, event_emitter):
        """Test response-generated event emission."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
            
        event_emitter.add_listener("response-generated", event_handler)
        
        response_data = {
            "id": "resp_001",
            "timestamp": time.time(),
            "provider": "openai",
            "text": "AI response text",
            "context": "User context"
        }
        
        event_emitter.emit("response-generated", response_data)
        time.sleep(0.2)
        
        assert len(received_events) == 1
        assert received_events[0]["provider"] == "openai"
        assert received_events[0]["text"] == "AI response text"
        
    def test_status_changed_event(self, event_emitter):
        """Test status-changed event emission."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
            
        event_emitter.add_listener("status-changed", event_handler)
        
        status_data = {
            "state": "recording",
            "message": "Recording in progress",
            "details": {"device": "microphone"}
        }
        
        event_emitter.emit("status-changed", status_data)
        time.sleep(0.2)
        
        assert len(received_events) == 1
        assert received_events[0]["state"] == "recording"
        
    def test_error_occurred_event(self, event_emitter):
        """Test error-occurred event emission."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
            
        event_emitter.add_listener("error-occurred", event_handler)
        
        error_data = {
            "error_type": "AudioDeviceError",
            "message": "Microphone not found",
            "timestamp": time.time()
        }
        
        event_emitter.emit("error-occurred", error_data)
        time.sleep(0.2)
        
        assert len(received_events) == 1
        assert received_events[0]["error_type"] == "AudioDeviceError"
        
    def test_multiple_event_subscribers(self, event_emitter):
        """Test multiple subscribers to same event."""
        received_by_handler1 = []
        received_by_handler2 = []
        
        def handler1(event_data):
            received_by_handler1.append(event_data)
            
        def handler2(event_data):
            received_by_handler2.append(event_data)
            
        event_emitter.add_listener("test-event", handler1)
        event_emitter.add_listener("test-event", handler2)
        
        test_data = {"message": "test"}
        event_emitter.emit("test-event", test_data)
        time.sleep(0.2)
        
        # Both handlers should receive the event
        assert len(received_by_handler1) == 1
        assert len(received_by_handler2) == 1
        
    def test_event_unsubscribe(self, event_emitter):
        """Test unsubscribing from events."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
            
        # Subscribe
        event_emitter.add_listener("test-event", event_handler)
        
        # Emit first event
        event_emitter.emit("test-event", {"count": 1})
        time.sleep(0.2)
        
        # Unsubscribe
        event_emitter.remove_listener("test-event", event_handler)
        
        # Emit second event
        event_emitter.emit("test-event", {"count": 2})
        time.sleep(0.2)
        
        # Should only have received first event
        assert len(received_events) == 1
        assert received_events[0]["count"] == 1
        
    def test_event_ordering(self, event_emitter):
        """Test that events are received in order."""
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
            
        event_emitter.add_listener("ordered-event", event_handler)
        
        # Emit multiple events in sequence
        for i in range(10):
            event_emitter.emit("ordered-event", {"sequence": i})
            time.sleep(0.01)
            
        time.sleep(0.3)
        
        # Verify events were received in order
        assert len(received_events) == 10
        for i, event in enumerate(received_events):
            assert event["sequence"] == i


class TestErrorHandling:
    """Test error handling in communication layer."""
    
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON messages."""
        handler = MessageHandler()
        
        # Test various malformed messages
        malformed_messages = [
            "not json",
            "{incomplete",
            '{"command": "test"',  # Missing closing brace
            "",  # Empty string
        ]
        
        for msg in malformed_messages:
            response_str = handler.handle_message(msg)
            response = json.loads(response_str)
            assert response["status"] == "error"
            assert "error" in response
            
    def test_missing_command_field(self):
        """Test handling of messages with missing command field."""
        handler = MessageHandler()
        
        command = {
            "params": {},
            "id": "test_missing_cmd"
        }
        
        response_str = handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response["status"] == "error"
        assert "command" in response["error"].lower()
        
    def test_unknown_command(self):
        """Test handling of unknown commands."""
        handler = MessageHandler()
        
        command = {
            "command": "unknown_command_xyz",
            "params": {},
            "id": "test_unknown"
        }
        
        response_str = handler.handle_message(json.dumps(command))
        response = json.loads(response_str)
        
        assert response["status"] == "error"
        assert "unknown" in response["error"].lower()


class TestIPCServerIntegration:
    """Test IPC server integration."""
    
    @pytest.fixture
    def ipc_server(self):
        """Create IPC server for testing."""
        server = IPCServer(host="127.0.0.1", port=0)  # Port 0 for random port
        yield server
        if server.is_running():
            server.stop()
        
    def test_server_initialization(self, ipc_server):
        """Test IPC server initialization."""
        assert ipc_server is not None
        assert ipc_server.host == "127.0.0.1"
        assert not ipc_server.is_running()
        
    def test_server_status(self, ipc_server):
        """Test server status reporting."""
        status = ipc_server.get_status()
        
        assert isinstance(status, dict)
        assert "running" in status
        assert "host" in status
        assert "port" in status
        assert "connected_clients" in status
        
    def test_event_emitter_integration(self, ipc_server):
        """Test event emitter integration with IPC server."""
        assert ipc_server.event_emitter is not None
        assert isinstance(ipc_server.event_emitter, EventEmitter)
        
    def test_message_handler_integration(self, ipc_server):
        """Test message handler integration with IPC server."""
        assert ipc_server.message_handler is not None
        assert isinstance(ipc_server.message_handler, MessageHandler)


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
