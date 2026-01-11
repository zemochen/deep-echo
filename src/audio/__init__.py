"""
Audio processing layer

This package contains audio recording and transcription functionality.
"""

from src.audio.recorder import (
    BaseRecorder,
    DefaultMicRecorder,
    DefaultSpeakerRecorder,
    AudioRecorderError,
    AudioDeviceNotFoundError,
    AudioRecordingError
)

__all__ = [
    'BaseRecorder',
    'DefaultMicRecorder',
    'DefaultSpeakerRecorder',
    'AudioRecorderError',
    'AudioDeviceNotFoundError',
    'AudioRecordingError'
]
