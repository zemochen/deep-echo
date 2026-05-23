"""
Event Emitter for IPC Communication.

This module provides event emission functionality to send events from the
Python backend to the Tauri frontend.
"""

import json
import logging
import threading
from typing import Dict, Any, List, Callable, Optional
from datetime import datetime
from queue import Queue, Empty

from backend.utils.logger import get_logger

logger = get_logger(__name__)


class EventEmitter:
    """
    Event emitter for sending events from backend to frontend.
    
    This class manages event emission, event queuing, and event delivery
    to connected clients (Tauri frontend).
    """
    
    def __init__(self):
        """Initialize the event emitter."""
        self._event_queue: Queue = Queue(maxsize=1000)
        self._listeners: Dict[str, List[Callable]] = {}
        self._is_running = False
        self._processing_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        self._ipc_server: Optional[Any] = None  # Reference to IPC server for forwarding
        
        logger.info("Event emitter initialized")
    
    def set_ipc_server(self, ipc_server: Any) -> None:
        """
        Set the IPC server reference for event forwarding.
        
        Args:
            ipc_server: IPC server instance
        """
        self._ipc_server = ipc_server
        logger.info("IPC server reference set for event forwarding")
    
    def start(self) -> None:
        """Start the event emitter processing thread."""
        if self._is_running:
            logger.warning("Event emitter already running")
            return
        
        self._is_running = True
        self._processing_thread = threading.Thread(
            target=self._process_events,
            name="EventEmitterThread",
            daemon=True
        )
        self._processing_thread.start()
        logger.info("Event emitter started")
    
    def stop(self) -> None:
        """Stop the event emitter processing thread."""
        if not self._is_running:
            return
        
        logger.info("Stopping event emitter...")
        self._is_running = False
        
        if self._processing_thread:
            self._processing_thread.join(timeout=2.0)
        
        logger.info("Event emitter stopped")
    
    def emit(self, event_type: str, data: Any) -> bool:
        """
        Emit an event to the frontend.
        
        Args:
            event_type: Type of event (e.g., "transcript-updated")
            data: Event data
            
        Returns:
            True if event was queued successfully, False otherwise
        """
        try:
            event = {
                "type": event_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Add to queue for processing
            self._event_queue.put_nowait(event)
            logger.debug(f"Event emitted: {event_type}")
            
            # Notify local listeners (but don't forward to IPC here to avoid duplication)
            self._notify_listeners(event_type, data)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}")
            return False
    
    def emit_transcript_updated(self, transcript_data: Dict[str, Any]) -> bool:
        """
        Emit a transcript-updated event.
        
        Args:
            transcript_data: Transcript data
            
        Returns:
            True if event was emitted successfully
        """
        return self.emit("transcript-updated", transcript_data)
    
    def emit_response_generated(self, response_data: Dict[str, Any]) -> bool:
        """
        Emit a response-generated event.
        
        Args:
            response_data: Response data
            
        Returns:
            True if event was emitted successfully
        """
        return self.emit("response-generated", response_data)
    
    def emit_status_changed(self, status_data: Dict[str, Any]) -> bool:
        """
        Emit a status-changed event.
        
        Args:
            status_data: Status data
            
        Returns:
            True if event was emitted successfully
        """
        return self.emit("status-changed", status_data)
    
    def emit_error_occurred(self, error_data: Dict[str, Any]) -> bool:
        """
        Emit an error-occurred event.
        
        Args:
            error_data: Error data
            
        Returns:
            True if event was emitted successfully
        """
        return self.emit("error-occurred", error_data)
    
    def emit_config_updated(self, config_data: Dict[str, Any]) -> bool:
        """
        Emit a config-updated event.
        
        Args:
            config_data: Configuration data
            
        Returns:
            True if event was emitted successfully
        """
        return self.emit("config-updated", config_data)
    
    def emit_audio_started(self) -> bool:
        """
        Emit an audio-started event.
        
        Returns:
            True if event was emitted successfully
        """
        return self.emit("audio-started", {})
    
    def emit_audio_stopped(self) -> bool:
        """
        Emit an audio-stopped event.
        
        Returns:
            True if event was emitted successfully
        """
        return self.emit("audio-stopped", {})
    
    def add_listener(self, event_type: str, callback: Callable) -> None:
        """
        Add a listener for a specific event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Callback function to invoke when event occurs
        """
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            
            self._listeners[event_type].append(callback)
            logger.debug(f"Added listener for event: {event_type}")
    
    def remove_listener(self, event_type: str, callback: Callable) -> bool:
        """
        Remove a listener for a specific event type.
        
        Args:
            event_type: Type of event
            callback: Callback function to remove
            
        Returns:
            True if listener was removed, False otherwise
        """
        with self._lock:
            if event_type in self._listeners:
                try:
                    self._listeners[event_type].remove(callback)
                    logger.debug(f"Removed listener for event: {event_type}")
                    return True
                except ValueError:
                    pass
        
        return False
    
    def _notify_listeners(self, event_type: str, data: Any) -> None:
        """
        Notify all listeners for a specific event type.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        with self._lock:
            listeners = self._listeners.get(event_type, [])
            
            for callback in listeners:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_type}: {e}")
    
    def _process_events(self) -> None:
        """
        Event processing thread - keeps the thread alive for lifecycle
        management. Events are consumed by client handler threads via
        _send_pending_events to avoid race conditions with command responses.
        """
        logger.info("Event processing thread started")
        
        while self._is_running:
            threading.Event().wait(0.5)
        
        logger.info("Event processing thread stopped")
    
    def _forward_event(self, event: Dict[str, Any]) -> None:
        """
        Forward an event to connected clients.
        
        Args:
            event: Event to forward
        """
        logger.debug(f"Forwarding event: {event['type']}")
        
        # Forward to IPC server if available
        if self._ipc_server:
            try:
                # Broadcast event to all connected clients
                sent_count = self._ipc_server.broadcast_event(event['type'], event['data'])
                if sent_count > 0:
                    logger.debug(f"Event forwarded to {sent_count} client(s)")
            except Exception as e:
                logger.error(f"Failed to forward event to IPC server: {e}")
    
    def get_pending_events(self, max_events: int = 10) -> List[Dict[str, Any]]:
        """
        Get pending events from the queue without blocking.
        
        Args:
            max_events: Maximum number of events to retrieve
            
        Returns:
            List of pending events
        """
        events = []
        
        try:
            for _ in range(max_events):
                event = self._event_queue.get_nowait()
                events.append(event)
        except Empty:
            pass
        
        return events
    
    def clear_events(self) -> int:
        """
        Clear all pending events from the queue.
        
        Returns:
            Number of events cleared
        """
        count = 0
        
        try:
            while True:
                self._event_queue.get_nowait()
                count += 1
        except Empty:
            pass
        
        if count > 0:
            logger.info(f"Cleared {count} pending events")
        
        return count
    
    def get_queue_size(self) -> int:
        """
        Get the current size of the event queue.
        
        Returns:
            Number of events in queue
        """
        return self._event_queue.qsize()
    
    def is_running(self) -> bool:
        """
        Check if the event emitter is running.
        
        Returns:
            True if running, False otherwise
        """
        return self._is_running


# Global event emitter instance
_event_emitter: Optional[EventEmitter] = None


def get_event_emitter() -> EventEmitter:
    """
    Get the global event emitter instance.
    
    Returns:
        Global EventEmitter instance
    """
    global _event_emitter
    if _event_emitter is None:
        _event_emitter = EventEmitter()
    return _event_emitter
