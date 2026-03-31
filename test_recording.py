#!/usr/bin/env python3
"""
Test recording functionality with the running backend.
"""

import sys
import os
import time
import socket
import json

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

def test_recording():
    """Test recording commands with the running backend."""
    print("🧪 Testing recording functionality...")
    
    try:
        # Connect to the running backend
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(("127.0.0.1", 9876))
        client_socket.settimeout(5.0)
        
        print("✅ Connected to backend")
        
        # Receive welcome message
        welcome_data = client_socket.recv(1024)
        print(f"📨 Welcome: {welcome_data.decode('utf-8').strip()}")
        
        # Test 1: Start recording
        print("\n📤 Sending start_recording command...")
        start_command = json.dumps({
            "command": "start_recording",
            "data": {
                "device_type": "microphone"
            }
        })
        
        client_socket.send((start_command + '\n').encode('utf-8'))
        
        # Receive response
        response_data = client_socket.recv(4096)
        response_msg = response_data.decode('utf-8').strip()
        print(f"📨 Response: {response_msg}")
        
        # Parse response
        try:
            response_json = json.loads(response_msg)
            if response_json.get('status') == 'success':
                print("✅ Recording started successfully")
                data = response_json.get('data', {})
                print(f"   Device: {data.get('device_type')}")
                print(f"   Status: {data.get('status')}")
            else:
                print(f"❌ Recording failed: {response_json.get('error', 'Unknown error')}")
                return False
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON response: {e}")
            print(f"   Raw response: {response_msg}")
            return False
        
        # Wait a bit
        print("\n⏳ Waiting 3 seconds...")
        time.sleep(3)
        
        # Test 2: Get transcript
        print("\n📤 Sending get_transcript command...")
        transcript_command = json.dumps({
            "command": "get_transcript",
            "data": {}
        })
        
        client_socket.send((transcript_command + '\n').encode('utf-8'))
        
        # Receive response
        response_data = client_socket.recv(4096)
        response_msg = response_data.decode('utf-8').strip()
        print(f"📨 Response: {response_msg[:200]}...")
        
        # Test 3: Stop recording
        print("\n📤 Sending stop_recording command...")
        stop_command = json.dumps({
            "command": "stop_recording",
            "data": {}
        })
        
        client_socket.send((stop_command + '\n').encode('utf-8'))
        
        # Receive response
        response_data = client_socket.recv(4096)
        response_msg = response_data.decode('utf-8').strip()
        print(f"📨 Response: {response_msg}")
        
        # Parse response
        try:
            response_json = json.loads(response_msg)
            if response_json.get('status') == 'success':
                print("✅ Recording stopped successfully")
            else:
                print(f"⚠️ Stop recording response: {response_json}")
        except json.JSONDecodeError:
            print(f"⚠️ Raw stop response: {response_msg}")
        
        client_socket.close()
        print("\n✅ Recording test completed")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Starting recording functionality test...")
    print("=" * 60)
    
    if not test_recording():
        print("❌ Recording test failed")
        return 1
    
    print("=" * 60)
    print("✅ All recording tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())