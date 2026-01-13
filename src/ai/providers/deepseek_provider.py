"""
DeepSeek AI provider implementation.

This module implements the DeepSeek AI provider for generating responses
using DeepSeek's API.
"""

import requests
import time
import logging
from typing import Optional, Dict, Any

from .base_provider import (
    AIProvider, 
    AIProviderError, 
    AIProviderConnectionError,
    AIProviderAuthenticationError,
    AIProviderRateLimitError,
    AIProviderTimeoutError
)
from src.utils.retry import retry_with_backoff, RetryConfig, circuit_breaker
from src.utils.error_recovery import error_tracker

logger = logging.getLogger(__name__)


class DeepSeekProvider(AIProvider):
    """
    DeepSeek AI provider implementation.
    
    This class implements the AIProvider interface for DeepSeek's API,
    providing response generation capabilities with proper error handling
    and retry logic.
    """
    
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, 
                 base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the DeepSeek provider.
        
        Args:
            api_key: DeepSeek API key
            model: Model name (default: deepseek-chat)
            base_url: Optional base URL (default: https://api.deepseek.com/v1)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, model, base_url or self.DEFAULT_BASE_URL, timeout, max_retries)
        
        # Validate model is supported
        supported_models = ["deepseek-chat", "deepseek-coder"]
        if model not in supported_models:
            logger.warning(f"Model {model} may not be supported. Supported models: {supported_models}")
    
    @retry_with_backoff(
        exceptions=(
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            AIProviderConnectionError,
            AIProviderTimeoutError
        ),
        config=RetryConfig(max_attempts=3, base_delay=1.0, backoff_factor=2.0)
    )
    @circuit_breaker(
        failure_threshold=5,
        recovery_timeout=60.0,
        expected_exception=AIProviderError
    )
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using DeepSeek API.
        
        Args:
            prompt: The input prompt to generate a response for
            **kwargs: Additional parameters like temperature, max_tokens, etc.
            
        Returns:
            Generated response text
            
        Raises:
            AIProviderError: If the API call fails after all retries
        """
        if not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Record attempt for error tracking
        component = f"deepseek_provider_{self.model}"
        
        # Prepare request data
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 1000),
            "stream": False
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}/chat/completions"
        
        try:
            logger.debug(f"DeepSeek API request to {url}")
            
            response = requests.post(
                url,
                json=data,
                headers=headers,
                timeout=self.timeout
            )
            
            # Handle different HTTP status codes
            if response.status_code == 200:
                result = response.json()
                if "choices" in result and len(result["choices"]) > 0:
                    content = result["choices"][0]["message"]["content"]
                    logger.debug("DeepSeek API request successful")
                    return content.strip()
                else:
                    error = AIProviderError("Invalid response format from DeepSeek API")
                    error_tracker.record_error(error, component)
                    raise error
            
            elif response.status_code == 401:
                error = AIProviderAuthenticationError("Invalid API key for DeepSeek")
                error_tracker.record_error(error, component, "critical")
                raise error
            
            elif response.status_code == 429:
                error = AIProviderRateLimitError("DeepSeek API rate limit exceeded")
                error_tracker.record_error(error, component, "warning")
                raise error
            
            elif response.status_code >= 500:
                error = AIProviderConnectionError(f"DeepSeek API server error: {response.status_code}")
                error_tracker.record_error(error, component)
                raise error
            
            else:
                error_msg = f"DeepSeek API error: {response.status_code} - {response.text}"
                error = AIProviderError(error_msg)
                error_tracker.record_error(error, component)
                raise error
                
        except requests.exceptions.Timeout as e:
            error = AIProviderTimeoutError("DeepSeek API request timed out")
            error_tracker.record_error(error, component)
            raise error
            
        except requests.exceptions.ConnectionError as e:
            error = AIProviderConnectionError("Failed to connect to DeepSeek API")
            error_tracker.record_error(error, component)
            raise error
            
        except Exception as e:
            if not isinstance(e, AIProviderError):
                error = AIProviderError(f"DeepSeek API request failed: {str(e)}")
                error_tracker.record_error(error, component)
                raise error
            else:
                raise e
    
    def get_provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            "deepseek"
        """
        return "deepseek"
    
    def validate_config(self) -> bool:
        """
        Validate the DeepSeek provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not super().validate_config():
            return False
        
        # Additional DeepSeek-specific validation
        try:
            if not self.base_url.startswith(("http://", "https://")):
                logger.error("Invalid base URL format")
                return False
            return True
        except Exception as e:
            logger.error(f"DeepSeek configuration validation failed: {e}")
            return False