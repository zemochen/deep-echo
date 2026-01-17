"""
Volcano Engine (ByteDance) provider implementation.

This module implements the Volcano Engine AI provider for generating responses
using ByteDance's Volcano Engine API, migrating from the existing LlmClient implementation.
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


class VolcanoEngineProvider(AIProvider):
    """
    Volcano Engine (ByteDance) provider implementation.
    
    This class implements the AIProvider interface for ByteDance's Volcano Engine API,
    providing response generation capabilities with proper error handling
    and retry logic. Uses OpenAI-compatible API format.
    """
    
    DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
    DEFAULT_MODEL = "doubao-pro-4k"
    
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, 
                 base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the Volcano Engine provider.
        
        Args:
            api_key: Volcano Engine API key
            model: Model name (default: doubao-pro-4k)
            base_url: Optional base URL (default: https://ark.cn-beijing.volces.com/api/v3)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, model, base_url or self.DEFAULT_BASE_URL, timeout, max_retries)
        
        # Validate model is supported
        supported_models = [
            "doubao-pro-4k", "doubao-pro-32k", "doubao-pro-128k",
            "doubao-lite-4k", "doubao-lite-32k", "doubao-lite-128k",
            "deepseek-v3-241226"  # From existing implementation
        ]
        if model not in supported_models:
            logger.warning(f"Model {model} may not be supported. Supported models: {supported_models}")
        
        # Initialize OpenAI-compatible client for Volcano Engine
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=self.timeout
        )
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using Volcano Engine API.
        
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
        else:
            # Use system role for the prompt as in the original implementation
            messages.append({"role": "system", "content": prompt})
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Volcano Engine API request attempt {attempt + 1}/{self.max_retries}")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.0),  # Default to 0.0 as in original
                    max_tokens=kwargs.get("max_tokens", 1000),
                    top_p=kwargs.get("top_p", 1.0),
                    frequency_penalty=kwargs.get("frequency_penalty", 0.0),
                    presence_penalty=kwargs.get("presence_penalty", 0.0)
                )
                
                if response.choices and len(response.choices) > 0:
                    content = response.choices[0].message.content
                    logger.debug("Volcano Engine API request successful")
                    return content.strip() if content else ""
                else:
                    raise AIProviderError("Invalid response format from Volcano Engine API")
                    
            except Exception as e:
                error_str = str(e).lower()
                
                # Handle authentication errors
                if "unauthorized" in error_str or "invalid api key" in error_str:
                    raise AIProviderAuthenticationError("Invalid API key for Volcano Engine")
                
                # Handle rate limit errors
                elif "rate limit" in error_str or "quota" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderRateLimitError("Volcano Engine API rate limit exceeded")
                
                # Handle timeout errors
                elif "timeout" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Request timeout, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderTimeoutError("Volcano Engine API request timed out")
                
                # Handle connection errors
                elif "connection" in error_str or "network" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Connection error, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderConnectionError("Failed to connect to Volcano Engine API")
                
                # Handle server errors (5xx)
                elif "server error" in error_str or "internal error" in error_str:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Server error, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderConnectionError(f"Volcano Engine API server error: {str(e)}")
                
                # Handle other errors
                else:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Unexpected error: {e}, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderError(f"Volcano Engine API request failed: {str(e)}")
        
        raise AIProviderError("All retry attempts failed")
    
    def get_provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            "volcano"
        """
        return "volcano"
    
    def validate_config(self) -> bool:
        """
        Validate the Volcano Engine provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not super().validate_config():
            return False
        
        # Additional Volcano Engine-specific validation
        try:
            if not self.base_url.startswith(("http://", "https://")):
                logger.error("Invalid base URL format")
                return False
            
            # Validate API key format (Volcano Engine keys are typically UUIDs)
            if len(self.api_key) < 20:
                logger.warning("API key format may be invalid for Volcano Engine")
            
            return True
        except Exception as e:
            logger.error(f"Volcano Engine configuration validation failed: {e}")
            return False