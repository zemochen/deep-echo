"""
Main Window for DeepEcho Real-time Voice AI Assistant.

This module provides the main application window that integrates all UI components
and handles the coordination between audio processing, AI responses, and user interface.
"""

import threading
import queue
import time
import sys
from typing import Optional

# Optional import for testing compatibility
try:
    import customtkinter as ctk
    CUSTOMTKINTER_AVAILABLE = True
except ImportError:
    ctk = None
    CUSTOMTKINTER_AVAILABLE = False

from backend.ui.controller import UIController
from backend.ui.components import AIProviderSelector, StatusIndicator
from backend.ai.adapter import AIAdapter
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class MainWindow:
    """
    Main application window that coordinates all components.
    
    This class manages the main window, integrates UI components,
    and handles communication between different system parts.
    """
    
    def __init__(self):
        """Initialize the main window."""
        self.ui_controller = UIController()
        self.ai_adapter: Optional[AIAdapter] = None
        self.transcriber = None
        self.responder = None
        self.speaker_queue: Optional[queue.Queue] = None
        self.mic_queue: Optional[queue.Queue] = None
        
        # UI update threads
        self.transcript_update_thread: Optional[threading.Thread] = None
        self.response_update_thread: Optional[threading.Thread] = None
        
        self.is_running = False
    
    def initialize(self, transcriber, responder, ai_adapter: AIAdapter, 
                  speaker_queue: queue.Queue, mic_queue: queue.Queue):
        """
        Initialize the main window with system components.
        
        Args:
            transcriber: Audio transcriber instance
            responder: GPT responder instance
            ai_adapter: AI adapter instance
            speaker_queue: Speaker audio queue
            mic_queue: Microphone audio queue
        """
        self.transcriber = transcriber
        self.responder = responder
        self.ai_adapter = ai_adapter
        self.speaker_queue = speaker_queue
        self.mic_queue = mic_queue
        
        # Initialize UI
        root = self.ui_controller.init_ui()
        
        # Create UI components
        self.ui_controller.create_ui_components(transcriber, speaker_queue, mic_queue)
        
        # Set up AI provider selection
        self._setup_ai_provider_integration()
        
        # Set up callbacks
        self._setup_callbacks()
        
        # Update UI with current AI provider info
        self._update_provider_display()
        
        self.ui_controller.update_status("Ready")
        
        return root
    
    def _setup_ai_provider_integration(self):
        """Set up AI provider selection integration."""
        if not self.ai_adapter:
            return
        
        # Set current provider in UI
        provider_name = self.ai_adapter.get_current_provider()
        if provider_name:
            model_name = self.ai_adapter.get_current_model()
            self.ui_controller.set_current_provider(provider_name, model_name)
            
            # Update available models for current provider
            available_models = self._get_available_models(provider_name)
            self.ui_controller.set_ai_provider_models(provider_name, available_models)
    
    def _setup_callbacks(self):
        """Set up UI callbacks."""
        # Clear context callback
        def clear_context_callback():
            self._clear_context()
        self.ui_controller.set_clear_context_callback(clear_context_callback)
        
        # Provider change callback
        def provider_change_callback(provider: str):
            self._on_provider_change(provider)
        self.ui_controller.set_provider_change_callback(provider_change_callback)
        
        # Model change callback
        def model_change_callback(model: str):
            self._on_model_change(model)
        self.ui_controller.set_model_change_callback(model_change_callback)
    
    def _clear_context(self):
        """Clear transcript and audio queues."""
        if self.transcriber:
            self.transcriber.clear_transcript_data()
        
        if self.speaker_queue:
            with self.speaker_queue.mutex:
                self.speaker_queue.queue.clear()
        
        if self.mic_queue:
            with self.mic_queue.mutex:
                self.mic_queue.queue.clear()
        
        self.ui_controller.update_status("Context cleared")
        logger.info("Context cleared by user")
    
    def _on_provider_change(self, provider: str):
        """Handle AI provider change."""
        if not self.ai_adapter:
            self.ui_controller.show_error("AI adapter not available")
            return
        
        try:
            # Get available models for the new provider
            available_models = self._get_available_models(provider)
            self.ui_controller.set_ai_provider_models(provider, available_models)
            
            # Try to create and set the new provider
            # This would require API keys to be available
            self.ui_controller.update_status(f"Switching to {provider}...")
            
            # For now, just update the display
            # In a full implementation, this would create the actual provider
            if available_models:
                self._update_provider_display()
                self.ui_controller.update_status(f"Provider changed to {provider}")
                self.ui_controller.clear_error()
            else:
                self.ui_controller.show_error(f"No models available for {provider}")
            
        except Exception as e:
            error_msg = f"Failed to switch to {provider}: {str(e)}"
            self.ui_controller.show_error(error_msg)
            logger.error(error_msg)
    
    def _on_model_change(self, model: str):
        """Handle model change."""
        if not self.ai_adapter:
            self.ui_controller.show_error("AI adapter not available")
            return
        
        try:
            provider_name = self.ai_adapter.get_current_provider()
            if provider_name:
                self.ui_controller.update_status(f"Switching to {model}...")
                
                # For now, just update the display
                # In a full implementation, this would update the actual model
                self._update_provider_display()
                self.ui_controller.update_status(f"Model changed to {model}")
                self.ui_controller.clear_error()
            
        except Exception as e:
            error_msg = f"Failed to switch to model {model}: {str(e)}"
            self.ui_controller.show_error(error_msg)
            logger.error(error_msg)
    
    def _get_available_models(self, provider: str) -> list[str]:
        """Get available models for a provider."""
        provider_models = {
            "deepseek": ["deepseek-chat", "deepseek-coder"],
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
            "grok": ["grok-beta", "grok-2"],
            "claude": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
            "volcano": ["doubao-pro", "doubao-lite"],
            "glm": ["glm-4", "glm-3-turbo"]
        }
        return provider_models.get(provider, [])
    
    def _update_provider_display(self):
        """Update the provider information display."""
        if self.ai_adapter:
            provider_name = self.ai_adapter.get_current_provider()
            model_name = self.ai_adapter.get_current_model()
            if provider_name and model_name:
                self.ui_controller.update_provider_info()
    
    def start_ui_updates(self):
        """Start UI update loops."""
        if self.is_running:
            return
        
        self.is_running = True
        
        # Start transcript updates
        if self.transcriber and self.ui_controller.transcript_textbox:
            self.ui_controller.update_transcript_ui()
        
        # Start response updates
        if self.responder and self.ui_controller.response_textbox:
            self.ui_controller.update_response_ui(self.responder)
    
    def stop_ui_updates(self):
        """Stop UI update loops."""
        self.is_running = False
    
    def run(self):
        """Run the main window."""
        if not CUSTOMTKINTER_AVAILABLE:
            logger.warning("CustomTkinter not available, cannot run UI")
            return
            
        if not self.ui_controller.root:
            raise RuntimeError("Main window not initialized")
        
        # Start UI updates
        self.start_ui_updates()
        
        # Run the main loop
        self.ui_controller.root.mainloop()
    
    def get_root(self):
        """Get the root window."""
        return self.ui_controller.root
    
    def get_ui_components(self):
        """Get UI components for backward compatibility."""
        return (
            self.ui_controller.transcript_textbox,
            self.ui_controller.response_textbox,
            self.ui_controller.update_interval_slider,
            self.ui_controller.update_interval_label,
            self.ui_controller.freeze_button
        )
    
    def get_freeze_state(self):
        """Get freeze state for backward compatibility."""
        return self.ui_controller.get_freeze_state()
    
    def set_freeze_command(self, command):
        """Set freeze button command for backward compatibility."""
        if self.ui_controller.freeze_button:
            self.ui_controller.freeze_button.configure(command=command)
    
    def cleanup(self):
        """Clean up the main window resources."""
        logger.info("Cleaning up main window...")
        self.stop_ui_updates()
        if hasattr(self.ui_controller, 'cleanup'):
            self.ui_controller.cleanup()


def create_main_window() -> MainWindow:
    """
    Create and return a new main window instance.
    
    Returns:
        MainWindow: New main window instance
    """
    return MainWindow()