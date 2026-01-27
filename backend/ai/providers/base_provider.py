"""
Abstract base class for AI providers.

This module defines the common interface that all AI providers must implement
to ensure consistent behavior across different AI services.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """
    Abstract base class for AI providers.
    
    This class defines the common interface that all AI providers must implement
    to ensure consistent behavior and easy provider switching.
    """
    
    def __init__(self, api_key: str, model: str, base_url: Optional[str] = None, 
                 timeout: int = 30, max_retries: int = 3):
        """
        Initialize the AI provider.
        
        Args:
            api_key: API key for the AI service
            model: Model name to use for generation
            base_url: Optional base URL for the API (if different from default)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.timeout = timeout
        self.max_retries = max_retries
        
        # Validate required parameters
        if not api_key:
            raise ValueError("API key is required")
        if not model:
            raise ValueError("Model name is required")
    
    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response from the AI provider.
        
        Args:
            prompt: The input prompt to generate a response for
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated response text
            
        Raises:
            Exception: If the API call fails after all retries
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the name of the AI provider.
        
        Returns:
            Provider name as string
        """
        pass
    
    def get_model_name(self) -> str:
        """
        Get the current model name.
        
        Returns:
            Model name as string
        """
        return self.model
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current provider configuration.
        
        Returns:
            Dictionary containing provider configuration
        """
        return {
            "provider": self.get_provider_name(),
            "model": self.model,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "max_retries": self.max_retries
        }
    
    def validate_config(self) -> bool:
        """
        Validate the provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            if not self.api_key or not self.model:
                return False
            return True
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False


class AIProviderError(Exception):
    """Base exception for AI provider errors."""
    pass


class AIProviderConnectionError(AIProviderError):
    """Exception raised when connection to AI provider fails."""
    pass


class AIProviderAuthenticationError(AIProviderError):
    """Exception raised when authentication with AI provider fails."""
    pass


class AIProviderRateLimitError(AIProviderError):
    """Exception raised when AI provider rate limit is exceeded."""
    pass


class AIProviderTimeoutError(AIProviderError):
    """Exception raised when AI provider request times out."""
    pass