"""
Main entry point for DeepEcho Real-time Voice AI Assistant.

This module provides the main application startup logic with improved
initialization, dependency validation, and configuration management.
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.utils.logger import get_logger

logger = get_logger(__name__)


def parse_arguments():
    """Parse command line arguments."""
    args = {
        'use_api': '--api' in sys.argv,
        'use_integrated': '--integrated' in sys.argv,
        'verbose': '--verbose' in sys.argv or '-v' in sys.argv,
        'help': '--help' in sys.argv or '-h' in sys.argv
    }
    return args


def show_help():
    """Show help message."""
    help_text = """
DeepEcho Real-time Voice AI Assistant

Usage: python main.py [options]

Options:
  --api              Use API mode for transcription (more accurate, requires internet)
  --integrated       Use integrated application with full component management (default)
  --verbose, -v      Enable verbose logging
  --help, -h         Show this help message

Examples:
  python main.py                    # Run with integrated application (default)
  python main.py --api             # Use API transcription mode
  python main.py --verbose         # Enable verbose logging
"""
    print(help_text)


def main():
    """Main entry point."""
    args = parse_arguments()
    
    if args['help']:
        show_help()
        return 0
    
    # Configure logging level
    if args['verbose']:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)
    
    # Always use integrated application
    print("Starting DeepEcho Real-time Voice AI Assistant...")
    try:
        from backend.integration import run_integrated_application
        return run_integrated_application()
    except ImportError as e:
        logger.error(f"Failed to import integrated application: {e}")
        print(f"ERROR: Failed to start application: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
