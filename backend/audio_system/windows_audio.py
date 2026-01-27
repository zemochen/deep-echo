"""
Windows audio implementation

Provides Windows-specific audio device detection using WASAPI loopback devices.
"""

from backend.audio_system.audio_interface import AudioInterface
import pyaudio


class WindowsAudio(AudioInterface):
    """
    Windows implementation of audio interface.
    
    Uses WASAPI loopback devices for speaker output capture.
    Requires PyAudioWPatch >= 0.2.12.6
    """

    def get_default_speaker(self):
        """
        Get default speaker device using WASAPI loopback.
        
        Returns:
            dict: Default speaker loopback device information
            
        Raises:
            Exception: If no loopback device is found
        """
        # Requires PyAudioWPatch >= 0.2.12.6
        with pyaudio.PyAudio() as p:
            wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            
            if not default_speakers["isLoopbackDevice"]:
                for loopback in p.get_loopback_device_info_generator():
                    if default_speakers["name"] in loopback["name"]:
                        default_speakers = loopback
                        break
                else:
                    print("[ERROR] No loopback device found.")
                    return None
                    
            return default_speakers

