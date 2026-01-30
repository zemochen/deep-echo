"""
Backend Service Entry Point for DeepEcho.

This module serves as the main entry point for the Python backend service
that communicates with Tauri frontend via IPC (Inter-Process Communication).
"""

import sys
import os
import signal
import logging
import argparse
from typing import Optional
from pathlib import Path

# Add parent directory to Python path for imports
# This allows the file to be run from any location
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from backend.utils.logger import get_logger
from backend.config.config_manager import get_config_manager
from backend.ipc.ipc_server import IPCServer

logger = get_logger(__name__)


class BackendService:
    """
    Main backend service class that manages the IPC server and core components.
    
    This service initializes and manages:
    - IPC communication server
    - Audio recording and transcription
    - AI response generation
    - Configuration management
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9876):
        """
        Initialize the backend service.
        
        Args:
            host: Host address for IPC server
            port: Port number for IPC server
        """
        self.host = host
        self.port = port
        self.ipc_server: Optional[IPCServer] = None
        self._is_running = False
        
        logger.info(f"Initializing Backend Service on {host}:{port}")
    
    def initialize(self) -> bool:
        """
        Initialize all backend components.
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info("Initializing backend components...")
            
            # Load configuration
            config_manager = get_config_manager()
            config = config_manager.load_config()
            logger.info(f"Configuration loaded: Provider={config.ai_provider.provider_type}")
            
            # Initialize IPC server
            self.ipc_server = IPCServer(host=self.host, port=self.port)
            logger.info("IPC server initialized")
            
            # Register signal handlers for graceful shutdown
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
            
            logger.info("Backend service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize backend service: {e}", exc_info=True)
            return False
    
    def start(self) -> None:
        """
        Start the backend service.
        
        This method starts the IPC server and begins listening for
        commands from the Tauri frontend.
        """
        if not self.ipc_server:
            logger.error("IPC server not initialized. Call initialize() first.")
            return
        
        try:
            logger.info("Starting backend service...")
            self._is_running = True
            
            # Start IPC server (blocking call)
            self.ipc_server.start()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop()
        except Exception as e:
            logger.error(f"Error in backend service: {e}", exc_info=True)
            self.stop()
    
    def stop(self) -> None:
        """
        Stop the backend service and cleanup resources.
        """
        if not self._is_running:
            return
        
        logger.info("Stopping backend service...")
        self._is_running = False
        
        try:
            # Stop IPC server
            if self.ipc_server:
                self.ipc_server.stop()
                logger.info("IPC server stopped")
            
            logger.info("Backend service stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping backend service: {e}", exc_info=True)
    
    def _signal_handler(self, signum, frame):
        """
        Handle system signals for graceful shutdown.
        
        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.stop()
        sys.exit(0)
    
    def is_running(self) -> bool:
        """
        Check if the service is currently running.
        
        Returns:
            True if service is running, False otherwise
        """
        return self._is_running


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="DeepEcho Backend Service - IPC Server for Tauri Frontend"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address for IPC server (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=9876,
        help="Port number for IPC server (default: 9876)"
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--config-dir",
        type=str,
        default=None,
        help="Configuration directory path (default: ~/.deepecho)"
    )
    
    return parser.parse_args()


def main():
    """
    Main entry point for the backend service.
    """
    print("Starting DeepEcho Backend Service...")

    # Parse command line arguments
    args = parse_arguments()
    print(f"Args parsed: host={args.host}, port={args.port}, level={args.log_level}")
    
    # Configure logging level (loguru-based)
    from backend.utils.logger import set_log_level
    set_log_level(args.log_level)
    
    logger.info("=" * 60)
    logger.info("DeepEcho Backend Service")
    logger.info("=" * 60)
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Log Level: {args.log_level}")
    if args.config_dir:
        logger.info(f"Config Directory: {args.config_dir}")
    logger.info("=" * 60)
    
    print("Creating backend service...")
    service = BackendService(host=args.host, port=args.port)

    print("Initializing backend service...")
    if not service.initialize():
        logger.error("Failed to initialize backend service. Exiting.")
        sys.exit(1)

    print("Starting backend service...")
    # Start the service (blocking)
    try:
        service.start()
    except Exception as e:
        logger.error(f"Fatal error in backend service: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
