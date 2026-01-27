"""
Audio device factory

Factory pattern implementation for creating platform-specific audio interfaces.
"""

import platform
from backend.audio_system.audio_interface import AudioSystemInterface
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class AudioSystemFactory:
    """Factory for creating platform-specific audio systems."""
    
    def create_audio_system(self) -> AudioSystemInterface:
        """
        Create the appropriate audio system for the current platform.
        
        Returns:
            AudioSystemInterface: Platform-specific audio system implementation
        """
        system = platform.system()
        logger.info(f"Creating audio system for platform: {system}")
        
        try:
            if system == "Windows":
                from backend.audio_system.windows_audio import WindowsAudioSystem
                return WindowsAudioSystem()
            elif system == "Darwin":  # macOS
                # Try to import MacOSAudioSystem, fall back to GenericAudioSystem
                try:
                    from backend.audio_system.macos_audio import MacOSAudioSystem
                    return MacOSAudioSystem()
                except ImportError:
                    logger.warning("MacOSAudioSystem not found, using generic audio system")
                    return GenericAudioSystem()
            else:
                # Fallback to generic audio system
                logger.warning(f"Unsupported platform {system}, using generic audio system")
                return GenericAudioSystem()
        except ImportError as e:
            logger.warning(f"Failed to import platform-specific audio system: {e}")
            return GenericAudioSystem()


class GenericAudioSystem(AudioSystemInterface):
    """Generic audio system for unsupported platforms or testing."""
    
    def initialize_devices(self):
        """Initialize generic audio devices."""
        logger.info("Initializing generic audio devices")
        
    def get_device_status(self):
        """Get generic device status."""
        return {"status": "generic", "devices": []}
        
    def cleanup(self):
        """Clean up generic audio system."""
        logger.info("Cleaning up generic audio system")


def get_audio_device():
    """
    Get the appropriate audio interface for the current platform.
    
    Returns:
        AudioInterface: Platform-specific audio interface implementation
        
    Raises:
        NotImplementedError: If the current platform is not supported
    """
    system = platform.system()
    if system == "Windows":
        from backend.audio_system.windows_audio import WindowsAudio
        return WindowsAudio()
    elif system == "Darwin":  # macOS
        from backend.audio_system.macos_audio import MacOSAudio
        return MacOSAudio()
    else:
        raise NotImplementedError(f"Unsupported system: {system}")

