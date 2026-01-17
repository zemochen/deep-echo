"""
Audio system factory and interface

This package provides platform-specific audio device detection and management.
"""

from src.audio_system.audio_factory import get_audio_device

# Expose public API
def get_default_speaker():
    """Get the default speaker device for the current platform"""
    audio_interface = get_audio_device()
    return audio_interface.get_default_speaker()

__all__ = ['get_default_speaker', 'get_audio_device']
