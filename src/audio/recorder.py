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


class AudioRecorderError(Exception):
    """Base exception for audio recorder errors"""
    pass


class AudioDeviceNotFoundError(AudioRecorderError):
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
            logger.error(f"Failed to adjust for ambient noise on {device_name}: {e}")
            raise AudioRecorderError(f"Noise adjustment failed for {device_name}: {e}")

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
                logger.error(f"Error in record callback: {e}")

        try:
            self._stop_listening = self.recorder.listen_in_background(
                self.source, 
                record_callback, 
                phrase_time_limit=RECORD_TIMEOUT
            )
            logger.info("Background recording started successfully")
        except Exception as e:
            logger.error(f"Failed to start background recording: {e}")
            raise AudioRecordingError(f"Background recording failed: {e}")
    
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
            logger.info("Default microphone recorder initialized successfully")
        except OSError as e:
            logger.error(f"Default microphone not found: {e}")
            raise AudioDeviceNotFoundError(f"Default microphone not available: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize default microphone: {e}")
            raise AudioRecorderError(f"Microphone initialization failed: {e}")


class DefaultSpeakerRecorder(BaseRecorder):
    """
    Recorder for default speaker output (loopback recording).
    
    This class handles recording from the system's default speaker output
    using platform-specific loopback devices.
    """

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
                raise AudioDeviceNotFoundError("No default speaker device found")
            
            logger.info(f"Found speaker device: {speaker_info.get('name', 'Unknown')}")
            return speaker_info
        except Exception as e:
            logger.error(f"Failed to get default speaker: {e}")
            raise AudioDeviceNotFoundError(f"Speaker device not available: {e}")

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
            logger.info("Default speaker recorder initialized successfully")
        except AudioDeviceNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to initialize default speaker: {e}")
            raise AudioRecorderError(f"Speaker initialization failed: {e}")
