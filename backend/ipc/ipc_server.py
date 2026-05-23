"""
IPC Server for Backend Communication.

This module provides a TCP-based IPC server that handles communication
between the Tauri frontend and the Python backend.
"""

import socket
import threading
import json
import logging
from typing import Optional, Set
from datetime import datetime

from backend.utils.logger import get_logger
from backend.ipc.message_handler import MessageHandler
from backend.ipc.event_emitter import EventEmitter, get_event_emitter

logger = get_logger(__name__)


class IPCServer:
    """
    IPC Server for handling frontend-backend communication.
    
    This server listens for incoming connections from the Tauri frontend,
    processes commands, and sends events back to the frontend.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 9876):
        """
        Initialize the IPC server.
        
        Args:
            host: Host address to bind to
            port: Port number to listen on
        """
        self.host = host
        self.port = port
        self.server_socket: Optional[socket.socket] = None
        self.message_handler = MessageHandler()
        self.event_emitter = get_event_emitter()
        
        # Set this server as the event forwarding target
        self.event_emitter.set_ipc_server(self)
        self.message_handler.set_ipc_server(self)
        
        self._is_running = False
        self._accept_thread: Optional[threading.Thread] = None
        self._client_threads: Set[threading.Thread] = set()
        self._clients: Set[socket.socket] = set()
        self._lock = threading.RLock()
        
        logger.info(f"IPC Server initialized on {host}:{port}")
    
    def start(self) -> None:
        """
        Start the IPC server.
        
        This method starts listening for incoming connections and
        begins processing messages.
        """
        if self._is_running:
            logger.warning("IPC server already running")
            return
        
        try:
            # Create server socket
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(5)
            
            self._is_running = True
            
            # Start event emitter
            self.event_emitter.start()
            
            logger.info(f"IPC Server listening on {self.host}:{self.port}")
            
            # Start accepting connections in a separate thread
            self._accept_thread = threading.Thread(
                target=self._accept_connections,
                name="IPCAcceptThread",
                daemon=True
            )
            self._accept_thread.start()
            
            # Keep main thread alive
            self._accept_thread.join()
            
        except Exception as e:
            logger.error(f"Failed to start IPC server: {e}", exc_info=True)
            self.stop()
            raise
    
    def stop(self) -> None:
        """
        Stop the IPC server and cleanup resources.
        """
        if not self._is_running:
            return
        
        logger.info("Stopping IPC server...")
        self._is_running = False
        
        try:
            # Clean up message handler resources
            try:
                self.message_handler.cleanup()
            except Exception as e:
                logger.warning(f"Error cleaning up message handler: {e}")
            
            # Stop event emitter
            self.event_emitter.stop()
            
            # Close all client connections
            with self._lock:
                for client in list(self._clients):
                    try:
                        client.close()
                    except Exception as e:
                        logger.debug(f"Error closing client: {e}")
                
                self._clients.clear()
            
            # Close server socket
            if self.server_socket:
                try:
                    self.server_socket.close()
                except Exception as e:
                    logger.debug(f"Error closing server socket: {e}")
            
            # Wait for threads to finish
            if self._accept_thread:
                self._accept_thread.join(timeout=2.0)
            
            for thread in list(self._client_threads):
                thread.join(timeout=1.0)
            
            logger.info("IPC server stopped")
            
        except Exception as e:
            logger.error(f"Error stopping IPC server: {e}", exc_info=True)
    
    def _accept_connections(self) -> None:
        """
        Accept incoming client connections (runs in background thread).
        """
        logger.info("Started accepting connections")
        
        while self._is_running:
            try:
                # Set timeout to allow checking _is_running flag
                self.server_socket.settimeout(1.0)
                
                try:
                    client_socket, client_address = self.server_socket.accept()
                    logger.info(f"New client connected: {client_address}")
                    
                    # Add client to set
                    with self._lock:
                        self._clients.add(client_socket)
                    
                    # Handle client in separate thread
                    client_thread = threading.Thread(
                        target=self._handle_client,
                        args=(client_socket, client_address),
                        name=f"IPCClientThread-{client_address}",
                        daemon=True
                    )
                    
                    with self._lock:
                        self._client_threads.add(client_thread)
                    
                    client_thread.start()
                    
                except socket.timeout:
                    # Timeout is expected, continue loop
                    continue
                    
            except Exception as e:
                if self._is_running:
                    logger.error(f"Error accepting connection: {e}")
        
        logger.info("Stopped accepting connections")
    
    def _handle_client(self, client_socket: socket.socket, client_address: tuple) -> None:
        """
        Handle a connected client (runs in background thread).
        
        Args:
            client_socket: Client socket
            client_address: Client address tuple
        """
        logger.info(f"Handling client: {client_address}")
        
        try:
            # Set socket timeout
            client_socket.settimeout(30.0)
            
            # Send welcome message
            welcome = json.dumps({
                "type": "welcome",
                "message": "Connected to DeepEcho Backend",
                "timestamp": datetime.utcnow().isoformat()
            })
            self._send_message(client_socket, welcome)
            
            # Process messages from client
            buffer = ""
            
            while self._is_running:
                try:
                    # Receive data
                    data = client_socket.recv(4096)
                    
                    if not data:
                        # Client disconnected
                        logger.info(f"Client disconnected: {client_address}")
                        break
                    
                    # Decode and add to buffer
                    buffer += data.decode('utf-8')
                    
                    # Process complete messages (newline-delimited)
                    while '\n' in buffer:
                        message, buffer = buffer.split('\n', 1)
                        
                        if message.strip():
                            # Handle message
                            response = self.message_handler.handle_message(message)
                            
                            # Send response
                            self._send_message(client_socket, response)
                            
                            # Drain pending events immediately after response
                            # to ensure events arrive AFTER the command response
                            self._send_pending_events(client_socket)
                    
                except socket.timeout:
                    # Send pending events during timeout
                    self._send_pending_events(client_socket)
                    continue
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    break
            
        except Exception as e:
            logger.error(f"Error in client handler: {e}", exc_info=True)
        finally:
            # Cleanup
            with self._lock:
                self._clients.discard(client_socket)
            
            try:
                client_socket.close()
            except Exception:
                pass
            
            logger.info(f"Client handler finished: {client_address}")
    
    def _send_message(self, client_socket: socket.socket, message: str) -> bool:
        """
        Send a message to a client.
        
        Args:
            client_socket: Client socket
            message: Message to send (JSON string)
            
        Returns:
            True if sent successfully, False otherwise
        """
        try:
            # Add newline delimiter
            data = (message + '\n').encode('utf-8')
            client_socket.sendall(data)
            return True
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False
    
    def _send_pending_events(self, client_socket: socket.socket) -> None:
        """
        Send pending events to a client.
        
        Args:
            client_socket: Client socket
        """
        try:
            events = self.event_emitter.get_pending_events(max_events=10)
            
            for event in events:
                event_message = json.dumps(event)
                self._send_message(client_socket, event_message)
                
        except Exception as e:
            logger.error(f"Error sending pending events: {e}")
    
    def broadcast_event(self, event_type: str, data: dict) -> int:
        """
        Broadcast an event to all connected clients.
        
        Args:
            event_type: Type of event
            data: Event data
            
        Returns:
            Number of clients that received the event
        """
        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        event_message = json.dumps(event)
        sent_count = 0
        
        with self._lock:
            for client in list(self._clients):
                if self._send_message(client, event_message):
                    sent_count += 1
        
        return sent_count
    
    def get_connected_clients_count(self) -> int:
        """
        Get the number of connected clients.
        
        Returns:
            Number of connected clients
        """
        with self._lock:
            return len(self._clients)
    
    def is_running(self) -> bool:
        """
        Check if the server is running.
        
        Returns:
            True if running, False otherwise
        """
        return self._is_running
    
    def get_status(self) -> dict:
        """
        Get server status information.
        
        Returns:
            Dictionary with status information
        """
        return {
            "running": self._is_running,
            "host": self.host,
            "port": self.port,
            "connected_clients": self.get_connected_clients_count(),
            "registered_commands": len(self.message_handler.get_registered_commands()),
            "event_queue_size": self.event_emitter.get_queue_size()
        }
