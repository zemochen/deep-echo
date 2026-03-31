#!/usr/bin/env python3
"""
Simple test script to verify transcription functionality.
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add backend to path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from backend.utils.logger import get_logger
from backend.ipc.event_emitter import get_event_emitter

logger = get_logger(__name__)

def test_event_emission():
    """Test event emission functionality."""
    print("🧪 Testing event emission...")
    
    # Get event emitter
    event_emitter = get_event_emitter()
    
    # Test transcript-updated event
    test_transcript = {
        "id": "test_transcript_1",
        "timestamp": "2025-01-28T23:40:00Z",
        "source": "microphone",
        "text": "Hello, this is a test transcript",
        "confidence": 0.95
    }
    
    print(f"📤 Emitting transcript-updated event: {test_transcript['text']}")
    
    try:
        event_emitter.emit_transcript_updated(test_transcript)
        print("✅ Event emitted successfully")
    except Exception as e:
        print(f"❌ Failed to emit event: {e}")
        return False
    
    return True

def main():
    """Main test function."""
    print("🚀 Starting transcription test...")
    print("=" * 50)
    
    # Test 1: Event emission
    if not test_event_emission():
        print("❌ Event emission test failed")
        return 1
    
    print("=" * 50)
    print("✅ All tests passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())