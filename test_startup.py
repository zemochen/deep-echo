#!/usr/bin/env python3
"""
Quick startup test to verify application can initialize.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing imports...")
    try:
        from src.integration import IntegratedDeepEchoApplication
        from src.utils.queue_manager import QueueManager, QueueType
        from src.utils.threading import ThreadManager
        from src.utils.resource_optimizer import ResourceOptimizer
        from src.audio.recorder import DefaultMicRecorder, DefaultSpeakerRecorder
        from src.audio.transcriber import AudioTranscriber
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False

def test_queue_manager():
    """Test QueueManager methods."""
    print("\nTesting QueueManager...")
    try:
        from src.utils.queue_manager import QueueManager, QueueType
        qm = QueueManager()
        
        # Test create_queue
        q = qm.create_queue("test_queue", maxsize=100, queue_type=QueueType.FIFO)
        print(f"✓ create_queue works: {q}")
        
        # Test stop_all_queues
        qm.stop_all_queues()
        print("✓ stop_all_queues works")
        
        return True
    except Exception as e:
        print(f"✗ QueueManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_thread_manager():
    """Test ThreadManager methods."""
    print("\nTesting ThreadManager...")
    try:
        from src.utils.threading import ThreadManager
        tm = ThreadManager()
        
        # Test stop_all_threads
        tm.stop_all_threads(timeout=1.0)
        print("✓ stop_all_threads works")
        
        return True
    except Exception as e:
        print(f"✗ ThreadManager test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_resource_optimizer():
    """Test ResourceOptimizer methods."""
    print("\nTesting ResourceOptimizer...")
    try:
        from src.utils.resource_optimizer import ResourceOptimizer
        ro = ResourceOptimizer()
        
        # Test stop
        ro.stop()
        print("✓ stop works")
        
        return True
    except Exception as e:
        print(f"✗ ResourceOptimizer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recorder_configure():
    """Test recorder configure method."""
    print("\nTesting Recorder configure...")
    try:
        from src.audio.recorder import BaseRecorder
        import custom_speech_recognition as sr
        
        # Check if configure method exists
        assert hasattr(BaseRecorder, 'configure'), "BaseRecorder missing configure method"
        print("✓ BaseRecorder has configure method")
        
        return True
    except Exception as e:
        print(f"✗ Recorder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("DeepEcho Startup Test Suite")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_queue_manager,
        test_thread_manager,
        test_resource_optimizer,
        test_recorder_configure,
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    return all(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
