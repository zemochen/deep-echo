from abc import ABC, abstractmethod

class AudioInterface(ABC):
    @abstractmethod
    def get_default_speaker(self):
        pass

