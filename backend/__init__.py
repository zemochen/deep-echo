"""
DeepEcho - Real-time Voice AI Assistant

A real-time voice transcription and AI assistant system that captures
microphone and speaker audio, converts speech to text, and generates
intelligent responses using AI models.
"""

__version__ = "0.1.0"
__author__ = "DeepEcho Team"

# Expose custom_speech_recognition for backward compatibility
from . import custom_speech_recognition
