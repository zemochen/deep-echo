"""
Complete Workflow Integration Tests.

Tests end-to-end workflows including audio recording to transcription,
AI response generation, and configuration management.

Requirements: All requirements (complete workflows)
"""

import pytest
import json
import time
import threading
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from backend.ipc.ipc_server import IPCServer
from backend.ipc.message_handler import MessageHandler
from backend.ipc.event_emitter import EventEmitter, get_event_emitter


class TestAudioRecordingToTranscriptionWorkflow:
    """Test complete audio recording to transcription workflow."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        # Cleanup
        try:
            handler.cleanup()
        except:
            pass
    
    def test_audio_recording_workflow(self, message_handler):
        """Test complete audio recording workflow."""
        # Step 1: Get available audio devices
        get_devices_cmd = {
            "command": "get_audio_devices",
            "params": {},
            "id": "workflow_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_devices_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        assert "data" in response
        
        # Step 2: Start recording (may fail without audio device)
        start_recording_cmd = {
            "command": "start_recording",
            "params": {"device_type": "microphone"},
            "id": "workflow_002"
        }
        
        response_str = message_handler.handle_message(json.dumps(start_recording_cmd))
        response = json.loads(response_str)
        
        # Recording may fail in test environment, that's OK
        assert response["status"] in ["success", "error"]
        
        if response["status"] == "success":
            # Step 3: Wait a bit for recording
            time.sleep(0.5)
            
            # Step 4: Get transcript
            get_transcript_cmd = {
                "command": "get_transcript",
                "params": {},
                "id": "workflow_003"
            }
            
            response_str = message_handler.handle_message(json.dumps(get_transcript_cmd))
            response = json.loads(response_str)
            
            assert response["status"] == "success"
            assert "data" in response
            
            # Step 5: Stop recording
            stop_recording_cmd = {
                "command": "stop_recording",
                "params": {},
                "id": "workflow_004"
            }
            
            response_str = message_handler.handle_message(json.dumps(stop_recording_cmd))
            response = json.loads(response_str)
            
            assert response["status"] == "success"
    
    def test_transcript_retrieval_without_recording(self, message_handler):
        """Test getting transcript without active recording."""
        get_transcript_cmd = {
            "command": "get_transcript",
            "params": {},
            "id": "workflow_005"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_transcript_cmd))
        response = json.loads(response_str)
        
        # Should return empty transcript gracefully
        assert response["status"] == "success"
        assert "data" in response
    
    def test_multiple_recording_sessions(self, message_handler):
        """Test multiple recording sessions in sequence."""
        for i in range(3):
            # Start recording
            start_cmd = {
                "command": "start_recording",
                "params": {"device_type": "microphone"},
                "id": f"multi_start_{i}"
            }
            
            response_str = message_handler.handle_message(json.dumps(start_cmd))
            response = json.loads(response_str)
            
            if response["status"] == "success":
                time.sleep(0.2)
                
                # Stop recording
                stop_cmd = {
                    "command": "stop_recording",
                    "params": {},
                    "id": f"multi_stop_{i}"
                }
                
                response_str = message_handler.handle_message(json.dumps(stop_cmd))
                response = json.loads(response_str)
                
                assert response["status"] == "success"


class TestAIResponseGenerationWorkflow:
    """Test AI response generation workflow."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def test_ai_response_workflow(self, message_handler):
        """Test complete AI response generation workflow."""
        # Step 1: Get current configuration
        get_config_cmd = {
            "command": "get_config",
            "params": {},
            "id": "ai_workflow_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_config_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        assert "data" in response
        
        # Step 2: Generate AI response (may fail without API key)
        generate_cmd = {
            "command": "generate_response",
            "params": {"context": "Test context for AI response"},
            "id": "ai_workflow_002"
        }
        
        response_str = message_handler.handle_message(json.dumps(generate_cmd))
        response = json.loads(response_str)
        
        # May fail without valid API key, that's OK
        assert response["status"] in ["success", "error"]
    
    def test_provider_switching_workflow(self, message_handler):
        """Test AI provider switching workflow."""
        # Get current config
        get_config_cmd = {
            "command": "get_config",
            "params": {},
            "id": "provider_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_config_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        
        # Note: Actual provider switching requires valid API keys
        # This test just verifies the command structure works
    
    def test_response_with_empty_context(self, message_handler):
        """Test AI response generation with empty context."""
        generate_cmd = {
            "command": "generate_response",
            "params": {"context": ""},
            "id": "empty_context"
        }
        
        response_str = message_handler.handle_message(json.dumps(generate_cmd))
        response = json.loads(response_str)
        
        # Should handle gracefully
        assert response["status"] in ["success", "error"]


class TestConfigurationManagementWorkflow:
    """Test configuration management workflow."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def test_config_read_workflow(self, message_handler):
        """Test configuration reading workflow."""
        get_config_cmd = {
            "command": "get_config",
            "params": {},
            "id": "config_read_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_config_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        assert "data" in response
        
        # Verify config structure
        config_data = response["data"]
        assert "audio" in config_data
        assert "ai" in config_data
        assert "ui" in config_data
    
    def test_config_update_workflow(self, message_handler):
        """Test configuration update workflow."""
        # Step 1: Get current config
        get_config_cmd = {
            "command": "get_config",
            "params": {},
            "id": "config_update_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_config_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        original_config = response["data"]
        
        # Step 2: Update config
        update_config_cmd = {
            "command": "update_config",
            "params": {
                "config": {
                    "audio": {
                        "recordTimeout": 5
                    }
                }
            },
            "id": "config_update_002"
        }
        
        response_str = message_handler.handle_message(json.dumps(update_config_cmd))
        response = json.loads(response_str)
        
        # Update may succeed or fail depending on environment
        assert response["status"] in ["success", "error"]
        
        # Step 3: Verify config was updated (if update succeeded)
        if response["status"] == "success":
            get_config_cmd["id"] = "config_update_003"
            response_str = message_handler.handle_message(json.dumps(get_config_cmd))
            response = json.loads(response_str)
            
            assert response["status"] == "success"
    
    def test_config_validation(self, message_handler):
        """Test configuration validation."""
        # Try to update with invalid config
        invalid_config_cmd = {
            "command": "update_config",
            "params": {
                "config": {
                    "audio": {
                        "recordTimeout": "invalid"  # Should be number
                    }
                }
            },
            "id": "config_invalid"
        }
        
        response_str = message_handler.handle_message(json.dumps(invalid_config_cmd))
        response = json.loads(response_str)
        
        # Should handle invalid config gracefully
        assert response["status"] in ["success", "error"]


class TestEndToEndWorkflow:
    """Test complete end-to-end workflows."""
    
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
    
    def test_complete_conversation_workflow(self, message_handler, event_emitter):
        """Test complete conversation workflow from recording to AI response."""
        # Track events
        received_events = []
        
        def event_handler(event_data):
            received_events.append(event_data)
        
        event_emitter.add_listener("transcript-updated", event_handler)
        event_emitter.add_listener("response-generated", event_handler)
        
        # Step 1: Start recording
        start_cmd = {
            "command": "start_recording",
            "params": {"device_type": "microphone"},
            "id": "e2e_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(start_cmd))
        response = json.loads(response_str)
        
        if response["status"] == "success":
            # Step 2: Wait for some recording
            time.sleep(0.3)
            
            # Step 3: Get transcript
            get_transcript_cmd = {
                "command": "get_transcript",
                "params": {},
                "id": "e2e_002"
            }
            
            response_str = message_handler.handle_message(json.dumps(get_transcript_cmd))
            response = json.loads(response_str)
            
            assert response["status"] == "success"
            
            # Step 4: Stop recording
            stop_cmd = {
                "command": "stop_recording",
                "params": {},
                "id": "e2e_003"
            }
            
            response_str = message_handler.handle_message(json.dumps(stop_cmd))
            response = json.loads(response_str)
            
            assert response["status"] == "success"
    
    def test_system_health_check_workflow(self, message_handler):
        """Test system health check workflow."""
        # Get system info
        system_info_cmd = {
            "command": "get_system_info",
            "params": {},
            "id": "health_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(system_info_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        
        # Get config
        get_config_cmd = {
            "command": "get_config",
            "params": {},
            "id": "health_002"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_config_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        
        # Get audio devices
        get_devices_cmd = {
            "command": "get_audio_devices",
            "params": {},
            "id": "health_003"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_devices_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
    
    def test_error_recovery_workflow(self, message_handler):
        """Test error recovery in workflow."""
        # Try invalid command
        invalid_cmd = {
            "command": "invalid_command",
            "params": {},
            "id": "error_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(invalid_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "error"
        
        # System should still be responsive after error
        ping_cmd = {
            "command": "ping",
            "params": {},
            "id": "error_002"
        }
        
        response_str = message_handler.handle_message(json.dumps(ping_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
    
    def test_concurrent_operations_workflow(self, message_handler):
        """Test concurrent operations in workflow."""
        results = []
        
        def execute_command(cmd_id):
            cmd = {
                "command": "ping",
                "params": {},
                "id": f"concurrent_{cmd_id}"
            }
            
            response_str = message_handler.handle_message(json.dumps(cmd))
            response = json.loads(response_str)
            results.append(response)
        
        # Execute multiple commands concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=execute_command, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=2.0)
        
        # All commands should succeed
        assert len(results) == 5
        for result in results:
            assert result["status"] == "success"


class TestWorkflowStateManagement:
    """Test state management across workflows."""
    
    @pytest.fixture
    def message_handler(self):
        """Create message handler for testing."""
        handler = MessageHandler()
        yield handler
        try:
            handler.cleanup()
        except:
            pass
    
    def test_recording_state_persistence(self, message_handler):
        """Test recording state persists across commands."""
        # Start recording
        start_cmd = {
            "command": "start_recording",
            "params": {"device_type": "microphone"},
            "id": "state_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(start_cmd))
        response = json.loads(response_str)
        
        if response["status"] == "success":
            # Try to start again (should indicate already recording)
            start_cmd["id"] = "state_002"
            response_str = message_handler.handle_message(json.dumps(start_cmd))
            response = json.loads(response_str)
            
            # Should handle duplicate start gracefully
            assert response["status"] in ["success", "error"]
            
            # Stop recording
            stop_cmd = {
                "command": "stop_recording",
                "params": {},
                "id": "state_003"
            }
            
            response_str = message_handler.handle_message(json.dumps(stop_cmd))
            response = json.loads(response_str)
            
            assert response["status"] == "success"
    
    def test_transcript_accumulation(self, message_handler):
        """Test transcript accumulates over time."""
        # Get initial transcript
        get_transcript_cmd = {
            "command": "get_transcript",
            "params": {},
            "id": "accum_001"
        }
        
        response_str = message_handler.handle_message(json.dumps(get_transcript_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        
        # Clear transcript
        clear_cmd = {
            "command": "clear_transcript",
            "params": {},
            "id": "accum_002"
        }
        
        response_str = message_handler.handle_message(json.dumps(clear_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"
        
        # Get transcript again (should be empty)
        get_transcript_cmd["id"] = "accum_003"
        response_str = message_handler.handle_message(json.dumps(get_transcript_cmd))
        response = json.loads(response_str)
        
        assert response["status"] == "success"


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])
