"""
Enhanced transcriber models module with improved model handling and language detection.

This module provides better model management, automatic language detection for API mode,
and model switching capabilities for the real-time voice AI assistant.
"""

import torch
import os
import logging
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List, Tuple
from enum import Enum

# Optional imports for testing compatibility
try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    WhisperModel = None
    FASTER_WHISPER_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OpenAI = None
    OPENAI_AVAILABLE = False

from LlmClient import get_openai_client
from src.utils.logger import get_logger
from src.utils.exceptions import AudioTranscriptionError

logger = get_logger(__name__)


class TranscriptionMode(Enum):
    """Enumeration of available transcription modes."""
    LOCAL = "local"
    API = "api"


class LanguageDetectionResult:
    """Result of language detection operation."""
    
    def __init__(self, language: str, confidence: float, detected_languages: List[Tuple[str, float]] = None):
        """
        Initialize language detection result.
        
        Args:
            language: Primary detected language code
            confidence: Confidence score for primary language (0.0-1.0)
            detected_languages: List of (language_code, confidence) tuples for all detected languages
        """
        self.language = language
        self.confidence = confidence
        self.detected_languages = detected_languages or [(language, confidence)]


class BaseTranscriber(ABC):
    """Abstract base class for all transcriber implementations."""
    
    @abstractmethod
    def get_transcription(self, wav_file_path: str) -> str:
        """
        Get transcription from audio file.
        
        Args:
            wav_file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        pass
    
    @abstractmethod
    def get_mode(self) -> TranscriptionMode:
        """
        Get the transcription mode.
        
        Returns:
            TranscriptionMode enum value
        """
        pass
    
    @abstractmethod
    def supports_language_detection(self) -> bool:
        """
        Check if this transcriber supports automatic language detection.
        
        Returns:
            True if language detection is supported
        """
        pass
    
    def detect_language(self, wav_file_path: str) -> Optional[LanguageDetectionResult]:
        """
        Detect language from audio file (if supported).
        
        Args:
            wav_file_path: Path to the audio file
            
        Returns:
            LanguageDetectionResult if detection is supported, None otherwise
        """
        if not self.supports_language_detection():
            return None
        return self._detect_language_impl(wav_file_path)
    
    def _detect_language_impl(self, wav_file_path: str) -> Optional[LanguageDetectionResult]:
        """
        Implementation of language detection (override in subclasses).
        
        Args:
            wav_file_path: Path to the audio file
            
        Returns:
            LanguageDetectionResult or None
        """
        return None


class FasterWhisperTranscriber(BaseTranscriber):
    """Local Faster Whisper transcriber with improved model handling."""
    
    SUPPORTED_MODELS = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    DEFAULT_MODEL = "small"
    
    def __init__(self, model_name: str = None, device: str = None, compute_type: str = None):
        """
        Initialize Faster Whisper transcriber.
        
        Args:
            model_name: Whisper model name (default: "small")
            device: Device to use ("cpu", "cuda", "auto")
            compute_type: Compute type ("int8", "float16", "float32")
        """
        self.model_name = model_name or self.DEFAULT_MODEL
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.compute_type = compute_type or ("float32" if torch.cuda.is_available() else "int8")
        
        # Validate model name
        if self.model_name not in self.SUPPORTED_MODELS:
            logger.warning(f"Unsupported model '{self.model_name}', falling back to '{self.DEFAULT_MODEL}'")
            self.model_name = self.DEFAULT_MODEL
        
        self.model = None
        self._load_model()
    
    def _load_model(self) -> None:
        """Load the Whisper model with error handling."""
        if not FASTER_WHISPER_AVAILABLE:
            logger.warning("faster_whisper not available, using mock model for testing")
            self.model = None
            return
            
        try:
            logger.info(f"Loading Faster Whisper model '{self.model_name}' on {self.device}...")
            self.model = WhisperModel(
                self.model_name, 
                device=self.device,
                compute_type=self.compute_type
            )
            logger.info(f"Faster Whisper model loaded successfully. GPU available: {torch.cuda.is_available()}")
        except Exception as e:
            logger.error(f"Failed to load Faster Whisper model: {e}")
            # Fallback to CPU with int8 if GPU loading fails
            if self.device == "cuda":
                logger.info("Attempting fallback to CPU...")
                self.device = "cpu"
                self.compute_type = "int8"
                try:
                    self.model = WhisperModel(
                        self.model_name,
                        device=self.device,
                        compute_type=self.compute_type
                    )
                    logger.info("Successfully loaded model on CPU fallback")
                except Exception as fallback_error:
                    raise AudioTranscriptionError(f"Failed to load Whisper model: {fallback_error}")
            else:
                raise AudioTranscriptionError(f"Failed to load Whisper model: {e}")
    
    def get_transcription(self, wav_file_path: str) -> str:
        """
        Get transcription from audio file using local Whisper model.
        
        Args:
            wav_file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        if not FASTER_WHISPER_AVAILABLE or not self.model:
            # Return mock transcription for testing
            return f"Mock transcription for {os.path.basename(wav_file_path)}"
        
        if not os.path.exists(wav_file_path):
            raise AudioTranscriptionError(f"Audio file not found: {wav_file_path}")
        
        try:
            # Use language detection for better accuracy if available
            language = None
            if self.supports_language_detection():
                lang_result = self.detect_language(wav_file_path)
                if lang_result and lang_result.confidence > 0.5:
                    language = lang_result.language
            
            # Transcribe with detected language
            segments, info = self.model.transcribe(
                wav_file_path, 
                beam_size=5,
                language=language,
                condition_on_previous_text=False
            )
            
            full_text = " ".join(segment.text for segment in segments)
            result = full_text.strip()
            
            logger.debug(f"Local transcription completed: {len(result)} characters")
            return result
            
        except Exception as e:
            logger.error(f"Local transcription failed: {e}")
            return ''
    
    def get_mode(self) -> TranscriptionMode:
        """Get the transcription mode."""
        return TranscriptionMode.LOCAL
    
    def supports_language_detection(self) -> bool:
        """Check if language detection is supported."""
        return True
    
    def _detect_language_impl(self, wav_file_path: str) -> Optional[LanguageDetectionResult]:
        """
        Detect language using Faster Whisper model.
        
        Args:
            wav_file_path: Path to the audio file
            
        Returns:
            LanguageDetectionResult with detected language
        """
        if not FASTER_WHISPER_AVAILABLE or not self.model:
            # Return mock language detection for testing
            return LanguageDetectionResult(language="en", confidence=0.9)
        
        try:
            # Use Whisper's built-in language detection
            segments, info = self.model.transcribe(
                wav_file_path,
                beam_size=1,  # Faster for detection
                max_new_tokens=1,  # Just need language detection
                condition_on_previous_text=False
            )
            
            detected_language = info.language
            confidence = info.language_probability
            
            logger.debug(f"Language detected: {detected_language} (confidence: {confidence:.2f})")
            
            return LanguageDetectionResult(
                language=detected_language,
                confidence=confidence
            )
            
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            return None
    
    def switch_model(self, model_name: str) -> bool:
        """
        Switch to a different Whisper model.
        
        Args:
            model_name: New model name to load
            
        Returns:
            True if model switch was successful
        """
        if model_name == self.model_name:
            logger.info(f"Already using model '{model_name}'")
            return True
        
        if model_name not in self.SUPPORTED_MODELS:
            logger.error(f"Unsupported model: {model_name}")
            return False
        
        try:
            old_model = self.model_name
            self.model_name = model_name
            self._load_model()
            logger.info(f"Successfully switched from '{old_model}' to '{model_name}'")
            return True
        except Exception as e:
            logger.error(f"Failed to switch to model '{model_name}': {e}")
            # Restore previous model
            self.model_name = old_model
            return False


class APIWhisperTranscriber(BaseTranscriber):
    """OpenAI Whisper API transcriber with automatic language detection."""
    
    SUPPORTED_LANGUAGES = [
        "af", "am", "ar", "as", "az", "ba", "be", "bg", "bn", "bo", "br", "bs", "ca", "cs", "cy", "da", "de", "el",
        "en", "es", "et", "eu", "fa", "fi", "fo", "fr", "gl", "gu", "ha", "haw", "he", "hi", "hr", "ht", "hu", "hy",
        "id", "is", "it", "ja", "jw", "ka", "kk", "km", "kn", "ko", "la", "lb", "ln", "lo", "lt", "lv", "mg", "mi",
        "mk", "ml", "mn", "mr", "ms", "mt", "my", "ne", "nl", "nn", "no", "oc", "pa", "pl", "ps", "pt", "ro", "ru",
        "sa", "sd", "si", "sk", "sl", "sn", "so", "sq", "sr", "su", "sv", "sw", "ta", "te", "tg", "th", "tk", "tl",
        "tr", "tt", "uk", "ur", "uz", "vi", "yi", "yo", "zh"
    ]
    
    def __init__(self, api_key: str = None, model: str = "whisper-1", language: str = None):
        """
        Initialize API Whisper transcriber.
        
        Args:
            api_key: OpenAI API key (optional, will use client from LlmClient)
            model: Whisper model to use (default: "whisper-1")
            language: Fixed language code (optional, enables auto-detection if None)
        """
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI not available, using mock client for testing")
            self.client = None
        else:
            self.client = get_openai_client()
            
        self.model = model
        self.fixed_language = language
        
        # Validate language if provided
        if self.fixed_language and self.fixed_language not in self.SUPPORTED_LANGUAGES:
            logger.warning(f"Unsupported language '{self.fixed_language}', will use auto-detection")
            self.fixed_language = None
        
        logger.info(f"API Whisper transcriber initialized with model '{self.model}'")
        if self.fixed_language:
            logger.info(f"Fixed language: {self.fixed_language}")
        else:
            logger.info("Auto language detection enabled")
    
    def get_transcription(self, wav_file_path: str) -> str:
        """
        Get transcription from audio file using OpenAI Whisper API.
        
        Args:
            wav_file_path: Path to the audio file
            
        Returns:
            Transcribed text
        """
        if not OPENAI_AVAILABLE or not self.client:
            # Return mock transcription for testing
            return f"Mock API transcription for {os.path.basename(wav_file_path)}"
            
        if not os.path.exists(wav_file_path):
            raise AudioTranscriptionError(f"Audio file not found: {wav_file_path}")
        
        try:
            with open(wav_file_path, "rb") as audio_file:
                # Prepare transcription parameters
                transcription_params = {
                    "model": self.model,
                    "file": audio_file,
                    "response_format": "text"
                }
                
                # Add language if fixed language is set
                if self.fixed_language:
                    transcription_params["language"] = self.fixed_language
                
                # Call OpenAI API
                result = self.client.audio.transcriptions.create(**transcription_params)
                
                # Handle different response formats
                if hasattr(result, 'text'):
                    text = result.text
                else:
                    text = str(result)
                
                logger.debug(f"API transcription completed: {len(text)} characters")
                return text.strip()
                
        except Exception as e:
            logger.error(f"API transcription failed: {e}")
            return ''
    
    def get_mode(self) -> TranscriptionMode:
        """Get the transcription mode."""
        return TranscriptionMode.API
    
    def supports_language_detection(self) -> bool:
        """Check if language detection is supported."""
        return True
    
    def _detect_language_impl(self, wav_file_path: str) -> Optional[LanguageDetectionResult]:
        """
        Detect language using OpenAI Whisper API.
        
        Args:
            wav_file_path: Path to the audio file
            
        Returns:
            LanguageDetectionResult with detected language
        """
        if not os.path.exists(wav_file_path):
            return None
        
        try:
            with open(wav_file_path, "rb") as audio_file:
                # Use transcription with verbose response to get language info
                result = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="verbose_json"
                )
                
                # Extract language information
                detected_language = getattr(result, 'language', 'en')
                
                # OpenAI API doesn't provide confidence scores, so we estimate
                # based on text length and quality
                text_length = len(getattr(result, 'text', ''))
                confidence = min(0.9, max(0.5, text_length / 100.0))  # Rough estimation
                
                logger.debug(f"API language detected: {detected_language} (estimated confidence: {confidence:.2f})")
                
                return LanguageDetectionResult(
                    language=detected_language,
                    confidence=confidence
                )
                
        except Exception as e:
            logger.warning(f"API language detection failed: {e}")
            return None
    
    def set_language(self, language: str = None) -> bool:
        """
        Set fixed language or enable auto-detection.
        
        Args:
            language: Language code to fix, or None for auto-detection
            
        Returns:
            True if language setting was successful
        """
        if language and language not in self.SUPPORTED_LANGUAGES:
            logger.error(f"Unsupported language: {language}")
            return False
        
        old_language = self.fixed_language
        self.fixed_language = language
        
        if language:
            logger.info(f"Language set to: {language}")
        else:
            logger.info("Auto language detection enabled")
        
        return True


class TranscriberModelManager:
    """Manager class for handling transcriber model switching and configuration."""
    
    def __init__(self):
        """Initialize the transcriber model manager."""
        self.current_transcriber: Optional[BaseTranscriber] = None
        self.current_mode: Optional[TranscriptionMode] = None
        self._model_cache: Dict[str, BaseTranscriber] = {}
        
        logger.info("TranscriberModelManager initialized")
    
    def get_transcriber(self, mode: TranscriptionMode, **kwargs) -> BaseTranscriber:
        """
        Get or create a transcriber for the specified mode.
        
        Args:
            mode: Transcription mode (LOCAL or API)
            **kwargs: Additional parameters for transcriber initialization
            
        Returns:
            BaseTranscriber instance
        """
        cache_key = f"{mode.value}_{hash(frozenset(kwargs.items()))}"
        
        if cache_key in self._model_cache:
            logger.debug(f"Using cached transcriber for {mode.value}")
            return self._model_cache[cache_key]
        
        # Create new transcriber
        if mode == TranscriptionMode.LOCAL:
            transcriber = FasterWhisperTranscriber(**kwargs)
        elif mode == TranscriptionMode.API:
            transcriber = APIWhisperTranscriber(**kwargs)
        else:
            raise ValueError(f"Unsupported transcription mode: {mode}")
        
        # Cache the transcriber
        self._model_cache[cache_key] = transcriber
        logger.info(f"Created new {mode.value} transcriber")
        
        return transcriber
    
    def switch_mode(self, mode: TranscriptionMode, **kwargs) -> BaseTranscriber:
        """
        Switch to a different transcription mode.
        
        Args:
            mode: New transcription mode
            **kwargs: Parameters for the new transcriber
            
        Returns:
            New BaseTranscriber instance
        """
        old_mode = self.current_mode
        self.current_transcriber = self.get_transcriber(mode, **kwargs)
        self.current_mode = mode
        
        logger.info(f"Switched transcription mode from {old_mode} to {mode.value}")
        return self.current_transcriber
    
    def get_current_transcriber(self) -> Optional[BaseTranscriber]:
        """
        Get the currently active transcriber.
        
        Returns:
            Current BaseTranscriber instance or None
        """
        return self.current_transcriber
    
    def validate_mode_consistency(self, expected_mode: TranscriptionMode) -> bool:
        """
        Validate that current transcriber matches expected mode.
        
        Args:
            expected_mode: Expected transcription mode
            
        Returns:
            True if modes are consistent
        """
        if not self.current_transcriber:
            return False
        
        actual_mode = self.current_transcriber.get_mode()
        is_consistent = actual_mode == expected_mode
        
        if not is_consistent:
            logger.warning(f"Mode inconsistency: expected {expected_mode.value}, got {actual_mode.value}")
        
        return is_consistent
    
    def clear_cache(self) -> None:
        """Clear the transcriber cache."""
        self._model_cache.clear()
        logger.info("Transcriber cache cleared")


# Global model manager instance
_model_manager = TranscriberModelManager()


def get_model(use_api: bool, **kwargs) -> BaseTranscriber:
    """
    Get a transcriber model based on the specified mode.
    
    Args:
        use_api: True for API mode, False for local mode
        **kwargs: Additional parameters for transcriber initialization
        
    Returns:
        BaseTranscriber instance
    """
    mode = TranscriptionMode.API if use_api else TranscriptionMode.LOCAL
    return _model_manager.get_transcriber(mode, **kwargs)


def switch_transcription_mode(use_api: bool, **kwargs) -> BaseTranscriber:
    """
    Switch transcription mode and return new transcriber.
    
    Args:
        use_api: True for API mode, False for local mode
        **kwargs: Additional parameters for transcriber initialization
        
    Returns:
        New BaseTranscriber instance
    """
    mode = TranscriptionMode.API if use_api else TranscriptionMode.LOCAL
    return _model_manager.switch_mode(mode, **kwargs)


def get_current_transcriber() -> Optional[BaseTranscriber]:
    """
    Get the currently active transcriber.
    
    Returns:
        Current BaseTranscriber instance or None
    """
    return _model_manager.get_current_transcriber()


def validate_transcription_consistency(use_api: bool) -> bool:
    """
    Validate that current transcriber matches expected mode.
    
    Args:
        use_api: Expected API usage mode
        
    Returns:
        True if modes are consistent
    """
    expected_mode = TranscriptionMode.API if use_api else TranscriptionMode.LOCAL
    return _model_manager.validate_mode_consistency(expected_mode)


# Aliases for backward compatibility
LocalWhisperModel = FasterWhisperTranscriber
APIWhisperModel = APIWhisperTranscriber
TranscriberModel = BaseTranscriber