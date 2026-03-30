#!/usr/bin/env python3
"""
Start Backend Service for Testing.

This script starts the backend service in a way that's easy to test.
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.backend_service import main

if __name__ == "__main__":
    print("Starting Backend Service for Testing...")
    print("Press Ctrl+C to stop")
    print()
    main()
