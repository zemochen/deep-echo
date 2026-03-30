#!/usr/bin/env python3
"""
Backend Adaptation Verification Script.

This script verifies that the backend IPC adaptation is working correctly by:
1. Testing IPC server initialization
2. Testing command execution
3. Testing event forwarding
4. Testing error handling
"""

import sys
import time
import json
import socket
import threading
from typing import Dict, Any, List, Optional
from datetime import datetime


class IPCClient:
    """Simple IPC client for testing backend communication."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9876):
        """Initialize IPC client."""
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.received_events: List[Dict[str, Any]] = []
        self._receive_thread: Optional[threading.Thread] = None
        self._running = False
    
    def connect(self, timeout: float = 5.0) -> bool:
        """
        Connect to the IPC server.
        
        Args:
            timeout: Connection timeout in seconds
            
        Returns:
            True if connected successfully
        """
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(timeout)
            self.socket.connect((self.host, self.port))
            self.connected = True
            
            # Start receiving thread
            self._running = True
            self._receive_thread = threading.Thread(
                target=self._receive_messages,
                daemon=True
            )
            self._receive_thread.start()
            
            print(f"✓ Connected to IPC server at {self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to connect to IPC server: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the IPC server."""
        self._running = False
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        self.connected = False
        print("✓ Disconnected from IPC server")
    
    def send_command(self, command: str, params: Dict[str, Any] = None, request_id: str = None) -> Optional[Dict[str, Any]]:
        """
        Send a command to the backend.
        
        Args:
            command: Command name
            params: Command parameters
            request_id: Optional request ID
            
        Returns:
            Response data or None if failed
        """
        if not self.connected:
            print("✗ Not connected to IPC server")
            return None
        
        try:
            # Create request
            request = {
                "command": command,
                "params": params or {},
                "id": request_id or f"req_{int(time.time() * 1000)}"
            }
            
            # Send request
            message = json.dumps(request) + '\n'
            self.socket.sendall(message.encode('utf-8'))
            
            # Wait for response (with timeout)
            start_time = time.time()
            timeout = 10.0
            
            while time.time() - start_time < timeout:
                # Check if we have a response in received events
                for event in self.received_events:
                    if event.get("id") == request["id"]:
                        self.received_events.remove(event)
                        return event
                
                time.sleep(0.1)
            
            print(f"✗ Timeout waiting for response to command: {command}")
            return None
            
        except Exception as e:
            print(f"✗ Failed to send command {command}: {e}")
            return None
    
    def _receive_messages(self) -> None:
        """Receive messages from the server (runs in background thread)."""
        buffer = ""
        
        while self._running:
            try:
                data = self.socket.recv(4096)
                
                if not data:
                    break
                
                buffer += data.decode('utf-8')
                
                # Process complete messages
                while '\n' in buffer:
                    message, buffer = buffer.split('\n', 1)
                    
                    if message.strip():
                        try:
                            event = json.loads(message)
                            self.received_events.append(event)
                        except json.JSONDecodeError as e:
                            print(f"✗ Failed to parse message: {e}")
                
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"✗ Error receiving messages: {e}")
                break
    
    def get_events(self, event_type: str = None, timeout: float = 2.0) -> List[Dict[str, Any]]:
        """
        Get received events.
        
        Args:
            event_type: Optional event type filter
            timeout: How long to wait for events
            
        Returns:
            List of events
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            events = [e for e in self.received_events if not event_type or e.get("type") == event_type]
            if events:
                # Remove returned events from list
                for event in events:
                    self.received_events.remove(event)
                return events
            time.sleep(0.1)
        
        return []


class BackendVerifier:
    """Verifies backend adaptation functionality."""
    
    def __init__(self):
        """Initialize the verifier."""
        self.client = IPCClient()
        self.test_results: List[Dict[str, Any]] = []
    
    def run_all_tests(self) -> bool:
        """
        Run all verification tests.
        
        Returns:
            True if all tests passed
        """
        print("=" * 70)
        print("Backend Adaptation Verification")
        print("=" * 70)
        print()
        
        # Test 1: IPC Server Connection
        if not self.test_ipc_connection():
            print("\n✗ IPC connection test failed - cannot proceed with other tests")
            return False
        
        # Test 2: Basic Commands
        if not self.test_basic_commands():
            print("\n✗ Basic commands test failed")
            return False
        
        # Test 3: Audio Commands
        if not self.test_audio_commands():
            print("\n✗ Audio commands test failed")
            return False
        
        # Test 4: Config Commands
        if not self.test_config_commands():
            print("\n✗ Config commands test failed")
            return False
        
        # Test 5: System Commands
        if not self.test_system_commands():
            print("\n✗ System commands test failed")
            return False
        
        # Test 6: Error Handling
        if not self.test_error_handling():
            print("\n✗ Error handling test failed")
            return False
        
        # Cleanup
        self.client.disconnect()
        
        # Print summary
        self.print_summary()
        
        # Check if all tests passed
        all_passed = all(result["passed"] for result in self.test_results)
        
        if all_passed:
            print("\n" + "=" * 70)
            print("✓ All backend adaptation tests passed!")
            print("=" * 70)
        else:
            print("\n" + "=" * 70)
            print("✗ Some backend adaptation tests failed")
            print("=" * 70)
        
        return all_passed
    
    def test_ipc_connection(self) -> bool:
        """Test IPC server connection."""
        print("Test 1: IPC Server Connection")
        print("-" * 70)
        
        # Try to connect
        success = self.client.connect(timeout=5.0)
        
        if success:
            # Wait for welcome message
            time.sleep(0.5)
            events = self.client.get_events(event_type="welcome", timeout=2.0)
            
            if events:
                print(f"✓ Received welcome message: {events[0].get('message')}")
                self.record_test("IPC Connection", True, "Successfully connected and received welcome")
                return True
            else:
                print("✗ Did not receive welcome message")
                self.record_test("IPC Connection", False, "No welcome message received")
                return False
        else:
            self.record_test("IPC Connection", False, "Failed to connect to IPC server")
            return False
    
    def test_basic_commands(self) -> bool:
        """Test basic commands."""
        print("\nTest 2: Basic Commands")
        print("-" * 70)
        
        all_passed = True
        
        # Test ping command
        print("Testing ping command...")
        response = self.client.send_command("ping")
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            if data.get("message") == "pong":
                print(f"✓ Ping successful: {data.get('timestamp')}")
            else:
                print("✗ Ping response invalid")
                all_passed = False
        else:
            print("✗ Ping command failed")
            all_passed = False
        
        self.record_test("Basic Commands - Ping", all_passed, "Ping command test")
        return all_passed
    
    def test_audio_commands(self) -> bool:
        """Test audio-related commands."""
        print("\nTest 3: Audio Commands")
        print("-" * 70)
        
        all_passed = True
        
        # Test get_audio_devices
        print("Testing get_audio_devices command...")
        response = self.client.send_command("get_audio_devices")
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            microphones = data.get("microphones", [])
            speakers = data.get("speakers", [])
            print(f"✓ Found {len(microphones)} microphone(s) and {len(speakers)} speaker(s)")
        else:
            print("✗ get_audio_devices command failed")
            all_passed = False
        
        # Test start_recording (microphone)
        print("Testing start_recording command (microphone)...")
        response = self.client.send_command("start_recording", {"device_type": "microphone"})
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            if data.get("status") == "recording":
                print(f"✓ Recording started: {data.get('message')}")
                
                # Wait a bit
                time.sleep(1.0)
                
                # Test stop_recording
                print("Testing stop_recording command...")
                response = self.client.send_command("stop_recording")
                
                if response and response.get("status") == "success":
                    data = response.get("data", {})
                    if data.get("status") == "stopped":
                        print(f"✓ Recording stopped: {data.get('message')}")
                    else:
                        print("✗ Recording stop response invalid")
                        all_passed = False
                else:
                    print("✗ stop_recording command failed")
                    all_passed = False
            else:
                print("✗ Recording start response invalid")
                all_passed = False
        else:
            print("✗ start_recording command failed")
            all_passed = False
        
        # Test get_transcript
        print("Testing get_transcript command...")
        response = self.client.send_command("get_transcript")
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            transcript = data.get("transcript", "")
            entries = data.get("entries", [])
            print(f"✓ Transcript retrieved: {len(entries)} entries")
        else:
            print("✗ get_transcript command failed")
            all_passed = False
        
        self.record_test("Audio Commands", all_passed, "Audio command tests")
        return all_passed
    
    def test_config_commands(self) -> bool:
        """Test configuration commands."""
        print("\nTest 4: Config Commands")
        print("-" * 70)
        
        all_passed = True
        
        # Test get_config
        print("Testing get_config command...")
        response = self.client.send_command("get_config")
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            audio_config = data.get("audio", {})
            ai_config = data.get("ai", {})
            ui_config = data.get("ui", {})
            
            if audio_config and ai_config and ui_config:
                print(f"✓ Config retrieved:")
                print(f"  - Audio: {list(audio_config.keys())}")
                print(f"  - AI: Provider={ai_config.get('provider')}, Model={ai_config.get('model')}")
                print(f"  - UI: {list(ui_config.keys())}")
            else:
                print("✗ Config response incomplete")
                all_passed = False
        else:
            print("✗ get_config command failed")
            all_passed = False
        
        # Test update_config (UI settings only to avoid breaking things)
        print("Testing update_config command...")
        response = self.client.send_command("update_config", {
            "config": {
                "ui": {
                    "updateInterval": 2.0
                }
            }
        })
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            updated_fields = data.get("updated_fields", [])
            print(f"✓ Config updated: {updated_fields}")
        else:
            print("✗ update_config command failed")
            all_passed = False
        
        self.record_test("Config Commands", all_passed, "Configuration command tests")
        return all_passed
    
    def test_system_commands(self) -> bool:
        """Test system commands."""
        print("\nTest 5: System Commands")
        print("-" * 70)
        
        all_passed = True
        
        # Test get_system_info
        print("Testing get_system_info command...")
        response = self.client.send_command("get_system_info")
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            platform = data.get("platform")
            python_version = data.get("python_version")
            
            if platform and python_version:
                print(f"✓ System info retrieved:")
                print(f"  - Platform: {platform}")
                print(f"  - Python: {python_version[:50]}...")
                print(f"  - Architecture: {data.get('architecture')}")
            else:
                print("✗ System info response incomplete")
                all_passed = False
        else:
            print("✗ get_system_info command failed")
            all_passed = False
        
        self.record_test("System Commands", all_passed, "System command tests")
        return all_passed
    
    def test_error_handling(self) -> bool:
        """Test error handling."""
        print("\nTest 6: Error Handling")
        print("-" * 70)
        
        all_passed = True
        
        # Test unknown command
        print("Testing unknown command...")
        response = self.client.send_command("unknown_command_xyz")
        
        if response and response.get("status") == "error":
            error = response.get("error", "")
            if "Unknown command" in error:
                print(f"✓ Unknown command handled correctly: {error}")
            else:
                print("✗ Unknown command error message unexpected")
                all_passed = False
        else:
            print("✗ Unknown command not handled as error")
            all_passed = False
        
        # Test invalid parameters
        print("Testing invalid parameters...")
        response = self.client.send_command("start_recording", {"device_type": "invalid_device"})
        
        if response and response.get("status") == "success":
            data = response.get("data", {})
            if "error" in data or data.get("status") == "error":
                print(f"✓ Invalid parameters handled correctly")
            else:
                print("✗ Invalid parameters not handled properly")
                all_passed = False
        else:
            print("✗ Invalid parameters test inconclusive")
        
        self.record_test("Error Handling", all_passed, "Error handling tests")
        return all_passed
    
    def record_test(self, name: str, passed: bool, description: str) -> None:
        """
        Record a test result.
        
        Args:
            name: Test name
            passed: Whether test passed
            description: Test description
        """
        self.test_results.append({
            "name": name,
            "passed": passed,
            "description": description,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)
        
        passed_count = sum(1 for r in self.test_results if r["passed"])
        total_count = len(self.test_results)
        
        for result in self.test_results:
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"{status}: {result['name']}")
        
        print("-" * 70)
        print(f"Total: {passed_count}/{total_count} tests passed")
        print("=" * 70)


def main():
    """Main entry point."""
    print("\nBackend Adaptation Verification")
    print("=" * 70)
    print("\nThis script will verify that the backend IPC adaptation is working.")
    print("Make sure the backend service is running before proceeding.")
    print("\nTo start the backend service, run:")
    print("  python -m backend.backend_service")
    print("\n" + "=" * 70)
    
    input("\nPress Enter to start verification...")
    print()
    
    # Run verification
    verifier = BackendVerifier()
    success = verifier.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
