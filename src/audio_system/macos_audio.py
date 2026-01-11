"""
macOS audio implementation

Provides macOS-specific audio device detection using BlackHole virtual audio device.
"""

from src.audio_system.audio_interface import AudioInterface
import pyaudio


class MacOSAudio(AudioInterface):
    """
    macOS implementation of audio interface.
    
    Uses BlackHole virtual audio device for speaker output capture.
    BlackHole must be installed separately on the system.
    """
    
    def find_blackhole_device(self, p):
        """
        Find BlackHole virtual audio device.
        
        Args:
            p: PyAudio instance
            
        Returns:
            dict: BlackHole device information
            
        Raises:
            Exception: If BlackHole device is not found
        """
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if "BlackHole" in dev["name"] and dev["maxInputChannels"] > 0:
                print(f"Found BlackHole device: {dev['name']} (Index: {dev['index']})")
                return dev
        raise Exception(
            "BlackHole device not found. Please ensure it is installed and configured.")

    def get_default_speaker(self):
        """
        Get default speaker device using BlackHole.
        
        Returns:
            dict: BlackHole device information
            
        Raises:
            Exception: If BlackHole device is not found
        """
        p = pyaudio.PyAudio()
        try:
            blackhole_device = self.find_blackhole_device(p)
        finally:
            p.terminate()
        return blackhole_device

