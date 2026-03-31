#!/usr/bin/env python3

import sys
import os

# Add parent directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

print("Testing Python imports...")

try:
    from loguru import logger
    print("✓ loguru imported successfully")
except ImportError as e:
    print(f"✗ Failed to import loguru: {e}")
    sys.exit(1)

try:
    from backend.utils.logger import get_logger
    print("✓ backend.utils.logger imported successfully")
except ImportError as e:
    print(f"✗ Failed to import backend.utils.logger: {e}")
    sys.exit(1)

try:
    from backend.ipc.ipc_server import IPCServer
    print("✓ backend.ipc.ipc_server imported successfully")
except ImportError as e:
    print(f"✗ Failed to import backend.ipc.ipc_server: {e}")
    sys.exit(1)

print("All imports successful!")