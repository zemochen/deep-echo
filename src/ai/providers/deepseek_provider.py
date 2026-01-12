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
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"DeepSeek API request attempt {attempt + 1}/{self.max_retries}")
                
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
                        raise AIProviderError("Invalid response format from DeepSeek API")
                
                elif response.status_code == 401:
                    raise AIProviderAuthenticationError("Invalid API key for DeepSeek")
                
                elif response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderRateLimitError("DeepSeek API rate limit exceeded")
                
                elif response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Server error {response.status_code}, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderConnectionError(f"DeepSeek API server error: {response.status_code}")
                
                else:
                    error_msg = f"DeepSeek API error: {response.status_code} - {response.text}"
                    raise AIProviderError(error_msg)
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Request timeout, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AIProviderTimeoutError("DeepSeek API request timed out")
                    
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Connection error, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AIProviderConnectionError("Failed to connect to DeepSeek API")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Unexpected error: {e}, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AIProviderError(f"DeepSeek API request failed: {str(e)}")
        
        raise AIProviderError("All retry attempts failed")
    
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