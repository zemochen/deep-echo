"""
Audio device factory

Factory pattern implementation for creating platform-specific audio interfaces.
"""

import platform
from src.audio_system.windows_audio import WindowsAudio
from src.audio_system.macos_audio import MacOSAudio


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
        return WindowsAudio()
    elif system == "Darwin":  # macOS
        return MacOSAudio()
    else:
        raise NotImplementedError(f"Unsupported system: {system}")

