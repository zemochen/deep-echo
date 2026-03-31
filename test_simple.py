#!/usr/bin/env python3

import sys
import os

# Simple test
print("Simple Python test starting...")

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print(f"Added {parent_dir} to sys.path")

# Test basic import
try:
    import loguru
    print("✓ loguru imported")
except ImportError as e:
    print(f"✗ loguru failed: {e}")
    sys.exit(1)

# Test IPC server import
try:
    from backend.ipc.ipc_server import IPCServer
    print("✓ IPCServer imported")
except ImportError as e:
    print(f"✗ IPCServer failed: {e}")
    sys.exit(1)

# Test logger
try:
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
    print("✓ Logger created")
    logger.info("Test log message")
    print("✓ Log message sent")
except Exception as e:
    print(f"✗ Logger failed: {e}")
    import traceback
    traceback.print_exc()

print("Basic tests completed")