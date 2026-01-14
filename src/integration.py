"""
Integration module for DeepEcho Real-time Voice AI Assistant.

This module provides comprehensive integration of all system components
with proper initialization order, dependency management, and error handling.
"""

import sys
import os
import threading
import queue
import time
import signal
import atexit
from typing import Optional, Dict, Any, Tuple, List
from pathlib import Path
import logging

# Import configuration management
from src.config.config_manager import get_config_manager, SystemConfig, ConfigurationError
from src.config.settings import (
    ERROR_MESSAGES, SUCCESS_MESSAGES, REQUIRED_DEPENDENCIES,
    DEFAULT_AI_PROVIDER, RECORD_TIMEOUT, PHRASE_TIMEOUT
)
from src.utils.logger import get_logger
from src.utils.exceptions import DeepEchoError, AudioSystemError, TranscriptionError, AISystemError

# Import core components
from src.audio.recorder import DefaultMicRecorder, DefaultSpeakerRecorder, AudioRecorderError
from src.audio.transcriber import AudioTranscriber
from src.audio.models import TranscriberModel, LocalWhisperModel, APIWhisperModel
from src.ai.adapter import AIAdapter
from src.ai.responder import GPTResponder
from src.ui.main_window import MainWindow
from src.ui.controller import UIController

# Import audio system components
from src.audio_system.audio_factory import AudioSystemFactory
from src.audio_system.audio_interface import AudioSystemInterface

# Import utility components
from src.utils.threading import ThreadManager, ThreadPriority
from src.utils.queue_manager import QueueManager, QueueType
from src.utils.resource_optimizer import ResourceOptimizer
from src.utils.error_recovery import ErrorRecoveryManager
from src.utils.retry import retry_with_backoff, RetryConfig

logger = get_logger(__name__)


class IntegratedDeepEchoApplication:
    """
    Integrated DeepEcho application that manages all system components.
    
    This class provides comprehensive integration with proper initialization order,
    dependency validation, configuration management, and graceful error handling.
    """
    
    def __init__(self):
        """Initialize the integrated application."""
        self.config_manager = get_config_manager()
        self.config: Optional[SystemConfig] = None
        
        # Core components
        self.audio_system: Optional[AudioSystemInterface] = None
        self.mic_recorder: Optional[DefaultMicRecorder] = None
        self.speaker_recorder: Optional[DefaultSpeakerRecorder] = None
        self.transcriber: Optional[AudioTranscriber] = None
        self.ai_adapter: Optional[AIAdapter] = None
        self.responder: Optional[GPTResponder] = None
        self.main_window: Optional[MainWindow] = None
        self.ui_controller: Optional[UIController] = None
        
        # System management
        self.thread_manager = ThreadManager()
        self.queue_manager = QueueManager()
        self.resource_optimizer = ResourceOptimizer()
        self.error_recovery = ErrorRecoveryManager()
        
        # Audio queues (will be created in initialize_audio_system)
        self.speaker_queue = None
        self.mic_queue = None
        
        # State management
        self.shutdown_event = threading.Event()
        self.initialization_complete = threading.Event()
        self.system_ready = threading.Event()
        
        # Component status tracking
        self.component_status: Dict[str, bool] = {
            'dependencies': False,
            'configuration': False,
            'audio_system': False,
            'transcription': False,
            'ai_system': False,
            'ui_system': False
        }
        
        # Register cleanup handlers
        atexit.register(self.cleanup)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Integrated DeepEcho application initialized")
    
    def validate_system_dependencies(self) -> Tuple[bool, List[str]]:
        """
        Validate all system dependencies comprehensively.
        
        Returns:
            Tuple of (success, error_messages)
        """
        logger.info("Validating comprehensive system dependencies...")
        errors = []
        
        try:
            # Check FFmpeg
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-version"], 
                stdout=subprocess.DEVNULL, 
                stderr=subprocess.DEVNULL,
                timeout=10
            )
            if result.returncode != 0:
                errors.append(ERROR_MESSAGES["ffmpeg_not_found"])
        except (FileNotFoundError, subprocess.TimeoutExpired):
            errors.append(ERROR_MESSAGES["ffmpeg_not_found"])
        
        # Check Python version
        if sys.version_info < (3, 8):
            errors.append("Python 3.8 or higher is required")
        
        # Check required modules
        required_modules = [
            "customtkinter", "numpy", "threading", "queue", "openai",
            "anthropic", "requests", "hypothesis", "pytest"
        ]
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                errors.append(f"Required module '{module}' not found")
        
        # Check audio system dependencies
        try:
            import pyaudio
        except ImportError:
            errors.append("PyAudio not found - required for audio recording")
        
        # Platform-specific checks
        if sys.platform == "darwin":  # macOS
            try:
                import sounddevice
            except ImportError:
                errors.append("SoundDevice not found - required for macOS audio")
        elif sys.platform == "win32":  # Windows
            try:
                import pyaudiowpatch
            except ImportError:
                errors.append("PyAudioWPatch not found - required for Windows audio")
        
        success = len(errors) == 0
        if success:
            logger.info("All system dependencies validated successfully")
            self.component_status['dependencies'] = True
        else:
            logger.error(f"Dependency validation failed: {errors}")
        
        return success, errors
    
    def load_and_validate_configuration(self) -> bool:
        """
        Load and validate comprehensive system configuration.
        
        Returns:
            bool: True if configuration loaded and validated successfully
        """
        try:
            logger.info("Loading and validating system configuration...")
            
            # Load configuration
            self.config = self.config_manager.load_config()
            
            # Comprehensive validation
            is_valid, messages = self.config_manager.validate_current_config()
            if not is_valid:
                logger.warning(f"Configuration validation issues: {messages}")
                for message in messages:
                    print(f"WARNING: {message}")
            
            # Additional runtime validation
            self._validate_runtime_configuration()
            
            logger.info("Configuration loaded and validated successfully")
            self.component_status['configuration'] = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            print(f"ERROR: {ERROR_MESSAGES['config_load_failed']}: {e}")
            return False
    
    def _validate_runtime_configuration(self):
        """Validate runtime-specific configuration aspects."""
        if not self.config:
            return
        
        # Validate AI provider configuration
        if self.config.ai_provider.api_key == "your-api-key-here":
            logger.warning("AI provider API key not configured")
        
        # Validate audio configuration
        if self.config.audio.record_timeout <= 0:
            logger.warning("Invalid audio record timeout, using default")
            self.config.audio.record_timeout = RECORD_TIMEOUT
        
        # Validate UI configuration
        if self.config.ui.update_interval <= 0:
            logger.warning("Invalid UI update interval, using default")
            self.config.ui.update_interval = 0.3
    
    @retry_with_backoff(
        exceptions=(AudioSystemError, Exception),
        config=RetryConfig(max_attempts=3, backoff_factor=1.5)
    )
    def initialize_audio_system(self) -> bool:
        """
        Initialize comprehensive audio recording system.
        
        Returns:
            bool: True if audio system initialized successfully
        """
        try:
            logger.info("Initializing comprehensive audio system...")
            
            # Create managed queues with queue manager FIRST
            self.mic_queue = self.queue_manager.create_queue(
                name="microphone",
                maxsize=1000,
                queue_type=QueueType.FIFO
            )
            self.speaker_queue = self.queue_manager.create_queue(
                name="speaker",
                maxsize=1000,
                queue_type=QueueType.FIFO
            )
            
            # Initialize audio system factory
            audio_factory = AudioSystemFactory()
            self.audio_system = audio_factory.create_audio_system()
            
            # Initialize audio devices
            if self.audio_system:
                self.audio_system.initialize_devices()
            
            # Create audio recorders
            self.mic_recorder = DefaultMicRecorder()
            self.speaker_recorder = DefaultSpeakerRecorder()
            
            # Configure audio parameters
            if self.config:
                self.mic_recorder.configure(
                    record_timeout=self.config.audio.record_timeout,
                    phrase_timeout=self.config.audio.phrase_timeout,
                    energy_threshold=self.config.audio.energy_threshold
                )
                self.speaker_recorder.configure(
                    record_timeout=self.config.audio.record_timeout,
                    phrase_timeout=self.config.audio.phrase_timeout,
                    energy_threshold=self.config.audio.energy_threshold
                )
            
            # Start audio recording
            self.mic_recorder.record_into_queue(self.mic_queue)
            time.sleep(2)  # Allow mic to initialize
            self.speaker_recorder.record_into_queue(self.speaker_queue)
            
            logger.info("Audio system initialized successfully")
            self.component_status['audio_system'] = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize audio system: {e}")
            self.error_recovery.handle_audio_error(e)
            # Don't raise - allow application to continue with degraded audio
            logger.warning("Continuing with degraded audio system")
            self.component_status['audio_system'] = False
            return False
    
    def initialize_transcription_system(self) -> bool:
        """
        Initialize comprehensive transcription system.
        
        Returns:
            bool: True if transcription initialized successfully
        """
        try:
            logger.info("Initializing comprehensive transcription system...")
            
            # Determine transcription mode
            use_api = (self.config and self.config.audio.use_api_mode) or '--api' in sys.argv
            
            # Create appropriate transcription model
            if use_api:
                model = APIWhisperModel()
                logger.info("Using API-based transcription model")
            else:
                # Get model configuration
                model_name = "small"  # Default
                model_path = None
                
                if self.config:
                    # Check if a local model path is specified
                    if hasattr(self.config.audio, 'whisper_model_path') and self.config.audio.whisper_model_path:
                        model_path = self.config.audio.whisper_model_path
                        # If path exists, use it directly
                        if os.path.exists(model_path):
                            model_name = model_path
                            logger.info(f"Using local Whisper model file: {model_path}")
                        else:
                            logger.warning(f"Model path not found: {model_path}, falling back to model name")
                            model_name = getattr(self.config.audio, 'whisper_model', 'small')
                    elif hasattr(self.config.audio, 'whisper_model'):
                        model_name = self.config.audio.whisper_model
                        # Check if it's a path
                        if os.path.exists(model_name):
                            logger.info(f"Using local Whisper model file: {model_name}")
                        else:
                            logger.info(f"Using Whisper model: {model_name}")
                
                # Initialize local model with specified model name/path
                model = LocalWhisperModel(model_name=model_name)
                logger.info(f"Using local Whisper transcription model: {model_name}")
            
            # Initialize transcriber
            self.transcriber = AudioTranscriber(
                mic_source=self.mic_recorder.source,
                speaker_source=self.speaker_recorder.source,
                model=model
            )
            
            # Configure transcriber
            if self.config:
                self.transcriber.configure(
                    max_phrases=self.config.audio.max_phrases,
                    processing_interval=self.config.ui.processing_interval
                )
            
            # Start transcription using the new method
            # The new start_transcription method creates and manages its own thread
            self.transcriber.start_transcription(self.speaker_queue, self.mic_queue)
            
            logger.info("Transcription system initialized successfully")
            self.component_status['transcription'] = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize transcription system: {e}")
            self.error_recovery.handle_transcription_error(e)
            raise TranscriptionError(f"Transcription system initialization failed: {e}")
    
    def initialize_ai_system(self) -> bool:
        """
        Initialize comprehensive AI response system.
        
        Returns:
            bool: True if AI system initialized successfully
        """
        try:
            logger.info("Initializing comprehensive AI system...")
            
            # Initialize AI adapter
            self.ai_adapter = AIAdapter()
            
            # Configure AI provider
            if self.config and self.config.ai_provider.api_key != "your-api-key-here":
                # Use configured provider
                provider_config = self.config.ai_provider
                try:
                    provider = self.ai_adapter.create_provider(
                        provider_config.provider_type,
                        provider_config.api_key,
                        provider_config.model,
                        base_url=getattr(provider_config, 'base_url', None),
                        timeout=getattr(provider_config, 'timeout', 30),
                        max_retries=getattr(provider_config, 'max_retries', 3)
                    )
                    self.ai_adapter.set_provider(provider)
                    logger.info(f"Using configured {provider_config.provider_type} provider")
                    print(f"AI Provider: {provider_config.provider_type} with model: {provider_config.model}")
                    
                except Exception as e:
                    logger.warning(f"Failed to initialize configured provider: {e}")
                    self._initialize_fallback_ai_provider()
            else:
                # Use fallback provider detection
                self._initialize_fallback_ai_provider()
            
            # Initialize responder
            self.responder = GPTResponder(self.ai_adapter)
            
            # Configure responder with UI update interval
            if self.config:
                self.responder.update_response_interval(self.config.ui.update_interval)
            
            # Start responder thread using thread manager
            # The thread manager will create and manage the thread
            respond_thread = self.thread_manager.create_thread(
                name="AIResponseThread",
                target=self.responder.respond_to_transcriber,
                args=(self.transcriber,),
                daemon=True,
                priority=ThreadPriority.HIGH,
                auto_start=True
            )
            
            if not respond_thread:
                raise Exception("Failed to create AI response thread")
            
            logger.info("AI system initialized successfully")
            self.component_status['ai_system'] = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize AI system: {e}")
            self.error_recovery.handle_ai_error(e)
            raise AISystemError(f"AI system initialization failed: {e}")
    
    def _initialize_fallback_ai_provider(self):
        """Initialize AI provider using fallback detection."""
        try:
            # Try to detect available API keys from environment or legacy keys
            import os
            
            # Check environment variables
            openai_key = os.getenv('OPENAI_API_KEY')
            deepseek_key = os.getenv('DEEPSEEK_API_KEY')
            claude_key = os.getenv('ANTHROPIC_API_KEY')
            
            # Try legacy keys import
            try:
                from keys import OPENAI_API_KEY, VOLCENGINE_API_KEY
                if not openai_key and OPENAI_API_KEY:
                    openai_key = OPENAI_API_KEY
            except ImportError:
                pass
            
            # Initialize provider based on available keys
            if deepseek_key:
                provider = self.ai_adapter.create_provider("deepseek", deepseek_key)
                self.ai_adapter.set_provider(provider)
                logger.info("Using DeepSeek provider (fallback)")
                print(f"AI Provider: DeepSeek with model: {provider.get_model_name()}")
                
            elif openai_key and openai_key.startswith('sk-'):
                provider = self.ai_adapter.create_provider("openai", openai_key)
                self.ai_adapter.set_provider(provider)
                logger.info("Using OpenAI provider (fallback)")
                print(f"AI Provider: OpenAI with model: {provider.get_model_name()}")
                
            elif claude_key:
                provider = self.ai_adapter.create_provider("claude", claude_key)
                self.ai_adapter.set_provider(provider)
                logger.info("Using Claude provider (fallback)")
                print(f"AI Provider: Claude with model: {provider.get_model_name()}")
                
            else:
                logger.warning("No valid API keys found")
                print("WARNING: No AI provider configured - responses will be limited")
                self._create_dummy_provider("No AI provider configured")
                
        except Exception as e:
            logger.error(f"Error setting up fallback AI provider: {e}")
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
                
            def get_model_name(self) -> str:
                return "dummy-model"
        
        self.ai_adapter.set_provider(DummyProvider(message))
    
    def initialize_ui_system(self) -> bool:
        """
        Initialize comprehensive user interface system.
        
        Returns:
            bool: True if UI system initialized successfully
        """
        try:
            logger.info("Initializing comprehensive UI system...")
            
            # Initialize integrated UI
            logger.info("Using integrated UI")
            self._initialize_integrated_ui()
            
            logger.info("UI system initialized successfully")
            self.component_status['ui_system'] = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize UI system: {e}")
            print(f"ERROR: Failed to initialize user interface: {e}")
            return False
    
    def _initialize_integrated_ui(self):
        """Initialize integrated UI system."""
        # Initialize main window
        self.main_window = MainWindow()
        
        # Initialize UI controller
        self.ui_controller = UIController()
        
        # Configure UI components
        self.main_window.initialize(
            transcriber=self.transcriber,
            responder=self.responder,
            ai_adapter=self.ai_adapter,
            speaker_queue=self.speaker_queue,
            mic_queue=self.mic_queue
        )
        
        # UI controller is already set up by MainWindow.initialize()
        # No need for separate initialization
        
        print("READY - Using integrated UI with full AI provider support")
    
    def validate_component_integration(self) -> Tuple[bool, List[str]]:
        """
        Validate that all components are properly integrated and communicating.
        
        Returns:
            Tuple of (success, error_messages)
        """
        logger.info("Validating component integration...")
        errors = []
        
        try:
            # Check audio system integration
            if self.component_status['audio_system']:
                if not self.mic_recorder or not self.speaker_recorder:
                    errors.append("Audio recorders not properly initialized")
                
                if self.mic_queue.empty() and self.speaker_queue.empty():
                    # This is normal at startup, just log it
                    logger.info("Audio queues are empty (normal at startup)")
            
            # Check transcription integration
            if self.component_status['transcription']:
                if not self.transcriber:
                    errors.append("Transcriber not properly initialized")
                
                # Check if transcriber has access to audio sources
                if self.transcriber and not hasattr(self.transcriber, 'mic_source'):
                    errors.append("Transcriber missing audio source references")
            
            # Check AI system integration
            if self.component_status['ai_system']:
                if not self.ai_adapter:
                    errors.append("AI adapter not properly initialized")
                
                if not self.responder:
                    errors.append("AI responder not properly initialized")
                
                # Test AI adapter functionality
                try:
                    current_provider = self.ai_adapter.get_current_provider()
                    if not current_provider:
                        errors.append("No AI provider configured")
                except Exception as e:
                    errors.append(f"AI adapter error: {e}")
            
            # Check UI integration
            if self.component_status['ui_system']:
                if not self.main_window and not hasattr(self, 'root'):
                    errors.append("No UI system initialized")
            
            # Check thread management
            thread_status = self.thread_manager.get_thread_status()
            dead_threads = [name for name, status in thread_status.items() if not status['alive']]
            if dead_threads:
                errors.append(f"Dead threads detected: {dead_threads}")
            
            # Check queue management
            queue_status = self.queue_manager.get_queue_status()
            for queue_name, status in queue_status.items():
                if status['size'] > 10000:  # Very large queue indicates a problem
                    errors.append(f"Queue {queue_name} is very large: {status['size']} items")
            
            success = len(errors) == 0
            if success:
                logger.info("Component integration validation passed")
            else:
                logger.warning(f"Component integration issues: {errors}")
            
            return success, errors
            
        except Exception as e:
            logger.error(f"Component integration validation failed: {e}")
            return False, [f"Integration validation error: {e}"]
    
    def run_system_diagnostics(self) -> Dict[str, Any]:
        """
        Run comprehensive system diagnostics.
        
        Returns:
            Dict containing diagnostic results
        """
        logger.info("Running comprehensive system diagnostics...")
        
        diagnostics = {
            'timestamp': time.time(),
            'components': self.component_status.copy(),
            'threads': self.thread_manager.get_thread_status(),
            'queues': self.queue_manager.get_queue_status(),
            'resources': self.resource_optimizer.get_resource_status(),
            'errors': self.error_recovery.get_error_history()
        }
        
        # Audio system diagnostics
        if self.audio_system:
            diagnostics['audio_devices'] = self.audio_system.get_device_status()
        
        # AI system diagnostics
        if self.ai_adapter:
            diagnostics['ai_provider'] = {
                'current_provider': self.ai_adapter.get_current_provider(),
                'available_providers': self.ai_adapter.get_available_providers()
            }
        
        # Configuration diagnostics
        if self.config:
            diagnostics['configuration'] = {
                'audio_mode': 'API' if self.config.audio.use_api_mode else 'Local',
                'ai_provider': self.config.ai_provider.provider_type,
                'ui_mode': 'Integrated'
            }
        
        logger.info("System diagnostics completed")
        return diagnostics
    
    def run(self) -> int:
        """
        Run the integrated application with comprehensive error handling.
        
        Returns:
            int: Exit code (0 for success, non-zero for error)
        """
        try:
            logger.info("Starting integrated DeepEcho application...")
            print("Initializing DeepEcho Real-time Voice AI Assistant...")
            
            # Phase 1: Validate dependencies
            print("Phase 1: Validating system dependencies...")
            deps_valid, deps_errors = self.validate_system_dependencies()
            if not deps_valid:
                for error in deps_errors:
                    print(f"ERROR: {error}")
                return 1
            print("✓ Dependencies validated successfully")
            
            # Phase 2: Load configuration
            print("Phase 2: Loading system configuration...")
            if not self.load_and_validate_configuration():
                return 1
            print("✓ Configuration loaded successfully")
            
            # Phase 3: Initialize core systems
            print("Phase 3: Initializing core systems...")
            
            print("  - Initializing audio system...")
            audio_ready = self.initialize_audio_system()
            if audio_ready:
                print("  ✓ Audio system ready")
            else:
                print("  ⚠ Audio system unavailable (continuing with degraded mode)")
            
            print("  - Initializing transcription system...")
            if not self.initialize_transcription_system():
                return 1
            print("  ✓ Transcription system ready")
            
            print("  - Initializing AI system...")
            if not self.initialize_ai_system():
                return 1
            print("  ✓ AI system ready")
            
            print("  - Initializing user interface...")
            if not self.initialize_ui_system():
                return 1
            print("  ✓ User interface ready")
            
            # Phase 4: System ready and integration validation
            self.system_ready.set()
            self.initialization_complete.set()
            
            print("Phase 4: Validating component integration...")
            integration_valid, integration_errors = self.validate_component_integration()
            if not integration_valid:
                print("WARNING: Component integration issues detected:")
                for error in integration_errors:
                    print(f"  - {error}")
                print("System will continue but may have reduced functionality.")
            else:
                print("  ✓ All components properly integrated")
            
            # Run diagnostics
            print("Phase 5: Running system diagnostics...")
            diagnostics = self.run_system_diagnostics()
            logger.info(f"System diagnostics: {diagnostics}")
            
            # Display system status
            print("\n" + "="*60)
            print("SYSTEM STATUS")
            print("="*60)
            for component, status in self.component_status.items():
                status_icon = "✓" if status else "✗"
                print(f"{status_icon} {component.replace('_', ' ').title()}: {'Ready' if status else 'Failed'}")
            
            if diagnostics.get('ai_provider'):
                ai_info = diagnostics['ai_provider']
                print(f"✓ AI Provider: {ai_info['current_provider']}")
            
            if diagnostics.get('configuration'):
                config_info = diagnostics['configuration']
                print(f"✓ Audio Mode: {config_info['audio_mode']}")
                print(f"✓ UI Mode: Integrated")
            
            print("="*60)
            
            # Phase 6: End-to-end functionality test
            print("Phase 6: Testing end-to-end functionality...")
            e2e_success, e2e_results = self.test_end_to_end_functionality()
            if e2e_success:
                print("  ✓ End-to-end functionality test passed")
                for result in e2e_results:
                    print(f"    - {result}")
            else:
                print("  ⚠ End-to-end functionality test issues:")
                for result in e2e_results:
                    print(f"    - {result}")
            
            print("="*60)
            
            # Start resource optimization
            self.resource_optimizer.start_optimization()
            
            logger.info(SUCCESS_MESSAGES["system_ready"])
            print(SUCCESS_MESSAGES["system_ready"])
            print(f"\nAll components initialized: {all(self.component_status.values())}")
            
            # Phase 5: Run main application loop
            print("\nStarting application main loop...")
            if self.main_window:
                self.main_window.run()
            elif hasattr(self, 'root'):
                self.root.mainloop()
            else:
                # Keep the application running
                try:
                    print("Application running. Press Ctrl+C to exit.")
                    while not self.shutdown_event.is_set():
                        time.sleep(0.1)
                        # Periodic health checks
                        if time.time() % 30 < 0.1:  # Every 30 seconds
                            self._perform_health_check()
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt")
                    print("\nShutting down gracefully...")
            
            return 0
            
        except Exception as e:
            logger.error(f"Application error: {e}")
            print(f"ERROR: Application failed to start: {e}")
            return 1
        finally:
            self.cleanup()
    
    def _perform_health_check(self):
        """Perform periodic health checks on system components."""
        try:
            # Check thread health
            dead_threads = self.thread_manager.check_thread_health()
            if dead_threads:
                logger.warning(f"Dead threads detected: {dead_threads}")
                self.error_recovery.handle_thread_failure(dead_threads)
            
            # Check queue health
            queue_status = self.queue_manager.check_queue_health()
            if any(status['size'] > 1000 for status in queue_status.values()):
                logger.warning("Large queue sizes detected, optimizing...")
                self.queue_manager.optimize_queues()
            
            # Check resource usage
            resource_status = self.resource_optimizer.check_resource_usage()
            if resource_status['memory_usage'] > 0.8:
                logger.warning("High memory usage detected, optimizing...")
                self.resource_optimizer.optimize_memory()
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def test_end_to_end_functionality(self) -> Tuple[bool, List[str]]:
        """
        Test end-to-end functionality of the integrated system.
        
        Returns:
            Tuple of (success, test_results)
        """
        logger.info("Testing end-to-end functionality...")
        test_results = []
        
        try:
            # Test 1: Audio system responsiveness
            if self.component_status['audio_system']:
                try:
                    # Check if audio queues are receiving data (after some time)
                    time.sleep(1)  # Give audio system time to start
                    mic_size = self.mic_queue.qsize()
                    speaker_size = self.speaker_queue.qsize()
                    test_results.append(f"Audio queues - Mic: {mic_size}, Speaker: {speaker_size}")
                except Exception as e:
                    test_results.append(f"Audio system test failed: {e}")
            
            # Test 2: Transcription system
            if self.component_status['transcription'] and self.transcriber:
                try:
                    # Check if transcriber is responsive
                    transcript = self.transcriber.get_transcript()
                    test_results.append(f"Transcription system responsive, current length: {len(transcript)}")
                except Exception as e:
                    test_results.append(f"Transcription system test failed: {e}")
            
            # Test 3: AI system
            if self.component_status['ai_system'] and self.ai_adapter:
                try:
                    # Test AI provider
                    provider_name = self.ai_adapter.get_current_provider()
                    test_results.append(f"AI system using provider: {provider_name}")
                    
                    # Test simple response generation (if not dummy provider)
                    if provider_name != "dummy":
                        try:
                            test_response = self.ai_adapter.generate_response("Hello", max_tokens=10)
                            test_results.append(f"AI response test successful: {len(test_response)} chars")
                        except Exception as e:
                            test_results.append(f"AI response test failed: {e}")
                    else:
                        test_results.append("AI system using dummy provider (no real AI)")
                        
                except Exception as e:
                    test_results.append(f"AI system test failed: {e}")
            
            # Test 4: Thread health
            thread_status = self.thread_manager.get_thread_status()
            active_threads = sum(1 for status in thread_status.values() if status['alive'])
            test_results.append(f"Active threads: {active_threads}/{len(thread_status)}")
            
            # Test 5: Resource usage
            resource_status = self.resource_optimizer.get_resource_status()
            test_results.append(f"Memory usage: {resource_status.get('memory_usage', 'unknown')}")
            
            logger.info("End-to-end functionality test completed")
            return True, test_results
            
        except Exception as e:
            logger.error(f"End-to-end test failed: {e}")
            return False, [f"End-to-end test error: {e}"]
    
    def cleanup(self):
        """Clean up resources and shutdown gracefully."""
        logger.info("Starting comprehensive system cleanup...")
        
        # Signal shutdown
        self.shutdown_event.set()
        
        # Stop transcription explicitly
        if self.transcriber:
            try:
                self.transcriber.stop_transcription()
            except Exception as e:
                logger.error(f"Transcriber cleanup error: {e}")
        
        # Stop resource optimization
        if self.resource_optimizer:
            self.resource_optimizer.stop()
        
        # Clean up threads
        self.thread_manager.stop_all_threads(timeout=5.0)
        
        # Clean up queues
        self.queue_manager.stop_all_queues()
        
        # Clean up audio system
        if self.audio_system:
            try:
                self.audio_system.cleanup()
            except Exception as e:
                logger.error(f"Audio system cleanup error: {e}")
        
        # Clean up UI
        if self.main_window:
            try:
                self.main_window.cleanup()
            except Exception as e:
                logger.error(f"UI cleanup error: {e}")
        
        # Clean up AI system
        if self.ai_adapter:
            try:
                self.ai_adapter.cleanup()
            except Exception as e:
                logger.error(f"AI system cleanup error: {e}")
        
        logger.info("System cleanup completed")
    
    def _signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.cleanup()
        sys.exit(0)


def create_integrated_application() -> IntegratedDeepEchoApplication:
    """
    Factory function to create an integrated DeepEcho application.
    
    Returns:
        IntegratedDeepEchoApplication: Configured application instance
    """
    return IntegratedDeepEchoApplication()


def run_integrated_application() -> int:
    """
    Run the integrated DeepEcho application.
    
    Returns:
        int: Exit code
    """
    app = create_integrated_application()
    return app.run()


if __name__ == "__main__":
    sys.exit(run_integrated_application())