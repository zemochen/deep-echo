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

