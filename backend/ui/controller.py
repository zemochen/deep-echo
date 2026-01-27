"""
UI Controller for DeepEcho Real-time Voice AI Assistant.

This module provides the main UI controller that manages the user interface,
handles user interactions, and coordinates between different UI components.
"""

# Optional import for testing compatibility
try:
    import customtkinter as ctk
    CUSTOMTKINTER_AVAILABLE = True
except ImportError:
    ctk = None
    CUSTOMTKINTER_AVAILABLE = False

import threading
import queue
from typing import Optional, Callable, Tuple, List
from backend.utils.logger import get_logger

logger = get_logger(__name__)


# Mock classes for testing when customtkinter is not available
if not CUSTOMTKINTER_AVAILABLE:
    class MockCTk:
        def __init__(self, *args, **kwargs):
            pass
        def mainloop(self):
            pass
        def title(self, *args, **kwargs):
            pass
        def geometry(self, *args, **kwargs):
            pass
        def protocol(self, *args, **kwargs):
            pass
        def configure(self, *args, **kwargs):
            pass
    
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
    
    class MockCTkLabel:
        def __init__(self, *args, **kwargs):
            pass
        def pack(self, *args, **kwargs):
            pass
        def grid(self, *args, **kwargs):
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
        def pack(self, *args, **kwargs):
            pass
        def grid(self, *args, **kwargs):
            pass
    
    class MockCTkButton:
        def __init__(self, *args, **kwargs):
            pass
        def pack(self, *args, **kwargs):
            pass
        def grid(self, *args, **kwargs):
            pass
        def configure(self, *args, **kwargs):
            pass
    
    class MockCTkSlider:
        def __init__(self, *args, **kwargs):
            pass
        def pack(self, *args, **kwargs):
            pass
        def grid(self, *args, **kwargs):
            pass
        def get(self):
            return 1.0
        def set(self, *args, **kwargs):
            pass
        def configure(self, *args, **kwargs):
            pass
    
    # Replace ctk classes with mock classes
    if ctk is None:
        class ctk:
            CTk = MockCTk
            CTkFrame = MockCTkFrame
            CTkLabel = MockCTkLabel
            CTkTextbox = MockCTkTextbox
            CTkButton = MockCTkButton
            CTkSlider = MockCTkSlider
            
            @staticmethod
            def set_appearance_mode(*args, **kwargs):
                pass
            
            @staticmethod
            def set_default_color_theme(*args, **kwargs):
                pass


class UIController:
    """
    Main UI controller that manages the user interface and user interactions.
    
    This class handles UI initialization, component creation, and event management
    for the DeepEcho application.
    """
    
    def __init__(self):
        """Initialize the UI controller."""
        self.root: Optional[ctk.CTk] = None
        self.freeze_state = [False]  # Using list to allow modification in nested functions
        self.current_ai_provider = "Not configured"
        self.current_model = "Not configured"
        self.error_message = ""
        self.status_message = "Initializing..."
        
        # UI Components
        self.transcript_textbox: Optional[ctk.CTkTextbox] = None
        self.response_textbox: Optional[ctk.CTkTextbox] = None
        self.update_interval_slider: Optional[ctk.CTkSlider] = None
        self.update_interval_label: Optional[ctk.CTkLabel] = None
        self.freeze_button: Optional[ctk.CTkButton] = None
        self.clear_button: Optional[ctk.CTkButton] = None
        self.ai_provider_dropdown: Optional[ctk.CTkComboBox] = None
        self.model_dropdown: Optional[ctk.CTkComboBox] = None
        self.status_label: Optional[ctk.CTkLabel] = None
        self.error_label: Optional[ctk.CTkLabel] = None
        
        # Callbacks
        self.clear_context_callback: Optional[Callable] = None
        self.provider_change_callback: Optional[Callable] = None
        self.model_change_callback: Optional[Callable] = None
        
    def init_ui(self) -> ctk.CTk:
        """
        Initialize the main UI window.
        
        Returns:
            ctk.CTk: The main application window
        """
        logger.info("Initializing UI")
        
        self.root = ctk.CTk()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")
        
        # Configure grid weights for responsive layout
        self.root.grid_rowconfigure(0, weight=100)  # Main content area
        self.root.grid_rowconfigure(1, weight=1)    # Status bar
        self.root.grid_columnconfigure(0, weight=2) # Transcript area
        self.root.grid_columnconfigure(1, weight=1) # Control panel
        
        self.root.title("DeepEcho - Real-time Voice AI Assistant")
        self.root.geometry("1200x700")
        
        return self.root
    
    def create_ui_components(self, transcriber, speaker_queue: queue.Queue, 
                           mic_queue: queue.Queue) -> Tuple:
        """
        Create and layout all UI components.
        
        Args:
            transcriber: Audio transcriber instance
            speaker_queue: Speaker audio queue
            mic_queue: Microphone audio queue
            
        Returns:
            Tuple of UI components for backward compatibility
        """
        if not self.root:
            raise RuntimeError("UI must be initialized before creating components")
            
        logger.info("Creating UI components")
        
        # Create main content area
        self._create_main_content_area()
        
        # Create control panel
        self._create_control_panel()
        
        # Create status bar
        self._create_status_bar()
        
        # Set up callbacks
        self._setup_callbacks(transcriber, speaker_queue, mic_queue)
        
        # Return components for backward compatibility
        return (self.transcript_textbox, self.response_textbox, 
                self.update_interval_slider, self.update_interval_label, 
                self.freeze_button)
    
    def _create_main_content_area(self):
        """Create the main content area with transcript display."""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=0)
        
        # Transcript textbox
        self.transcript_textbox = ctk.CTkTextbox(
            main_frame,
            font=("Arial", 12),
            text_color='#FFFCF2',
            wrap="word"
        )
        self.transcript_textbox.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Clear button
        self.clear_button = ctk.CTkButton(
            main_frame,
            text="Clear Transcript",
            command=self._on_clear_context
        )
        self.clear_button.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
    
    def _create_control_panel(self):
        """Create the right-side control panel."""
        right_frame = ctk.CTkFrame(self.root)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(0, weight=100)  # Response textbox
        right_frame.grid_rowconfigure(1, weight=0)    # AI provider selection
        right_frame.grid_rowconfigure(2, weight=0)    # Model selection
        right_frame.grid_rowconfigure(3, weight=0)    # Freeze button
        right_frame.grid_rowconfigure(4, weight=0)    # Update interval label
        right_frame.grid_rowconfigure(5, weight=0)    # Update interval slider
        right_frame.grid_rowconfigure(6, weight=0)    # Error display
        
        # Response textbox
        self.response_textbox = ctk.CTkTextbox(
            right_frame, 
            width=350, 
            font=("Arial", 12), 
            text_color='#639cdc', 
            wrap="word"
        )
        self.response_textbox.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # AI Provider selection
        provider_label = ctk.CTkLabel(right_frame, text="AI Provider:", font=("Arial", 12))
        provider_label.grid(row=1, column=0, padx=10, pady=(10, 5), sticky="w")
        
        self.ai_provider_dropdown = ctk.CTkComboBox(
            right_frame,
            values=["deepseek", "openai", "grok", "claude", "volcano", "glm"],
            command=self._on_provider_change,
            width=330
        )
        self.ai_provider_dropdown.grid(row=1, column=0, padx=10, pady=(25, 5), sticky="ew")
        
        # Model selection
        model_label = ctk.CTkLabel(right_frame, text="Model:", font=("Arial", 12))
        model_label.grid(row=2, column=0, padx=10, pady=(5, 5), sticky="w")
        
        self.model_dropdown = ctk.CTkComboBox(
            right_frame,
            values=["Loading..."],
            command=self._on_model_change,
            width=330
        )
        self.model_dropdown.grid(row=2, column=0, padx=10, pady=(20, 5), sticky="ew")
        
        # Freeze button
        self.freeze_button = ctk.CTkButton(
            right_frame, 
            text="Freeze", 
            command=self._on_freeze_toggle
        )
        self.freeze_button.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        
        # Update interval controls
        self.update_interval_label = ctk.CTkLabel(
            right_frame, 
            text="Update interval: 2 seconds", 
            font=("Arial", 12), 
            text_color="#FFFCF2"
        )
        self.update_interval_label.grid(row=4, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        self.update_interval_slider = ctk.CTkSlider(
            right_frame, 
            from_=1, 
            to=10, 
            width=330, 
            height=20, 
            number_of_steps=9,
            command=self._on_interval_change
        )
        self.update_interval_slider.set(2)
        self.update_interval_slider.grid(row=5, column=0, padx=10, pady=(5, 10), sticky="ew")
        
        # Error display
        self.error_label = ctk.CTkLabel(
            right_frame,
            text="",
            font=("Arial", 10),
            text_color="#FF6B6B",
            wraplength=300
        )
        self.error_label.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
    
    def _create_status_bar(self):
        """Create the bottom status bar."""
        status_frame = ctk.CTkFrame(self.root)
        status_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 20))
        
        status_frame.grid_columnconfigure(0, weight=1)
        status_frame.grid_columnconfigure(1, weight=0)
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text=self.status_message,
            font=("Arial", 10),
            text_color="#FFFCF2"
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
        
        # Provider info label
        self.provider_info_label = ctk.CTkLabel(
            status_frame,
            text=f"Provider: {self.current_ai_provider} | Model: {self.current_model}",
            font=("Arial", 10),
            text_color="#639cdc"
        )
        self.provider_info_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
    
    def _setup_callbacks(self, transcriber, speaker_queue: queue.Queue, mic_queue: queue.Queue):
        """Set up callback functions for UI events."""
        self.transcriber = transcriber
        self.speaker_queue = speaker_queue
        self.mic_queue = mic_queue
    
    def _on_clear_context(self):
        """Handle clear context button click."""
        if self.clear_context_callback:
            self.clear_context_callback()
        logger.info("Context cleared by user")
    
    def _on_freeze_toggle(self):
        """Handle freeze/unfreeze button click."""
        self.freeze_state[0] = not self.freeze_state[0]
        self.freeze_button.configure(text="Unfreeze" if self.freeze_state[0] else "Freeze")
        status = "frozen" if self.freeze_state[0] else "active"
        self.update_status(f"Display {status}")
        logger.info(f"Display {status}")
    
    def _on_provider_change(self, provider: str):
        """Handle AI provider selection change."""
        if self.provider_change_callback:
            self.provider_change_callback(provider)
        self.current_ai_provider = provider
        self.update_provider_info()
        logger.info(f"AI provider changed to: {provider}")
    
    def _on_model_change(self, model: str):
        """Handle model selection change."""
        if self.model_change_callback:
            self.model_change_callback(model)
        self.current_model = model
        self.update_provider_info()
        logger.info(f"Model changed to: {model}")
    
    def _on_interval_change(self, value: float):
        """Handle update interval slider change."""
        interval = int(value)
        self.update_interval_label.configure(text=f"Update interval: {interval} seconds")
        logger.debug(f"Update interval changed to: {interval} seconds")
    
    def update_transcript_ui(self):
        """Update the transcript display."""
        if self.transcript_textbox and hasattr(self, 'transcriber'):
            transcript_string = self.transcriber.get_transcript()
            self._write_in_textbox(self.transcript_textbox, transcript_string)
            self.transcript_textbox.after(300, self.update_transcript_ui)
    
    def update_response_ui(self, responder):
        """Update the response display."""
        if not self.freeze_state[0] and self.response_textbox:
            try:
                response = responder.get_current_response()
                
                self.response_textbox.configure(state="normal")
                self._write_in_textbox(self.response_textbox, response)
                self.response_textbox.configure(state="disabled")
                
                # Update interval from slider
                if self.update_interval_slider:
                    update_interval = int(self.update_interval_slider.get())
                    responder.update_response_interval(update_interval)
                    self.update_interval_label.configure(
                        text=f"Update interval: {update_interval} seconds"
                    )
                
                # Clear any previous errors
                self.clear_error()
                
            except Exception as e:
                self.show_error(f"Response update error: {str(e)}")
                logger.error(f"Error updating response UI: {e}")
        
        if self.response_textbox:
            self.response_textbox.after(300, self.update_response_ui, responder)
    
    def _write_in_textbox(self, textbox: ctk.CTkTextbox, text: str):
        """Write text to a textbox, replacing existing content."""
        textbox.delete("0.0", "end")
        textbox.insert("0.0", text)
    
    def show_error(self, message: str):
        """Display an error message."""
        self.error_message = message
        if self.error_label:
            self.error_label.configure(text=message)
        logger.error(f"UI Error: {message}")
    
    def clear_error(self):
        """Clear the error message display."""
        self.error_message = ""
        if self.error_label:
            self.error_label.configure(text="")
    
    def update_status(self, message: str):
        """Update the status message."""
        self.status_message = message
        if self.status_label:
            self.status_label.configure(text=message)
    
    def update_provider_info(self):
        """Update the provider information display."""
        if self.provider_info_label:
            self.provider_info_label.configure(
                text=f"Provider: {self.current_ai_provider} | Model: {self.current_model}"
            )
    
    def set_ai_provider_models(self, provider: str, models: List[str]):
        """Update the model dropdown with available models for the selected provider."""
        if self.model_dropdown:
            self.model_dropdown.configure(values=models)
            if models:
                self.model_dropdown.set(models[0])
                self.current_model = models[0]
                self.update_provider_info()
    
    def set_current_provider(self, provider: str, model: str):
        """Set the current AI provider and model."""
        self.current_ai_provider = provider
        self.current_model = model
        
        if self.ai_provider_dropdown:
            self.ai_provider_dropdown.set(provider)
        if self.model_dropdown:
            self.model_dropdown.set(model)
        
        self.update_provider_info()
    
    def set_clear_context_callback(self, callback: Callable):
        """Set the callback for clearing context."""
        self.clear_context_callback = callback
    
    def set_provider_change_callback(self, callback: Callable):
        """Set the callback for provider changes."""
        self.provider_change_callback = callback
    
    def set_model_change_callback(self, callback: Callable):
        """Set the callback for model changes."""
        self.model_change_callback = callback
    
    def get_freeze_state(self) -> List[bool]:
        """Get the current freeze state."""
        return self.freeze_state
    
    def get_update_interval(self) -> int:
        """Get the current update interval setting."""
        if self.update_interval_slider:
            return int(self.update_interval_slider.get())
        return 2


# Backward compatibility functions
def init_ui() -> ctk.CTk:
    """Initialize UI (backward compatibility)."""
    controller = UIController()
    return controller.init_ui()


def create_ui_components(root, transcriber, speaker_queue, mic_queue):
    """Create UI components (backward compatibility)."""
    # This function maintains backward compatibility with existing code
    # In practice, the UIController should be used directly
    controller = UIController()
    controller.root = root
    return controller.create_ui_components(transcriber, speaker_queue, mic_queue)


def update_transcript_UI(transcriber, textbox):
    """Update transcript UI (backward compatibility)."""
    transcript_string = transcriber.get_transcript()
    textbox.delete("0.0", "end")
    textbox.insert("0.0", transcript_string)
    textbox.after(300, update_transcript_UI, transcriber, textbox)


def update_response_UI(responder, textbox, update_interval_slider_label, 
                      update_interval_slider, freeze_state):
    """Update response UI (backward compatibility)."""
    if not freeze_state[0]:
        response = responder.get_current_response()
        
        textbox.configure(state="normal")
        textbox.delete("0.0", "end")
        textbox.insert("0.0", response)
        textbox.configure(state="disabled")
        
        update_interval = int(update_interval_slider.get())
        responder.update_response_interval(update_interval)
        update_interval_slider_label.configure(text=f"Update interval: {update_interval} seconds")
    
    textbox.after(300, update_response_UI, responder, textbox, 
                  update_interval_slider_label, update_interval_slider, freeze_state)


def clear_context(transcriber, speaker_queue, mic_queue):
    """Clear context (backward compatibility)."""
    transcriber.clear_transcript_data()
    
    with speaker_queue.mutex:
        speaker_queue.queue.clear()
    with mic_queue.mutex:
        mic_queue.queue.clear()


def write_in_textbox(textbox, text):
    """Write text in textbox (backward compatibility)."""
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)