"""
Audio Recorder Module

This module provides audio recording functionality for microphone and speaker sources.
It handles cross-platform audio device detection and recording with proper error handling.
"""

import custom_speech_recognition as sr
import os
import logging
from datetime import datetime
from typing import Optional, Callable
import queue

from src.audio_system import get_default_speaker
from src.utils.retry import retry_with_backoff, RetryConfig
from src.utils.error_recovery import error_tracker, device_recovery_manager
from src.utils.exceptions import AudioError, AudioDeviceError

try:
    import pyaudiowpatch as pyaudio
except ImportError:
    if os.name != "nt":
        import pyaudio
    else:
        raise

# Configure logging
logger = logging.getLogger(__name__)

# Audio recording constants
RECORD_TIMEOUT = 3
ENERGY_THRESHOLD = 1000
DYNAMIC_ENERGY_THRESHOLD = False


class AudioRecorderError(AudioError):
    """Base exception for audio recorder errors"""
    pass


class AudioDeviceNotFoundError(AudioDeviceError):
    """Raised when audio device is not found"""
    pass


class AudioRecordingError(AudioRecorderError):
    """Raised when audio recording fails"""
    pass


class BaseRecorder:
    """
    Base class for audio recording functionality.
    
    This class provides common audio recording capabilities including
    ambient noise adjustment and background recording into a queue.
    """
    
    def __init__(self, source: sr.Microphone):
        """
        Initialize the base recorder.
        
        Args:
            source: Speech recognition microphone source
            
        Raises:
            ValueError: If source is None
            AudioRecorderError: If recorder initialization fails
        """
        if source is None:
            raise ValueError("audio source can't be None")
        
        try:
            self.recorder = sr.Recognizer()
            self.recorder.energy_threshold = ENERGY_THRESHOLD
            self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD
            self.source = source
            self._stop_listening: Optional[Callable] = None
            logger.info("BaseRecorder initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize BaseRecorder: {e}")
            raise AudioRecorderError(f"Recorder initialization failed: {e}")
    
    def configure(self, record_timeout: int = RECORD_TIMEOUT, 
                  phrase_timeout: float = 3.05,
                  energy_threshold: int = ENERGY_THRESHOLD) -> None:
        """
        Configure audio recording parameters.
        
        Args:
            record_timeout: Recording timeout in seconds
            phrase_timeout: Phrase timeout in seconds
            energy_threshold: Energy threshold for voice detection
        """
        self.recorder.energy_threshold = energy_threshold
        logger.debug(f"Configured recorder: timeout={record_timeout}, "
                    f"phrase_timeout={phrase_timeout}, threshold={energy_threshold}")

    @retry_with_backoff(
        exceptions=(OSError, AudioRecorderError),
        config=RetryConfig(max_attempts=3, base_delay=0.5, backoff_factor=1.5)
    )
    def adjust_for_noise(self, device_name: str, msg: str) -> None:
        """
        Adjust for ambient noise from the audio source.
        
        Args:
            device_name: Name of the audio device
            msg: Message to display during adjustment
            
        Raises:
            AudioRecorderError: If noise adjustment fails
        """
        try:
            logger.info(f"Adjusting for ambient noise from {device_name}. {msg}")
            with self.source:
                self.recorder.adjust_for_ambient_noise(self.source)
            logger.info(f"Completed ambient noise adjustment for {device_name}")
        except Exception as e:
            error = AudioRecorderError(f"Noise adjustment failed for {device_name}: {e}")
            error_tracker.record_error(error, f"audio_recorder_{device_name}")
            logger.error(f"Failed to adjust for ambient noise on {device_name}: {e}")
            raise error

    def record_into_queue(self, audio_queue: queue.Queue) -> None:
        """
        Start recording audio in background and put data into queue.
        
        Args:
            audio_queue: Queue to store audio data tuples (data, timestamp)
            
        Raises:
            AudioRecordingError: If background recording fails to start
        """
        def record_callback(_, audio: sr.AudioData) -> None:
            """Callback function to process recorded audio"""
            try:
                data = audio.get_raw_data()
                audio_queue.put((data, datetime.utcnow()))
            except Exception as e:
                error = AudioRecordingError(f"Error in record callback: {e}")
                error_tracker.record_error(error, "audio_recorder_callback")
                logger.error(f"Error in record callback: {e}")

        try:
            self._stop_listening = self.recorder.listen_in_background(
                self.source, 
                record_callback, 
                phrase_time_limit=RECORD_TIMEOUT
            )
            logger.info("Background recording started successfully")
        except Exception as e:
            error = AudioRecordingError(f"Background recording failed: {e}")
            error_tracker.record_error(error, "audio_recorder_background")
            logger.error(f"Failed to start background recording: {e}")
            raise error
    
    def stop_recording(self) -> None:
        """Stop background recording if active"""
        if self._stop_listening:
            try:
                self._stop_listening(wait_for_stop=False)
                logger.info("Background recording stopped")
            except Exception as e:
                logger.error(f"Error stopping recording: {e}")


class DefaultMicRecorder(BaseRecorder):
    """
    Recorder for default microphone input.
    
    This class handles recording from the system's default microphone device.
    """
    
    def __init__(self):
        """
        Initialize the default microphone recorder.
        
        Raises:
            AudioDeviceNotFoundError: If default microphone is not found
            AudioRecorderError: If initialization fails
        """
        try:
            logger.info("Initializing default microphone recorder")
            source = sr.Microphone(sample_rate=16000)
            super().__init__(source=source)
            self.adjust_for_noise("Default Mic", "Please make some noise from the Default Mic...")
            
            # Register device for recovery
            device_recovery_manager.register_device(
                "default_microphone",
                self._recover_microphone,
                {"device_type": "microphone", "sample_rate": 16000}
            )
            
            logger.info("Default microphone recorder initialized successfully")
        except OSError as e:
            error = AudioDeviceNotFoundError(f"Default microphone not available: {e}")
            error_tracker.record_error(error, "default_microphone", "critical")
            logger.error(f"Default microphone not found: {e}")
            raise error
        except Exception as e:
            error = AudioRecorderError(f"Microphone initialization failed: {e}")
            error_tracker.record_error(error, "default_microphone")
            logger.error(f"Failed to initialize default microphone: {e}")
            raise error
    
    def _recover_microphone(self, device_id: str, error: Exception) -> bool:
        """
        Attempt to recover the microphone device.
        
        Args:
            device_id: Device identifier
            error: Original error that caused failure
            
        Returns:
            True if recovery was successful
        """
        try:
            logger.info(f"Attempting microphone recovery for {device_id}")
            
            # Stop current recording if active
            self.stop_recording()
            
            # Reinitialize microphone source
            new_source = sr.Microphone(sample_rate=16000)
            self.source = new_source
            self.recorder = sr.Recognizer()
            self.recorder.energy_threshold = ENERGY_THRESHOLD
            self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD
            
            # Test the new source
            self.adjust_for_noise("Default Mic (Recovered)", "Testing recovered microphone...")
            
            logger.info("Microphone recovery successful")
            return True
            
        except Exception as recovery_error:
            logger.error(f"Microphone recovery failed: {recovery_error}")
            return False


class DefaultSpeakerRecorder(BaseRecorder):
    """
    Recorder for default speaker output (loopback recording).
    
    This class handles recording from the system's default speaker output
    using platform-specific loopback devices.
    """

    @retry_with_backoff(
        exceptions=(AudioDeviceNotFoundError, OSError),
        config=RetryConfig(max_attempts=3, base_delay=1.0, backoff_factor=2.0)
    )
    def _get_default_speaker(self) -> dict:
        """
        Get default speaker device information using audio_system module.
        
        Returns:
            Dictionary containing speaker device information
            
        Raises:
            AudioDeviceNotFoundError: If speaker device is not found
        """
        try:
            logger.info("Getting default speaker device")
            speaker_info = get_default_speaker()
            
            if speaker_info is None:
                error = AudioDeviceNotFoundError("No default speaker device found")
                error_tracker.record_error(error, "default_speaker")
                raise error
            
            logger.info(f"Found speaker device: {speaker_info.get('name', 'Unknown')}")
            return speaker_info
        except Exception as e:
            if not isinstance(e, AudioDeviceNotFoundError):
                error = AudioDeviceNotFoundError(f"Speaker device not available: {e}")
                error_tracker.record_error(error, "default_speaker")
                logger.error(f"Failed to get default speaker: {e}")
                raise error
            else:
                raise e

    def __init__(self):
        """
        Initialize the default speaker recorder.
        
        Raises:
            AudioDeviceNotFoundError: If default speaker is not found
            AudioRecorderError: If initialization fails
        """
        try:
            logger.info("Initializing default speaker recorder")
            default_speakers = self._get_default_speaker()
            
            source = sr.Microphone(
                speaker=True,
                device_index=default_speakers["index"],
                sample_rate=int(default_speakers["defaultSampleRate"]),
                chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                channels=default_speakers["maxInputChannels"]
            )
            
            super().__init__(source=source)
            self.adjust_for_noise("Default Speaker", "Please make or play some noise from the Default Speaker...")
            
            # Register device for recovery
            device_recovery_manager.register_device(
                "default_speaker",
                self._recover_speaker,
                {
                    "device_type": "speaker",
                    "device_index": default_speakers["index"],
                    "sample_rate": default_speakers["defaultSampleRate"],
                    "channels": default_speakers["maxInputChannels"]
                }
            )
            
            logger.info("Default speaker recorder initialized successfully")
        except AudioDeviceNotFoundError:
            raise
        except Exception as e:
            error = AudioRecorderError(f"Speaker initialization failed: {e}")
            error_tracker.record_error(error, "default_speaker")
            logger.error(f"Failed to initialize default speaker: {e}")
            raise error
    
    def _recover_speaker(self, device_id: str, error: Exception) -> bool:
        """
        Attempt to recover the speaker device.
        
        Args:
            device_id: Device identifier
            error: Original error that caused failure
            
        Returns:
            True if recovery was successful
        """
        try:
            logger.info(f"Attempting speaker recovery for {device_id}")
            
            # Stop current recording if active
            self.stop_recording()
            
            # Get fresh speaker information
            default_speakers = self._get_default_speaker()
            
            # Reinitialize speaker source
            new_source = sr.Microphone(
                speaker=True,
                device_index=default_speakers["index"],
                sample_rate=int(default_speakers["defaultSampleRate"]),
                chunk_size=pyaudio.get_sample_size(pyaudio.paInt16),
                channels=default_speakers["maxInputChannels"]
            )
            
            self.source = new_source
            self.recorder = sr.Recognizer()
            self.recorder.energy_threshold = ENERGY_THRESHOLD
            self.recorder.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD
            
            # Test the new source
            self.adjust_for_noise("Default Speaker (Recovered)", "Testing recovered speaker...")
            
            # Update device state
            device_recovery_manager.update_device_state(device_id, {
                "device_index": default_speakers["index"],
                "sample_rate": default_speakers["defaultSampleRate"],
                "channels": default_speakers["maxInputChannels"],
                "last_recovery": datetime.now().isoformat()
            })
            
            logger.info("Speaker recovery successful")
            return True
            
        except Exception as recovery_error:
            logger.error(f"Speaker recovery failed: {recovery_error}")
            return False
