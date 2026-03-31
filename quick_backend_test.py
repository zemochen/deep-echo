#!/usr/bin/env python3
"""
Quick Backend Test - Verifies backend can initialize without starting server.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_backend_initialization():
    """Test that backend components can be initialized."""
    print("Testing backend initialization...")
    print("-" * 70)
    
    try:
        # Test imports
        print("1. Testing imports...")
        from backend.backend_service import BackendService
        from backend.ipc.ipc_server import IPCServer
        from backend.ipc.message_handler import MessageHandler
        from backend.ipc.event_emitter import EventEmitter, get_event_emitter
        print("   ✓ All imports successful")
        
        # Test EventEmitter initialization
        print("2. Testing EventEmitter initialization...")
        event_emitter = get_event_emitter()
        assert event_emitter is not None
        print("   ✓ EventEmitter initialized")
        
        # Test MessageHandler initialization
        print("3. Testing MessageHandler initialization...")
        message_handler = MessageHandler()
        commands = message_handler.get_registered_commands()
        print(f"   ✓ MessageHandler initialized with {len(commands)} commands")
        print(f"   Commands: {', '.join(commands)}")
        
        # Test BackendService initialization
        print("4. Testing BackendService initialization...")
        service = BackendService(host="127.0.0.1", port=9876)
        print("   ✓ BackendService initialized")
        
        # Test configuration loading
        print("5. Testing configuration loading...")
        from backend.config.config_manager import get_config_manager
        config_manager = get_config_manager()
        config = config_manager.get_current_config()
        print(f"   ✓ Configuration loaded: Provider={config.ai_provider.provider_type}")
        
        print("-" * 70)
        print("✓ All initialization tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Initialization test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    print("=" * 70)
    print("Quick Backend Initialization Test")
    print("=" * 70)
    print()
    
    success = test_backend_initialization()
    
    print()
    if success:
        print("=" * 70)
        print("✓ Backend components are ready for testing")
        print("=" * 70)
        sys.exit(0)
    else:
        print("=" * 70)
        print("✗ Backend initialization failed")
        print("=" * 70)
        sys.exit(1)


if __name__ == "__main__":
    main()
