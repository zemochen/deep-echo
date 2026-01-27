"""
Audio interface abstract base class

Defines the interface that all platform-specific audio implementations must follow.
"""

from abc import ABC, abstractmethod


class AudioInterface(ABC):
    """
    Abstract base class for platform-specific audio interfaces.
    
    All platform implementations must inherit from this class and
    implement the get_default_speaker method.
    """
    
    @abstractmethod
    def get_default_speaker(self):
        """
        Get the default speaker device for the platform.
        
        Returns:
            dict: Device information dictionary containing device index,
                  sample rate, and other audio device properties
                  
        Raises:
            Exception: If no default speaker device is found
        """
        pass


class AudioSystemInterface(ABC):
    """
    Abstract base class for audio system implementations.
    
    This interface defines the methods that all audio system implementations
    must provide for device management and system integration.
    """
    
    @abstractmethod
    def initialize_devices(self):
        """Initialize audio devices for the system."""
        pass
    
    @abstractmethod
    def get_device_status(self):
        """
        Get the status of audio devices.
        
        Returns:
            dict: Device status information
        """
        pass
    
    @abstractmethod
    def cleanup(self):
        """Clean up audio system resources."""
        pass

