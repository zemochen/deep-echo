"""
Main entry point for DeepEcho Real-time Voice AI Assistant.

This module provides the main application startup logic with improved
initialization, dependency validation, and configuration management.
"""

import sys
import os
import threading
import queue
import time
import subprocess
import signal
import atexit
from typing import Optional, Tuple
from pathlib import Path

# Add current directory to Python path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import configuration management
from src.config.config_manager import get_config_manager, SystemConfig, ConfigurationError
from src.config.settings import (
    ERROR_MESSAGES, SUCCESS_MESSAGES, REQUIRED_DEPENDENCIES,
    DEFAULT_AI_PROVIDER
)
from src.utils.logger import get_logger

# Import core components
try:
    from src.audio.recorder import AudioRecorder
    from src.audio.transcriber import AudioTranscriber
except ImportError:
    # Components not yet implemented, will use legacy fallback
    AudioRecorder = None
    AudioTranscriber = None
from src.ai.adapter import AIAdapter
from src.ai.responder import GPTResponder

# Import UI components with fallback
try:
    from src.ui.main_window import MainWindow
except ImportError:
    MainWindow = None

# Legacy imports for backward compatibility
try:
    import AudioRecorder as LegacyAudioRecorder
    import AudioTranscriber as LegacyAudioTranscriber
    import TranscriberModels
    import UILayout as layout
    from keys import OPENAI_API_KEY, VOLCENGINE_API_KEY
    LEGACY_AVAILABLE = True
except ImportError:
    LEGACY_AVAILABLE = False

logger = get_logger(__name__)


class DeepEchoApplication:
    """
    Main application class for DeepEcho Real-time Voice AI Assistant.
    
    Handles system initialization, dependency validation, configuration management,
    and graceful startup/shutdown procedures.
    """
    
    def __init__(self):
        """Initialize the application."""
        self.config_manager = get_config_manager()
        self.config: Optional[SystemConfig] = None
        self.audio_recorder: Optional[AudioRecorder] = None
        self.transcriber: Optional[AudioTranscriber] = None
        self.ai_adapter: Optional[AIAdapter] = None
        self.responder: Optional[GPTResponder] = None
        self.main_window: Optional[MainWindow] = None
        
        # Audio queues
        self.speaker_queue = queue.Queue()
        self.mic_queue = queue.Queue()
        
        # Thread management
        self.threads = []
        self.shutdown_event = threading.Event()
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def validate_dependencies(self) -> Tuple[bool, str]:
        """
        Validate system dependencies.
        
        Returns:
            Tuple of (success, message)
        """
        logger.info("Validating system dependencies...")
        
        # Check FFmpeg
        try:
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            if result.returncode != 0:
                return False, ERROR_MESSAGES["ffmpeg_not_found"]
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False, ERROR_MESSAGES["ffmpeg_not_found"]
        
        logger.info("FFmpeg validation passed")
        
        # Check Python version
        if sys.version_info < (3, 8):
            return False, "Python 3.8 or higher is required"
        
        # Check required modules
        required_modules = [
            "customtkinter", "numpy", "threading", "queue"
        ]
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                return False, f"Required module '{module}' not found"
        
        logger.info("All dependencies validated successfully")
        return True, "Dependencies validation passed"
    
    def load_configuration(self) -> bool:
        """
        Load and validate system configuration.
        
        Returns:
            bool: True if configuration loaded successfully
        """
        try:
            logger.info("Loading system configuration...")
            self.config = self.config_manager.load_config()
            
            # Validate configuration
            is_valid, messages = self.config_manager.validate_current_config()
            if not is_valid:
                logger.warning(f"Configuration validation issues: {messages}")
                # Try to use configuration anyway, with warnings
                for message in messages:
                    print(f"WARNING: {message}")
            
            logger.info("Configuration loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            print(f"ERROR: {ERROR_MESSAGES['config_load_failed']}: {e}")
            return False
    
    def initialize_audio_system(self) -> bool:
        """
        Initialize audio recording system.
        
        Returns:
            bool: True if audio system initialized successfully
        """
        try:
            logger.info("Initializing audio system...")
            
            # Check if we should use legacy or new audio system
            use_legacy = '--legacy' in sys.argv or not hasattr(self, 'config')
            
            if use_legacy and LEGACY_AVAILABLE:
                logger.info("Using legacy audio system")
                # Use legacy audio recorder
                self.user_audio_recorder = LegacyAudioRecorder.DefaultMicRecorder()
                self.user_audio_recorder.record_into_queue(self.mic_queue)
                
                time.sleep(2)  # Allow mic to initialize
                
                self.speaker_audio_recorder = LegacyAudioRecorder.DefaultSpeakerRecorder()
                self.speaker_audio_recorder.record_into_queue(self.speaker_queue)
                
            else:
                logger.info("Using new audio system")
                # Use new audio recorder (when implemented)
                # For now, fall back to legacy if available
                if LEGACY_AVAILABLE:
                    self.user_audio_recorder = LegacyAudioRecorder.DefaultMicRecorder()
                    self.user_audio_recorder.record_into_queue(self.mic_queue)
                    
                    time.sleep(2)
                    
                    self.speaker_audio_recorder = LegacyAudioRecorder.DefaultSpeakerRecorder()
                    self.speaker_audio_recorder.record_into_queue(self.speaker_queue)
                else:
                    raise RuntimeError("Audio system not available")
            
            logger.info("Audio system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            print(f"ERROR: {ERROR_MESSAGES['audio_device_error']}: {e}")
            return False
    
    def initialize_transcription(self) -> bool:
        """
        Initialize transcription system.
        
        Returns:
            bool: True if transcription initialized successfully
        """
        try:
            logger.info("Initializing transcription system...")
            
            # Determine transcription mode
            use_api = '--api' in sys.argv or (self.config and self.config.audio.use_api_mode)
            
            if LEGACY_AVAILABLE:
                # Use legacy transcriber
                model = TranscriberModels.get_model(use_api)
                self.transcriber = LegacyAudioTranscriber(
                    self.user_audio_recorder.source,
                    self.speaker_audio_recorder.source,
                    model
                )
                
                # Start transcription thread
                transcribe_thread = threading.Thread(
                    target=self.transcriber.transcribe_audio_queue,
                    args=(self.speaker_queue, self.mic_queue),
                    daemon=True
                )
                transcribe_thread.start()
                self.threads.append(transcribe_thread)
                
            else:
                # Use new transcriber (when implemented)
                raise RuntimeError("New transcription system not yet implemented")
            
            logger.info("Transcription system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize transcription: {e}")
            print(f"ERROR: {ERROR_MESSAGES['transcription_error']}: {e}")
            return False
    
    def initialize_ai_system(self) -> bool:
        """
        Initialize AI response system.
        
        Returns:
            bool: True if AI system initialized successfully
        """
        try:
            logger.info("Initializing AI system...")
            
            # Initialize AI adapter
            self.ai_adapter = AIAdapter()
            
            # Configure AI provider based on configuration
            if self.config and self.config.ai_provider.api_key != "your-api-key-here":
                # Use configured provider
                provider_config = self.config.ai_provider
                try:
                    provider = self.ai_adapter.create_provider(
                        provider_config.provider_type,
                        provider_config.api_key,
                        provider_config.model
                    )
                    self.ai_adapter.set_provider(provider)
                    logger.info(f"Using configured {provider_config.provider_type} provider")
                    print(f"Using {provider_config.provider_type} provider with model: {provider_config.model}")
                    
                except Exception as e:
                    logger.warning(f"Failed to initialize configured provider: {e}")
                    # Fall back to legacy key detection
                    self._initialize_legacy_ai_provider()
            else:
                # Fall back to legacy key detection
                self._initialize_legacy_ai_provider()
            
            # Initialize responder
            self.responder = GPTResponder(self.ai_adapter)
            
            # Start responder thread
            respond_thread = threading.Thread(
                target=self.responder.respond_to_transcriber,
                args=(self.transcriber,),
                daemon=True
            )
            respond_thread.start()
            self.threads.append(respond_thread)
            
            logger.info("AI system initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI system: {e}")
            print(f"ERROR: {ERROR_MESSAGES['ai_response_error']}: {e}")
            return False
    
    def _initialize_legacy_ai_provider(self):
        """Initialize AI provider using legacy key detection."""
        try:
            if LEGACY_AVAILABLE and OPENAI_API_KEY and OPENAI_API_KEY.startswith('sk-'):
                # Use OpenAI as default provider
                openai_provider = self.ai_adapter.create_provider("openai", OPENAI_API_KEY)
                self.ai_adapter.set_provider(openai_provider)
                logger.info("Using legacy OpenAI provider")
                print(f"Using OpenAI provider with model: {openai_provider.get_model_name()}")
                
            elif LEGACY_AVAILABLE and VOLCENGINE_API_KEY:
                # Use Volcano Engine as fallback
                volcano_provider = self.ai_adapter.create_provider("volcano", VOLCENGINE_API_KEY)
                self.ai_adapter.set_provider(volcano_provider)
                logger.info("Using legacy Volcano Engine provider")
                print(f"Using Volcano Engine provider with model: {volcano_provider.get_model_name()}")
                
            else:
                logger.warning("No valid API keys found")
                print(ERROR_MESSAGES["no_api_key"])
                # Create a dummy provider for testing
                self._create_dummy_provider("No AI provider configured")
                
        except Exception as e:
            logger.error(f"Error setting up legacy AI provider: {e}")
            print(f"Error setting up AI provider: {e}")
            self._create_dummy_provider(f"AI provider error: {e}")
    
    def _create_dummy_provider(self, message: str):
        """Create a dummy AI provider for fallback."""
        from src.ai.providers.base_provider import AIProvider
        
        class DummyProvider(AIProvider):
            def __init__(self, msg: str):
                super().__init__("dummy-key", "dummy-model")
                self.message = msg
                
            def generate_response(self, prompt: str, **kwargs) -> str:
                return self.message
                
            def get_provider_name(self) -> str:
                return "dummy"
        
        self.ai_adapter.set_provider(DummyProvider(message))
    
    def initialize_ui(self) -> bool:
        """
        Initialize user interface.
        
        Returns:
            bool: True if UI initialized successfully
        """
        try:
            logger.info("Initializing user interface...")
            
            # Determine UI mode
            use_new_ui = '--new-ui' in sys.argv or (self.config and self.config.ui.use_new_ui)
            use_legacy_ui = '--legacy-ui' in sys.argv
            
            if use_legacy_ui or (not use_new_ui and LEGACY_AVAILABLE):
                logger.info("Using legacy UI")
                self._initialize_legacy_ui()
            else:
                logger.info("Using new UI")
                self._initialize_new_ui()
            
            logger.info("User interface initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize UI: {e}")
            print(f"ERROR: Failed to initialize user interface: {e}")
            return False
    
    def _initialize_new_ui(self):
        """Initialize new main window UI."""
        self.main_window = MainWindow()
        self.main_window.initialize(
            self.transcriber,
            self.responder,
            self.ai_adapter,
            self.speaker_queue,
            self.mic_queue
        )
        print("READY - Using new UI with AI provider selection")
    
    def _initialize_legacy_ui(self):
        """Initialize legacy UI for backward compatibility."""
        if not LEGACY_AVAILABLE:
            raise RuntimeError("Legacy UI not available")
        
        self.root = layout.init_ui()
        
        transcript_textbox, response_textbox, update_interval_slider, \
        update_interval_slider_label, freeze_button = layout.create_ui_components(
            self.root, self.transcriber, self.speaker_queue, self.mic_queue
        )
        
        freeze_state = [False]
        
        def freeze_unfreeze():
            freeze_state[0] = not freeze_state[0]
            freeze_button.configure(text="Unfreeze" if freeze_state[0] else "Freeze")
            return freeze_state[0]
        
        freeze_button.configure(command=freeze_unfreeze)
        update_interval_slider_label.configure(
            text=f"Update interval: {update_interval_slider.get()} seconds"
        )
        
        print("READY - Using legacy UI")
        
        # Start UI update threads
        layout.update_transcript_UI(self.transcriber, transcript_textbox)
        layout.update_response_UI(
            self.responder, response_textbox, update_interval_slider_label,
            update_interval_slider, freeze_state
        )
    
    def run(self):
        """Run the main application."""
        try:
            logger.info("Starting DeepEcho application...")
            
            # Validate dependencies
            deps_valid, deps_message = self.validate_dependencies()
            if not deps_valid:
                print(deps_message)
                return 1
            
            # Load configuration
            if not self.load_configuration():
                return 1
            
            # Initialize systems
            if not self.initialize_audio_system():
                return 1
            
            if not self.initialize_transcription():
                return 1
            
            if not self.initialize_ai_system():
                return 1
            
            if not self.initialize_ui():
                return 1
            
            # Start the application
            logger.info(SUCCESS_MESSAGES["system_ready"])
            print(SUCCESS_MESSAGES["system_ready"])
            
            if self.main_window:
                self.main_window.run()
            elif hasattr(self, 'root'):
                self.root.mainloop()
            else:
                # Keep the application running
                try:
                    while not self.shutdown_event.is_set():
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    pass
            
            return 0
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            print(f"ERROR: Application failed to start: {e}")
            return 1
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources and shutdown gracefully."""
        logger.info("Shutting down application...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Wait for threads to finish
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        # Clean up UI
        if self.main_window:
            try:
                self.main_window.cleanup()
            except:
                pass
        
        logger.info("Application shutdown complete")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.cleanup()
        sys.exit(0)


def parse_arguments():
    """Parse command line arguments."""
    args = {
        'use_api': '--api' in sys.argv,
        'use_new_ui': '--new-ui' in sys.argv,
        'use_legacy_ui': '--legacy-ui' in sys.argv,
        'use_legacy': '--legacy' in sys.argv,
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
  --new-ui           Use new UI with AI provider selection (default)
  --legacy-ui        Use legacy UI for backward compatibility
  --legacy           Use legacy audio system
  --verbose, -v      Enable verbose logging
  --help, -h         Show this help message

Examples:
  python main.py                    # Run with default settings
  python main.py --api             # Use API transcription mode
  python main.py --legacy-ui       # Use legacy UI
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
    
    # Create and run application
    app = DeepEchoApplication()
    return app.run()


if __name__ == "__main__":
    sys.exit(main())