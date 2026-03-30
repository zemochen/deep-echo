#!/usr/bin/env python3
"""
Verification script for Task 17: Backend Component Adaptation

This script tests all adapted backend components through the IPC message handler.
"""

import json
import sys
from backend.ipc.message_handler import MessageHandler


def test_command(handler, command_name, params, description):
    """Test a single command and print results."""
    print(f"\n{'='*60}")
    print(f"Testing: {description}")
    print(f"{'='*60}")
    
    request = json.dumps({
        'command': command_name,
        'params': params,
        'id': f'test-{command_name}'
    })
    
    print(f"Request: {command_name}")
    print(f"Params: {json.dumps(params, indent=2)}")
    
    response = handler.handle_message(request)
    response_data = json.loads(response)
    
    print(f"\nResponse Status: {response_data.get('status')}")
    
    if response_data.get('status') == 'success':
        print("✅ SUCCESS")
        data = response_data.get('data', {})
        
        # Print relevant data based on command
        if command_name == 'get_audio_devices':
            print(f"  Microphones: {len(data.get('microphones', []))}")
            print(f"  Speakers: {len(data.get('speakers', []))}")
        elif command_name == 'get_config':
            print(f"  AI Provider: {data.get('ai', {}).get('provider')}")
            print(f"  AI Model: {data.get('ai', {}).get('model')}")
            print(f"  Whisper Model: {data.get('audio', {}).get('whisperModel')}")
        elif command_name == 'get_transcript':
            print(f"  Transcript Length: {len(data.get('transcript', ''))}")
            print(f"  Entries: {len(data.get('entries', []))}")
        elif command_name == 'ping':
            print(f"  Message: {data.get('message')}")
        else:
            print(f"  Data: {json.dumps(data, indent=2)[:200]}...")
    else:
        print("❌ ERROR")
        print(f"  Error: {response_data.get('error')}")
    
    return response_data.get('status') == 'success'


def main():
    """Run all verification tests."""
    print("="*60)
    print("Task 17 Verification: Backend Component Adaptation")
    print("="*60)
    
    # Create message handler
    print("\nInitializing message handler...")
    handler = MessageHandler()
    print(f"✅ Message handler initialized")
    print(f"   Registered commands: {len(handler.get_registered_commands())}")
    
    results = []
    
    # Test 1: Ping (basic connectivity)
    results.append(test_command(
        handler, 'ping', {},
        "Basic IPC Communication (Ping)"
    ))
    
    # Test 2: Get system info
    results.append(test_command(
        handler, 'get_system_info', {},
        "System Information Retrieval"
    ))
    
    # Test 3: Get audio devices (17.1)
    results.append(test_command(
        handler, 'get_audio_devices', {},
        "Audio Device Enumeration (Task 17.1)"
    ))
    
    # Test 4: Get configuration (17.4)
    results.append(test_command(
        handler, 'get_config', {},
        "Configuration Retrieval (Task 17.4)"
    ))
    
    # Test 5: Get transcript (17.2)
    results.append(test_command(
        handler, 'get_transcript', {},
        "Transcript Retrieval (Task 17.2)"
    ))
    
    # Test 6: Update config (17.4)
    results.append(test_command(
        handler, 'update_config', {
            'config': {
                'ui': {
                    'updateInterval': 10
                }
            }
        },
        "Configuration Update (Task 17.4)"
    ))
    
    # Test 7: Clear transcript (17.2)
    results.append(test_command(
        handler, 'clear_transcript', {},
        "Transcript Clearing (Task 17.2)"
    ))
    
    # Cleanup
    print(f"\n{'='*60}")
    print("Cleanup")
    print(f"{'='*60}")
    handler.cleanup()
    print("✅ Cleanup completed successfully")
    
    # Summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n✅ All tests passed!")
        return 0
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
