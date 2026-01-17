"""
OpenAI provider implementation.

This module implements the OpenAI provider for generating responses
using OpenAI's API, migrating from the existing LlmClient implementation.
"""

import time
import logging
from typing import Optional, Dict, Any

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("OpenAI library is required. Install with: pip install openai")

from .base_provider import (
    AIProvider, 
    AIProviderError, 
    AIProviderConnectionError,
    AIProviderAuthenticationError,
    AIProviderRateLimitError,
    AIProviderTimeoutError
)

logger = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """
    OpenAI provider implementation.
    
    This class implements the AIProvider interface for OpenAI's API,
    providing response generation capabilities with proper error handling
    and retry logic.
    """
    
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-3.5-turbo"
    
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, 
                 base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-3.5-turbo)
            base_url: Optional base URL (default: https://api.openai.com/v1)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, model, base_url or self.DEFAULT_BASE_URL, timeout, max_retries)
        
        # Validate model is supported
        supported_models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"]
        if model not in supported_models:
            logger.warning(f"Model {model} may not be supported. Supported models: {supported_models}")
        
        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using OpenAI API.
        
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
        
        # Prepare messages - support both system and user content
        messages = []
        if kwargs.get("system_message"):
            messages.append({"role": "system", "content": kwargs["system_message"]})
        messages.append({"role": "user", "content": prompt})
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"OpenAI API request attempt {attempt + 1}/{self.max_retries}")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens", 1000),
                    top_p=kwargs.get("top_p", 1.0),
                    frequency_penalty=kwargs.get("frequency_penalty", 0.0),
                    presence_penalty=kwargs.get("presence_penalty", 0.0)
                )
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    logger.debug("OpenAI API request successful")
                    return content.strip() if content else ""
                else:
                    raise AIProviderError("Invalid response format from OpenAI API")
                    
            except Exception as e:
                error_str = str(e).lower()
                
                # Handle authentication errors
                if "unauthorized" in error_str or "invalid api key" in error_str:
                    raise AIProviderAuthenticationError("Invalid API key for OpenAI")
                
                # Handle rate limit errors
                elif "rate limit" in error_str or "quota" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderRateLimitError("OpenAI API rate limit exceeded")
                
                # Handle timeout errors
                elif "timeout" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Request timeout, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderTimeoutError("OpenAI API request timed out")
                
                # Handle connection errors
                elif "connection" in error_str or "network" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Connection error, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderConnectionError("Failed to connect to OpenAI API")
                
                # Handle server errors (5xx)
                elif "server error" in error_str or "internal error" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Server error, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderConnectionError(f"OpenAI API server error: {str(e)}")
                
                # Handle other errors
                else:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Unexpected error: {e}, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderError(f"OpenAI API request failed: {str(e)}")
        
        raise AIProviderError("All retry attempts failed")
    
    def get_provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            "openai"
        """
        return "openai"
    
    def validate_config(self) -> bool:
        """
        Validate the OpenAI provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not super().validate_config():
            return False
        
        # Additional OpenAI-specific validation
        try:
            if not self.base_url.startswith(("http://", "https://")):
                logger.error("Invalid base URL format")
                return False
            
            # Validate API key format (OpenAI keys typically start with 'sk-')
            if not self.api_key.startswith('sk-') and len(self.api_key) < 20:
                logger.warning("API key format may be invalid for OpenAI")
            
            return True
        except Exception as e:
            logger.error(f"OpenAI configuration validation failed: {e}")
            return False