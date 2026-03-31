#!/usr/bin/env python3
"""
Test frontend-backend communication for transcript functionality.
"""

import sys
import os
import time
import threading
import json
import socket
from pathlib import Path

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.utils.logger import get_logger
from backend.ipc.ipc_server import IPCServer
from backend.ipc.event_emitter import get_event_emitter

logger = get_logger(__name__)

def test_ipc_communication():
    """Test IPC server communication."""
    print("🧪 Testing IPC communication...")
    
    # Start IPC server in background thread
    ipc_server = IPCServer(host="127.0.0.1", port=9877)  # Use different port for testing
    
    server_thread = threading.Thread(target=ipc_server.start, daemon=True)
    server_thread.start()
    
    # Wait for server to start
    time.sleep(1)
    
    # Test client connection
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 9877))
        
        # Receive welcome message
        welcome_data = client_socket.recv(1024)
        welcome_msg = welcome_data.decode('utf-8').strip()
        print(f"📨 Received welcome: {welcome_msg}")
        
        # Send a test command
        test_command = json.dumps({
            "command": "ping",
            "data": {}
        })
        
        client_socket.send((test_command + '\n').encode('utf-8'))
        
        # Receive response
        response_data = client_socket.recv(1024)
        response_msg = response_data.decode('utf-8').strip()
        print(f"📨 Received response: {response_msg}")
        
        client_socket.close()
        
        print("✅ IPC communication test passed")
        return True
        
    except Exception as e:
        print(f"❌ IPC communication test failed: {e}")
        return False
    finally:
        ipc_server.stop()

def test_transcript_event_forwarding():
    """Test transcript event forwarding through IPC."""
    print("🧪 Testing transcript event forwarding...")
    
    # Start IPC server
    ipc_server = IPCServer(host="127.0.0.1", port=9878)
    
    server_thread = threading.Thread(target=ipc_server.start, daemon=True)
    server_thread.start()
    
    time.sleep(1)
    
    try:
        # Connect client
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 9878))
        
        # Receive welcome message
        welcome_data = client_socket.recv(1024)
        print(f"📨 Welcome: {welcome_data.decode('utf-8').strip()}")
        
        # Emit a transcript event
        event_emitter = get_event_emitter()
        test_transcript = {
            "id": "test_transcript_2",
            "timestamp": "2025-01-28T23:45:00Z",
            "source": "microphone",
            "text": "Testing event forwarding",
            "confidence": 0.98
        }
        
        print(f"📤 Emitting transcript event: {test_transcript['text']}")
        event_emitter.emit_transcript_updated(test_transcript)
        
        # Wait for event to be processed and forwarded
        time.sleep(0.5)
        
        # Check if we received the forwarded event
        client_socket.settimeout(2.0)
        try:
            event_data = client_socket.recv(1024)
            event_msg = event_data.decode('utf-8').strip()
            print(f"📨 Received forwarded event: {event_msg}")
            
            # Parse the event
            event_json = json.loads(event_msg)
            if event_json.get('type') == 'transcript-updated':
                print("✅ Transcript event forwarding test passed")
                return True
            else:
                print(f"❌ Unexpected event type: {event_json.get('type')}")
                return False
                
        except socket.timeout:
            print("❌ No event received within timeout")
            return False
        
    except Exception as e:
        print(f"❌ Event forwarding test failed: {e}")
        return False
    finally:
        try:
            client_socket.close()
        except:
            pass
        ipc_server.stop()

def main():
    """Main test function."""
    print("🚀 Starting frontend-backend communication test...")
    print("=" * 60)
    
    # Test 1: Basic IPC communication
    if not test_ipc_communication():
        print("❌ Basic IPC communication test failed")
        return 1
    
    print("=" * 60)
    
    # Test 2: Transcript event forwarding
    if not test_transcript_event_forwarding():
        print("❌ Transcript event forwarding test failed")
        return 1
    
    print("=" * 60)
    print("✅ All frontend-backend communication tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())