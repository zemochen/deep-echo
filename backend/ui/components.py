"""
UI Components for DeepEcho Real-time Voice AI Assistant.

This module provides reusable UI components and widgets used throughout
the application interface.
"""

# Optional import for testing compatibility
try:
    import customtkinter as ctk
    CUSTOMTKINTER_AVAILABLE = True
except ImportError:
    ctk = None
    CUSTOMTKINTER_AVAILABLE = False

from typing import List, Optional, Callable, Dict, Any
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# Mock classes for testing when customtkinter is not available
if not CUSTOMTKINTER_AVAILABLE:
    class MockCTkFrame:
        def __init__(self, *args, **kwargs):
            pass
        def pack(self, *args, **kwargs):
            pass
        def grid(self, *args, **kwargs):
            pass
        def place(self, *args, **kwargs):
            pass
        def configure(self, *args, **kwargs):
            pass
    
    class MockCTkTextbox:
        def __init__(self, *args, **kwargs):
            pass
        def insert(self, *args, **kwargs):
            pass
        def delete(self, *args, **kwargs):
            pass
        def get(self, *args, **kwargs):
            return ""
        def configure(self, *args, **kwargs):
            pass
    
    # Replace ctk classes with mock classes
    if ctk is None:
        class ctk:
            CTkFrame = MockCTkFrame
            CTkTextbox = MockCTkTextbox


class AIProviderSelector(ctk.CTkFrame):
    """
    AI Provider selection component with provider and model dropdowns.
    
    This component handles AI provider selection and model configuration
    with validation feedback.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the AI provider selector.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(parent, **kwargs)
        
        self.provider_change_callback: Optional[Callable] = None
        self.model_change_callback: Optional[Callable] = None
        
        # Available providers and their models
        self.provider_models = {
            "deepseek": ["deepseek-chat", "deepseek-coder"],
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
            "grok": ["grok-beta", "grok-2"],
            "claude": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
            "volcano": ["doubao-pro", "doubao-lite"],
            "glm": ["glm-4", "glm-3-turbo"]
        }
        
        self.current_provider = "deepseek"
        self.current_model = "deepseek-chat"
        
        self._create_components()
    
    def _create_components(self):
        """Create the provider selector components."""
        self.grid_columnconfigure(0, weight=1)
        
        # Provider selection
        provider_label = ctk.CTkLabel(self, text="AI Provider:", font=("Arial", 12))
        provider_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.provider_dropdown = ctk.CTkComboBox(
            self,
            values=list(self.provider_models.keys()),
            command=self._on_provider_change,
            width=300
        )
        self.provider_dropdown.set(self.current_provider)
        self.provider_dropdown.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Model selection
        model_label = ctk.CTkLabel(self, text="Model:", font=("Arial", 12))
        model_label.grid(row=2, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.model_dropdown = ctk.CTkComboBox(
            self,
            values=self.provider_models[self.current_provider],
            command=self._on_model_change,
            width=300
        )
        self.model_dropdown.set(self.current_model)
        self.model_dropdown.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Validation feedback
        self.validation_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 10),
            text_color="#FF6B6B"
        )
        self.validation_label.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="ew")
    
    def _on_provider_change(self, provider: str):
        """Handle provider selection change."""
        self.current_provider = provider
        
        # Update model dropdown with new provider's models
        models = self.provider_models.get(provider, [])
        self.model_dropdown.configure(values=models)
        
        if models:
            self.current_model = models[0]
            self.model_dropdown.set(self.current_model)
        
        # Clear validation message
        self.validation_label.configure(text="")
        
        # Call callback if set
        if self.provider_change_callback:
            self.provider_change_callback(provider)
        
        logger.info(f"Provider changed to: {provider}")
    
    def _on_model_change(self, model: str):
        """Handle model selection change."""
        self.current_model = model
        
        # Clear validation message
        self.validation_label.configure(text="")
        
        # Call callback if set
        if self.model_change_callback:
            self.model_change_callback(model)
        
        logger.info(f"Model changed to: {model}")
    
    def set_provider_change_callback(self, callback: Callable):
        """Set callback for provider changes."""
        self.provider_change_callback = callback
    
    def set_model_change_callback(self, callback: Callable):
        """Set callback for model changes."""
        self.model_change_callback = callback
    
    def get_current_selection(self) -> tuple[str, str]:
        """Get current provider and model selection."""
        return self.current_provider, self.current_model
    
    def set_current_selection(self, provider: str, model: str):
        """Set current provider and model selection."""
        if provider in self.provider_models:
            self.current_provider = provider
            self.provider_dropdown.set(provider)
            
            # Update model dropdown
            models = self.provider_models[provider]
            self.model_dropdown.configure(values=models)
            
            if model in models:
                self.current_model = model
                self.model_dropdown.set(model)
            elif models:
                self.current_model = models[0]
                self.model_dropdown.set(models[0])
    
    def show_validation_error(self, message: str):
        """Show validation error message."""
        self.validation_label.configure(text=message, text_color="#FF6B6B")
    
    def show_validation_success(self, message: str):
        """Show validation success message."""
        self.validation_label.configure(text=message, text_color="#4CAF50")
    
    def clear_validation(self):
        """Clear validation message."""
        self.validation_label.configure(text="")


class StatusIndicator(ctk.CTkFrame):
    """
    Status indicator component showing system status and error messages.
    
    This component provides visual feedback about system status, errors,
    and current configuration.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the status indicator.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(parent, **kwargs)
        
        self.status_message = "Ready"
        self.error_message = ""
        self.provider_info = "Provider: Not configured"
        
        self._create_components()
    
    def _create_components(self):
        """Create the status indicator components."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        
        # Status message
        self.status_label = ctk.CTkLabel(
            self,
            text=self.status_message,
            font=("Arial", 10),
            text_color="#FFFCF2"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Provider info
        self.provider_label = ctk.CTkLabel(
            self,
            text=self.provider_info,
            font=("Arial", 10),
            text_color="#639cdc"
        )
        self.provider_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # Error message (initially hidden)
        self.error_label = ctk.CTkLabel(
            self,
            text="",
            font=("Arial", 10),
            text_color="#FF6B6B",
            wraplength=400
        )
        self.error_label.grid(row=1, column=0, columnspan=2, padx=10, pady=0, sticky="ew")
    
    def update_status(self, message: str):
        """Update the status message."""
        self.status_message = message
        self.status_label.configure(text=message)
        logger.debug(f"Status updated: {message}")
    
    def update_provider_info(self, provider: str, model: str):
        """Update the provider information."""
        self.provider_info = f"Provider: {provider} | Model: {model}"
        self.provider_label.configure(text=self.provider_info)
    
    def show_error(self, message: str):
        """Show an error message."""
        self.error_message = message
        self.error_label.configure(text=f"Error: {message}")
        logger.error(f"UI Error displayed: {message}")
    
    def clear_error(self):
        """Clear the error message."""
        self.error_message = ""
        self.error_label.configure(text="")


class ControlPanel(ctk.CTkFrame):
    """
    Control panel component with freeze button and update interval controls.
    
    This component provides user controls for managing display updates
    and response generation intervals.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the control panel.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments for CTkFrame
        """
        super().__init__(parent, **kwargs)
        
        self.freeze_state = [False]
        self.update_interval = 2
        self.freeze_callback: Optional[Callable] = None
        self.interval_change_callback: Optional[Callable] = None
        
        self._create_components()
    
    def _create_components(self):
        """Create the control panel components."""
        self.grid_columnconfigure(0, weight=1)
        
        # Freeze button
        self.freeze_button = ctk.CTkButton(
            self,
            text="Freeze",
            command=self._on_freeze_toggle
        )
        self.freeze_button.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        # Update interval label
        self.interval_label = ctk.CTkLabel(
            self,
            text=f"Update interval: {self.update_interval} seconds",
            font=("Arial", 12),
            text_color="#FFFCF2"
        )
        self.interval_label.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        # Update interval slider
        self.interval_slider = ctk.CTkSlider(
            self,
            from_=1,
            to=10,
            width=300,
            height=20,
            number_of_steps=9,
            command=self._on_interval_change
        )
        self.interval_slider.set(self.update_interval)
        self.interval_slider.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
    
    def _on_freeze_toggle(self):
        """Handle freeze button toggle."""
        self.freeze_state[0] = not self.freeze_state[0]
        self.freeze_button.configure(text="Unfreeze" if self.freeze_state[0] else "Freeze")
        
        if self.freeze_callback:
            self.freeze_callback(self.freeze_state[0])
        
        logger.info(f"Display {'frozen' if self.freeze_state[0] else 'unfrozen'}")
    
    def _on_interval_change(self, value: float):
        """Handle interval slider change."""
        self.update_interval = int(value)
        self.interval_label.configure(text=f"Update interval: {self.update_interval} seconds")
        
        if self.interval_change_callback:
            self.interval_change_callback(self.update_interval)
        
        logger.debug(f"Update interval changed to: {self.update_interval} seconds")
    
    def set_freeze_callback(self, callback: Callable):
        """Set callback for freeze state changes."""
        self.freeze_callback = callback
    
    def set_interval_change_callback(self, callback: Callable):
        """Set callback for interval changes."""
        self.interval_change_callback = callback
    
    def get_freeze_state(self) -> List[bool]:
        """Get current freeze state."""
        return self.freeze_state
    
    def get_update_interval(self) -> int:
        """Get current update interval."""
        return self.update_interval
    
    def set_freeze_state(self, frozen: bool):
        """Set freeze state programmatically."""
        self.freeze_state[0] = frozen
        self.freeze_button.configure(text="Unfreeze" if frozen else "Freeze")


class TranscriptDisplay(ctk.CTkTextbox):
    """
    Enhanced transcript display component.
    
    This component provides an improved transcript display with better
    formatting and user interaction capabilities.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the transcript display.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments for CTkTextbox
        """
        # Set default styling
        default_kwargs = {
            "font": ("Arial", 12),
            "text_color": "#FFFCF2",
            "wrap": "word"
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self.last_update_time = 0
        self.auto_scroll = True
    
    def update_transcript(self, transcript_text: str):
        """
        Update the transcript display with new text.
        
        Args:
            transcript_text: New transcript text to display
        """
        # Store current scroll position
        current_position = self.yview()
        
        # Update content
        self.delete("0.0", "end")
        self.insert("0.0", transcript_text)
        
        # Auto-scroll to bottom if user was at bottom
        if self.auto_scroll and current_position[1] >= 0.9:
            self.see("end")
    
    def set_auto_scroll(self, enabled: bool):
        """Enable or disable auto-scrolling."""
        self.auto_scroll = enabled


class ResponseDisplay(ctk.CTkTextbox):
    """
    Enhanced response display component.
    
    This component provides an improved AI response display with better
    formatting and state management.
    """
    
    def __init__(self, parent, **kwargs):
        """
        Initialize the response display.
        
        Args:
            parent: Parent widget
            **kwargs: Additional arguments for CTkTextbox
        """
        # Set default styling
        default_kwargs = {
            "font": ("Arial", 12),
            "text_color": "#639cdc",
            "wrap": "word",
            "state": "disabled"
        }
        default_kwargs.update(kwargs)
        
        super().__init__(parent, **default_kwargs)
        
        self.last_response = ""
    
    def update_response(self, response_text: str):
        """
        Update the response display with new text.
        
        Args:
            response_text: New response text to display
        """
        if response_text != self.last_response:
            self.configure(state="normal")
            self.delete("0.0", "end")
            self.insert("0.0", response_text)
            self.configure(state="disabled")
            self.last_response = response_text
    
    def clear_response(self):
        """Clear the response display."""
        self.configure(state="normal")
        self.delete("0.0", "end")
        self.configure(state="disabled")
        self.last_response = ""