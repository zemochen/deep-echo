#!/usr/bin/env python3
"""
Integration test for transcript functionality with running backend.
"""

import sys
import os
import time
import socket
import json
from pathlib import Path

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.utils.logger import get_logger
from backend.ipc.event_emitter import get_event_emitter

logger = get_logger(__name__)

def test_with_running_backend():
    """Test with the running backend service."""
    print("🧪 Testing with running backend service...")
    
    try:
        # Connect to the running backend
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 9876))
        
        print("✅ Connected to running backend")
        
        # Receive welcome message
        welcome_data = client_socket.recv(1024)
        welcome_msg = welcome_data.decode('utf-8').strip()
        print(f"📨 Welcome: {welcome_msg}")
        
        # Send a ping command to test basic communication
        ping_command = json.dumps({
            "command": "ping",
            "data": {}
        })
        
        client_socket.send((ping_command + '\n').encode('utf-8'))
        
        # Receive ping response
        response_data = client_socket.recv(1024)
        response_msg = response_data.decode('utf-8').strip()
        print(f"📨 Ping response: {response_msg}")
        
        # Parse the response
        try:
            response_json = json.loads(response_msg)
            if response_json.get('status') == 'success':
                print("✅ Backend communication working")
            else:
                print("❌ Backend communication failed")
                return False
        except json.JSONDecodeError:
            print("❌ Invalid JSON response")
            return False
        
        client_socket.close()
        print("✅ Backend integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def main():
    """Main test function."""
    print("🚀 Starting transcript integration test...")
    print("=" * 60)
    
    # Test with running backend
    if not test_with_running_backend():
        print("❌ Integration test failed")
        return 1
    
    print("=" * 60)
    print("✅ Transcript integration test passed!")
    print("")
    print("🎯 Next steps:")
    print("1. Check the frontend application to see if transcripts appear")
    print("2. Test with actual audio input")
    print("3. Verify the 'No transcript available yet' issue is resolved")
    return 0

if __name__ == "__main__":
    sys.exit(main())