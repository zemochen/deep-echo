"""
IPC (Inter-Process Communication) module for DeepEcho backend.

This module provides IPC communication between the Tauri frontend
and the Python backend service.
"""

from .ipc_server import IPCServer
from .message_handler import MessageHandler

__all__ = ['IPCServer', 'MessageHandler']
