"""
Message Handler for IPC Communication.

This module handles incoming messages from the Tauri frontend and routes them
to the appropriate backend functions.
"""

import json
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from backend.utils.logger import get_logger
from backend.ipc.event_emitter import get_event_emitter

logger = get_logger(__name__)


class MessageHandler:
    """
    Message handler for processing IPC commands from Tauri frontend.
    
    This class routes incoming commands to the appropriate handler functions
    and manages the request/response cycle.
    """
    
    def __init__(self):
        """Initialize the message handler."""
        self._handlers: Dict[str, Callable] = {}
        
        # Backend component instances
        self._mic_recorder: Optional[Any] = None
        self._speaker_recorder: Optional[Any] = None
        self._transcriber: Optional[Any] = None
        self._ai_adapter: Optional[Any] = None
        self._config_manager: Optional[Any] = None
        
        # Audio queues for recording
        self._mic_queue: Optional[Any] = None
        self._speaker_queue: Optional[Any] = None
        
        # Recording state
        self._is_recording = False
        self._recording_device_type: Optional[str] = None
        
        # Get event emitter for listening to events
        self._event_emitter = get_event_emitter()
        
        self._register_default_handlers()
        self._register_event_listeners()
        logger.info("Message handler initialized")
    
    def _register_default_handlers(self) -> None:
        """Register default command handlers."""
        # Audio commands
        self.register_handler("start_recording", self._handle_start_recording)
        self.register_handler("stop_recording", self._handle_stop_recording)
        self.register_handler("get_transcript", self._handle_get_transcript)
        self.register_handler("get_audio_devices", self._handle_get_audio_devices)
        self.register_handler("set_audio_device", self._handle_set_audio_device)
        
        # AI commands
        self.register_handler("generate_response", self._handle_generate_response)
        self.register_handler("switch_provider", self._handle_switch_provider)
        
        # Config commands
        self.register_handler("get_config", self._handle_get_config)
        self.register_handler("update_config", self._handle_update_config)
        
        # System commands
        self.register_handler("get_system_info", self._handle_get_system_info)
        self.register_handler("ping", self._handle_ping)
        self.register_handler("clear_transcript", self._handle_clear_transcript)
        
        logger.debug(f"Registered {len(self._handlers)} command handlers")
    
    def _register_event_listeners(self) -> None:
        """Register event listeners for backend events."""
        # Register listeners for various event types
        self._event_emitter.add_listener("transcript-updated", self._on_transcript_updated)
        self._event_emitter.add_listener("response-generated", self._on_response_generated)
        self._event_emitter.add_listener("audio-started", self._on_audio_started)
        self._event_emitter.add_listener("audio-stopped", self._on_audio_stopped)
        self._event_emitter.add_listener("error-occurred", self._on_error_occurred)
        
        logger.debug("Event listeners registered")
    
    def set_ipc_server(self, ipc_server) -> None:
        """
        Set the IPC server reference for event forwarding.
        
        Args:
            ipc_server: IPC server instance
        """
        self._ipc_server = ipc_server
        logger.debug("IPC server reference set for event forwarding")
    
    def _on_transcript_updated(self, data: Any) -> None:
        """
        Handle transcript-updated event.
        
        Args:
            data: Transcript data
        """
        logger.debug(f"Transcript updated event received: {data.get('source', 'unknown')}")
        # Event forwarding is handled by the event emitter processing loop
    
    def _on_response_generated(self, data: Any) -> None:
        """
        Handle response-generated event.
        
        Args:
            data: Response data
        """
        logger.debug(f"Response generated event received from {data.get('provider', 'unknown')}")
        # Event forwarding is handled by the event emitter processing loop
    
    def _on_audio_started(self, data: Any) -> None:
        """
        Handle audio-started event.
        
        Args:
            data: Event data
        """
        logger.debug("Audio started event received")
        # Event forwarding is handled by the event emitter processing loop
    
    def _on_audio_stopped(self, data: Any) -> None:
        """
        Handle audio-stopped event.
        
        Args:
            data: Event data
        """
        logger.debug("Audio stopped event received")
        # Event forwarding is handled by the event emitter processing loop
    
    def _on_error_occurred(self, data: Any) -> None:
        """
        Handle error-occurred event.
        
        Args:
            data: Error data
        """
        logger.warning(f"Error event received: {data.get('error', 'unknown error')}")
        # Event forwarding is handled by the event emitter processing loop
    
    def register_handler(self, command: str, handler: Callable) -> None:
        """
        Register a command handler.
        
        Args:
            command: Command name
            handler: Handler function
        """
        self._handlers[command] = handler
        logger.debug(f"Registered handler for command: {command}")
    
    def handle_message(self, message: str) -> str:
        """
        Handle an incoming message from the frontend.
        
        Args:
            message: JSON-encoded message string
            
        Returns:
            JSON-encoded response string
        """
        try:
            # Parse incoming message
            request = json.loads(message)
            command = request.get("command")
            params = request.get("params", {})
            request_id = request.get("id")
            
            logger.debug(f"Handling command: {command} (id: {request_id})")
            
            # Validate command
            if not command:
                return self._create_error_response(
                    "Missing command field",
                    request_id=request_id
                )
            
            # Get handler
            handler = self._handlers.get(command)
            if not handler:
                return self._create_error_response(
                    f"Unknown command: {command}",
                    request_id=request_id
                )
            
            # Execute handler
            result = handler(params)
            
            # Create success response
            return self._create_success_response(result, request_id=request_id)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON message: {e}")
            return self._create_error_response(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            return self._create_error_response(f"Internal error: {str(e)}")
    
    def _create_success_response(self, data: Any, request_id: Optional[str] = None) -> str:
        """
        Create a success response.
        
        Args:
            data: Response data
            request_id: Optional request ID
            
        Returns:
            JSON-encoded response
        """
        response = {
            "status": "success",
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request_id:
            response["id"] = request_id
        
        return json.dumps(response)
    
    def _create_error_response(self, error: str, request_id: Optional[str] = None) -> str:
        """
        Create an error response.
        
        Args:
            error: Error message
            request_id: Optional request ID
            
        Returns:
            JSON-encoded response
        """
        response = {
            "status": "error",
            "error": error,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if request_id:
            response["id"] = request_id
        
        return json.dumps(response)
    
    # ========== Audio Command Handlers ==========
    
    def _handle_start_recording(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle start_recording command.
        
        Args:
            params: Command parameters (device_type: "microphone" or "speaker")
            
        Returns:
            Response data
        """
        device_type = params.get("device_type", "microphone")
        logger.info(f"Start recording requested for device: {device_type}")
        
        try:
            # Import required modules
            from backend.audio.recorder import DefaultMicRecorder, DefaultSpeakerRecorder
            import queue
            
            # Check if already recording
            if self._is_recording:
                return {
                    "message": f"Already recording {self._recording_device_type}",
                    "device_type": self._recording_device_type,
                    "status": "recording"
                }
            
            # Initialize both recorders and queues if not already done
            if not self._mic_recorder:
                self._mic_recorder = DefaultMicRecorder()
                self._mic_queue = queue.Queue()
                logger.info("Microphone recorder initialized")
            
            if not self._speaker_recorder:
                self._speaker_recorder = DefaultSpeakerRecorder()
                self._speaker_queue = queue.Queue()
                logger.info("Speaker recorder initialized")
            
            # Initialize transcriber if not already done
            if not self._transcriber:
                logger.info("Initializing transcriber...")
                from backend.audio.transcriber import AudioTranscriber
                from backend.audio.models import FasterWhisperTranscriber
                from backend.config.config_manager import get_config_manager
                import backend.custom_speech_recognition as sr
                from backend.audio_system import get_default_speaker
                
                # Get configuration
                config_manager = get_config_manager()
                config = config_manager.get_current_config()
                
                # Initialize transcription model
                model = FasterWhisperTranscriber(
                    model_name=config.audio.whisper_model
                )
                
                # Create transcriber with mic and speaker sources
                mic_source = sr.Microphone(sample_rate=16000)
                
                # Get speaker source info
                speaker_info = get_default_speaker()
                
                try:
                    import pyaudiowpatch as pyaudio
                except ImportError:
                    import pyaudio
                
                speaker_source = sr.Microphone(
                    speaker=True,
                    device_index=speaker_info["index"],
                    sample_rate=int(speaker_info["defaultSampleRate"]),
                    chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                    channels=speaker_info["maxInputChannels"]
                )
                
                self._transcriber = AudioTranscriber(mic_source, speaker_source, model)
                logger.info("Transcriber initialized successfully")
                
                # Start transcription immediately with the queues
                self._transcriber.start_transcription(self._speaker_queue, self._mic_queue)
                logger.info("Transcription started")
            
            # Start recording based on device type
            if device_type == "microphone":
                # Start recording into queue
                self._mic_recorder.record_into_queue(self._mic_queue)
                logger.info("Microphone recording started")
                
            elif device_type == "speaker":
                # Start recording into queue
                self._speaker_recorder.record_into_queue(self._speaker_queue)
                logger.info("Speaker recording started")
                
            else:
                return {
                    "error": f"Invalid device type: {device_type}",
                    "status": "error"
                }
            
            self._is_recording = True
            self._recording_device_type = device_type
            
            return {
                "message": f"Recording started for {device_type}",
                "device_type": device_type,
                "status": "recording"
            }
            
        except Exception as e:
            logger.error(f"Failed to start recording: {e}", exc_info=True)
            return {
                "error": f"Failed to start recording: {str(e)}",
                "status": "error"
            }
    
    def _handle_stop_recording(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle stop_recording command.
        
        Args:
            params: Command parameters
            
        Returns:
            Response data
        """
        logger.info("Stop recording requested")
        
        try:
            if not self._is_recording:
                return {
                    "message": "No active recording",
                    "status": "stopped"
                }
            
            # Stop the appropriate recorder
            if self._recording_device_type == "microphone" and self._mic_recorder:
                self._mic_recorder.stop_recording()
                logger.info("Microphone recording stopped")
                
            elif self._recording_device_type == "speaker" and self._speaker_recorder:
                self._speaker_recorder.stop_recording()
                logger.info("Speaker recording stopped")
            
            self._is_recording = False
            stopped_device = self._recording_device_type
            self._recording_device_type = None
            
            return {
                "message": f"Recording stopped for {stopped_device}",
                "device_type": stopped_device,
                "status": "stopped"
            }
            
        except Exception as e:
            logger.error(f"Failed to stop recording: {e}", exc_info=True)
            return {
                "error": f"Failed to stop recording: {str(e)}",
                "status": "error"
            }
    
    def _handle_get_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_transcript command.
        
        Args:
            params: Command parameters
            
        Returns:
            Response data with transcript
        """
        logger.debug("Get transcript requested")
        
        try:
            # Check if transcriber is initialized
            if not self._transcriber:
                return {
                    "transcript": "",
                    "entries": [],
                    "timestamp": datetime.utcnow().isoformat(),
                    "message": "Transcriber not initialized - start recording first"
                }
            
            # Get transcript data
            transcript_text = self._transcriber.get_transcript()
            
            # Get individual entries
            mic_entries = self._transcriber.get_mic_transcript()
            speaker_entries = self._transcriber.get_speaker_transcript()
            
            # Format entries for response
            entries = []
            for text, timestamp in mic_entries:
                entries.append({
                    "source": "microphone",
                    "text": text,
                    "timestamp": timestamp.isoformat()
                })
            for text, timestamp in speaker_entries:
                entries.append({
                    "source": "speaker",
                    "text": text,
                    "timestamp": timestamp.isoformat()
                })
            
            # Sort by timestamp (newest first)
            entries.sort(key=lambda x: x["timestamp"], reverse=True)
            
            return {
                "transcript": transcript_text,
                "entries": entries[:50],  # Limit to 50 most recent
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get transcript: {e}", exc_info=True)
            return {
                "error": f"Failed to get transcript: {str(e)}",
                "transcript": "",
                "entries": [],
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _handle_get_audio_devices(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_audio_devices command.
        
        Args:
            params: Command parameters
            
        Returns:
            Response data with available audio devices
        """
        logger.debug("Get audio devices requested")
        
        try:
            import backend.custom_speech_recognition as sr
            from backend.audio_system import get_default_speaker
            
            microphones = []
            speakers = []
            
            # Get microphone devices
            try:
                mic_list = sr.Microphone.list_microphone_names()
                for idx, name in enumerate(mic_list):
                    microphones.append({
                        "id": str(idx),
                        "name": name,
                        "deviceType": "microphone",
                        "is_default": idx == 0
                    })
                logger.debug(f"Found {len(microphones)} microphone devices")
            except Exception as e:
                logger.warning(f"Failed to enumerate microphones: {e}")
            
            # Get speaker device (loopback)
            try:
                speaker_info = get_default_speaker()
                if speaker_info:
                    speakers.append({
                        "id": str(speaker_info.get("index", 0)),
                        "name": speaker_info.get("name", "Default Speaker"),
                        "deviceType": "speaker",
                        "is_default": True,
                        "sample_rate": speaker_info.get("defaultSampleRate"),
                        "channels": speaker_info.get("maxInputChannels")
                    })
                logger.debug(f"Found {len(speakers)} speaker devices")
            except Exception as e:
                logger.warning(f"Failed to get speaker device: {e}")
            
            return {
                "microphones": microphones,
                "speakers": speakers
            }
            
        except Exception as e:
            logger.error(f"Failed to get audio devices: {e}", exc_info=True)
            return {
                "error": f"Failed to get audio devices: {str(e)}",
                "microphones": [],
                "speakers": []
            }
    
    def _handle_set_audio_device(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle set_audio_device command.
        
        Args:
            params: Command parameters (device_type, device_id)
            
        Returns:
            Response data
        """
        device_type = params.get("device_type")
        device_id = params.get("device_id")
        
        logger.info(f"Set audio device: type={device_type}, id={device_id}")
        
        try:
            # Stop current recording if active
            if self._is_recording:
                self._handle_stop_recording({})
            
            # Reset the appropriate recorder to force reinitialization with new device
            if device_type == "microphone":
                self._mic_recorder = None
                self._mic_queue = None
                logger.info(f"Microphone device will be reinitialized on next recording")
                
            elif device_type == "speaker":
                self._speaker_recorder = None
                self._speaker_queue = None
                logger.info(f"Speaker device will be reinitialized on next recording")
            else:
                return {
                    "error": f"Invalid device type: {device_type}",
                    "status": "error"
                }
            
            return {
                "message": f"Audio device set: {device_type}",
                "device_type": device_type,
                "device_id": device_id,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Failed to set audio device: {e}", exc_info=True)
            return {
                "error": f"Failed to set audio device: {str(e)}",
                "status": "error"
            }
    
    # ========== AI Command Handlers ==========
    
    def _handle_generate_response(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle generate_response command.
        
        Args:
            params: Command parameters (context)
            
        Returns:
            Response data with AI-generated response
        """
        context = params.get("context", "")
        logger.info(f"Generate response requested (context length: {len(context)})")
        
        try:
            # Initialize AI adapter if not already done
            if not self._ai_adapter:
                from backend.ai.adapter import AIAdapter
                from backend.config.config_manager import get_config_manager
                
                # Get configuration
                config_manager = get_config_manager()
                config = config_manager.get_current_config()
                
                # Create AI provider
                self._ai_adapter = AIAdapter()
                provider = self._ai_adapter.create_provider(
                    provider_type=config.ai_provider.provider_type,
                    api_key=config.ai_provider.api_key,
                    model=config.ai_provider.model,
                    base_url=config.ai_provider.base_url,
                    timeout=config.ai_provider.timeout
                )
                self._ai_adapter.set_provider(provider)
                logger.info(f"AI adapter initialized with {config.ai_provider.provider_type}")
            
            # Generate response
            response_text = self._ai_adapter.generate_response(context)
            
            return {
                "response": response_text,
                "provider": self._ai_adapter.get_current_provider(),
                "model": self._ai_adapter.get_current_model(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate response: {e}", exc_info=True)
            return {
                "error": f"Failed to generate response: {str(e)}",
                "response": "",
                "provider": "unknown",
                "model": "unknown",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _handle_switch_provider(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle switch_provider command.
        
        Args:
            params: Command parameters (provider, model)
            
        Returns:
            Response data
        """
        provider = params.get("provider")
        model = params.get("model")
        api_key = params.get("api_key")
        
        logger.info(f"Switch provider requested: {provider} (model: {model})")
        
        try:
            # Initialize AI adapter if not already done
            if not self._ai_adapter:
                from backend.ai.adapter import AIAdapter
                self._ai_adapter = AIAdapter()
            
            # Get API key from config if not provided
            if not api_key:
                from backend.config.config_manager import get_config_manager
                config_manager = get_config_manager()
                
                # Try to get API key from current config or update config
                current_config = config_manager.get_current_config()
                if current_config.ai_provider.provider_type == provider:
                    api_key = current_config.ai_provider.api_key
                else:
                    # Need API key to switch to new provider
                    return {
                        "error": "API key required to switch to new provider",
                        "status": "error"
                    }
            
            # Switch provider
            self._ai_adapter.switch_provider(
                provider_type=provider,
                api_key=api_key,
                model=model
            )
            
            # Update configuration
            from backend.config.config_manager import get_config_manager
            config_manager = get_config_manager()
            success, messages = config_manager.update_ai_provider(
                provider_type=provider,
                api_key=api_key,
                model=model
            )
            
            if success:
                logger.info(f"Successfully switched to {provider}")
                return {
                    "message": f"Switched to provider: {provider}",
                    "provider": provider,
                    "model": model,
                    "status": "success"
                }
            else:
                logger.warning(f"Provider switched but config update failed: {messages}")
                return {
                    "message": f"Switched to provider: {provider} (config update failed)",
                    "provider": provider,
                    "model": model,
                    "status": "partial_success",
                    "warnings": messages
                }
            
        except Exception as e:
            logger.error(f"Failed to switch provider: {e}", exc_info=True)
            return {
                "error": f"Failed to switch provider: {str(e)}",
                "status": "error"
            }
    
    # ========== Config Command Handlers ==========
    
    def _handle_get_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_config command.
        
        Args:
            params: Command parameters
            
        Returns:
            Response data with configuration
        """
        logger.debug("Get config requested")
        
        try:
            # Initialize config manager if not already done
            if not self._config_manager:
                from backend.config.config_manager import get_config_manager
                self._config_manager = get_config_manager()
            
            # Get current configuration
            config = self._config_manager.get_current_config()
            
            # Convert to dictionary format for response
            return {
                "audio": {
                    "recordTimeout": config.audio.record_timeout,
                    "phraseTimeout": config.audio.phrase_timeout,
                    "maxPhrases": config.audio.max_phrases,
                    "energyThreshold": config.audio.energy_threshold,
                    "useApiMode": config.audio.use_api_mode,
                    "whisperModel": config.audio.whisper_model,
                    "whisperModelPath": config.audio.whisper_model_path
                },
                "ai": {
                    "provider": config.ai_provider.provider_type,
                    "model": config.ai_provider.model,
                    "baseUrl": config.ai_provider.base_url,
                    "timeout": config.ai_provider.timeout,
                    "maxRetries": config.ai_provider.max_retries
                },
                "ui": {
                    "updateInterval": config.ui.update_interval,
                    "processingInterval": config.ui.processing_interval,
                    "uiUpdateInterval": config.ui.ui_update_interval,
                    "useNewUi": config.ui.use_new_ui
                },
                "defaultProvider": config.default_provider
            }
            
        except Exception as e:
            logger.error(f"Failed to get config: {e}", exc_info=True)
            return {
                "error": f"Failed to get config: {str(e)}",
                "audio": {},
                "ai": {},
                "ui": {}
            }
    
    def _handle_update_config(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle update_config command.
        
        Args:
            params: Command parameters (config object)
            
        Returns:
            Response data
        """
        config_updates = params.get("config", {})
        logger.info(f"Update config requested: {list(config_updates.keys())}")
        
        try:
            # Initialize config manager if not already done
            if not self._config_manager:
                from backend.config.config_manager import get_config_manager
                self._config_manager = get_config_manager()
            
            updated_fields = []
            
            # Update audio configuration
            if "audio" in config_updates:
                audio_config = config_updates["audio"]
                audio_updates = {}
                
                # Map frontend field names to backend field names
                field_mapping = {
                    "recordTimeout": "record_timeout",
                    "phraseTimeout": "phrase_timeout",
                    "maxPhrases": "max_phrases",
                    "energyThreshold": "energy_threshold",
                    "useApiMode": "use_api_mode",
                    "whisperModel": "whisper_model",
                    "whisperModelPath": "whisper_model_path"
                }
                
                for frontend_key, backend_key in field_mapping.items():
                    if frontend_key in audio_config:
                        audio_updates[backend_key] = audio_config[frontend_key]
                
                if audio_updates:
                    success = self._config_manager.update_audio_config(**audio_updates)
                    if success:
                        updated_fields.extend(audio_updates.keys())
                        logger.info(f"Audio config updated: {list(audio_updates.keys())}")
            
            # Update UI configuration
            if "ui" in config_updates:
                ui_config = config_updates["ui"]
                ui_updates = {}
                
                # Map frontend field names to backend field names
                field_mapping = {
                    "updateInterval": "update_interval",
                    "processingInterval": "processing_interval",
                    "uiUpdateInterval": "ui_update_interval",
                    "useNewUi": "use_new_ui"
                }
                
                for frontend_key, backend_key in field_mapping.items():
                    if frontend_key in ui_config:
                        ui_updates[backend_key] = ui_config[frontend_key]
                
                if ui_updates:
                    success = self._config_manager.update_ui_config(**ui_updates)
                    if success:
                        updated_fields.extend(ui_updates.keys())
                        logger.info(f"UI config updated: {list(ui_updates.keys())}")
            
            # Update AI provider configuration
            if "ai" in config_updates:
                ai_config = config_updates["ai"]
                if "provider" in ai_config:
                    provider = ai_config["provider"]
                    model = ai_config.get("model")
                    api_key = ai_config.get("apiKey")
                    
                    if api_key:
                        success, messages = self._config_manager.update_ai_provider(
                            provider_type=provider,
                            api_key=api_key,
                            model=model
                        )
                        if success:
                            updated_fields.append("ai_provider")
                            logger.info(f"AI provider updated to {provider}")
                            
                            # Also update the AI adapter if it exists
                            if self._ai_adapter:
                                try:
                                    self._ai_adapter.switch_provider(
                                        provider_type=provider,
                                        api_key=api_key,
                                        model=model
                                    )
                                except Exception as e:
                                    logger.warning(f"Failed to update AI adapter: {e}")
            
            if updated_fields:
                return {
                    "message": "Configuration updated successfully",
                    "updated_fields": updated_fields,
                    "status": "success"
                }
            else:
                return {
                    "message": "No configuration fields updated",
                    "updated_fields": [],
                    "status": "success"
                }
            
        except Exception as e:
            logger.error(f"Failed to update config: {e}", exc_info=True)
            return {
                "error": f"Failed to update config: {str(e)}",
                "status": "error"
            }
    
    # ========== System Command Handlers ==========
    
    def _handle_get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle get_system_info command.
        
        Args:
            params: Command parameters
            
        Returns:
            Response data with system information
        """
        import platform
        import sys
        
        logger.debug("Get system info requested")
        
        return {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "python_version": sys.version,
            "architecture": platform.machine(),
            "hostname": platform.node()
        }
    
    def _handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle ping command for health check.
        
        Args:
            params: Command parameters
            
        Returns:
            Response data
        """
        return {
            "message": "pong",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _handle_clear_transcript(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle clear_transcript command.
        
        Args:
            params: Command parameters
            
        Returns:
            Response data
        """
        try:
            if self._transcriber:
                self._transcriber.clear_transcript_data()
                logger.info("Transcript data cleared")
                return {
                    "message": "Transcript cleared successfully",
                    "status": "success"
                }
            else:
                return {
                    "message": "No transcriber initialized",
                    "status": "success"
                }
        except Exception as e:
            logger.error(f"Failed to clear transcript: {e}", exc_info=True)
            return {
                "error": f"Failed to clear transcript: {str(e)}",
                "status": "error"
            }
    
    def get_registered_commands(self) -> list:
        """
        Get list of registered commands.
        
        Returns:
            List of command names
        """
        return list(self._handlers.keys())
    
    def cleanup(self) -> None:
        """
        Clean up message handler resources.
        
        This method stops all active recordings and transcriptions,
        and releases resources.
        """
        try:
            logger.info("Cleaning up message handler resources")
            
            # Stop recording if active
            if self._is_recording:
                self._handle_stop_recording({})
            
            # Stop transcription if active
            if self._transcriber:
                try:
                    self._transcriber.stop_transcription()
                except Exception as e:
                    logger.warning(f"Error stopping transcription: {e}")
            
            # Clean up AI adapter
            if self._ai_adapter:
                try:
                    self._ai_adapter.cleanup()
                except Exception as e:
                    logger.warning(f"Error cleaning up AI adapter: {e}")
            
            # Clear references
            self._mic_recorder = None
            self._speaker_recorder = None
            self._transcriber = None
            self._ai_adapter = None
            self._config_manager = None
            self._mic_queue = None
            self._speaker_queue = None
            
            logger.info("Message handler cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during message handler cleanup: {e}", exc_info=True)
