"""
Custom exception classes

Defines application-specific exceptions for better error handling.
"""


class DeepEchoError(Exception):
    """Base exception for all DeepEcho errors"""
    pass


class AudioError(DeepEchoError):
    """Base exception for audio-related errors"""
    pass


class AudioDeviceError(AudioError):
    """Raised when audio device operations fail"""
    pass


class TranscriptionError(DeepEchoError):
    """Raised when transcription operations fail"""
    pass


class AudioTranscriptionError(TranscriptionError):
    """Raised when audio transcription operations fail"""
    pass


class AIProviderError(DeepEchoError):
    """Base exception for AI provider errors"""
    pass


class AIProviderConnectionError(AIProviderError):
    """Raised when AI provider connection fails"""
    pass


class AIProviderResponseError(AIProviderError):
    """Raised when AI provider returns invalid response"""
    pass


class AIProviderTimeoutError(AIProviderError):
    """Raised when AI provider request times out"""
    pass


class AIProviderAuthenticationError(AIProviderError):
    """Raised when AI provider authentication fails"""
    pass


class AIProviderRateLimitError(AIProviderError):
    """Raised when AI provider rate limit is exceeded"""
    pass


class ConfigurationError(DeepEchoError):
    """Raised when configuration is invalid or missing"""
    pass


class UIError(DeepEchoError):
    """Raised when UI operations fail"""
    pass


class AudioSystemError(AudioError):
    """Raised when audio system operations fail"""
    pass


class AISystemError(AIProviderError):
    """Raised when AI system operations fail"""
    pass
