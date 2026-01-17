"""
Claude (Anthropic) provider implementation.

This module implements the Claude AI provider for generating responses
using Anthropic's Claude API.
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


class ClaudeProvider(AIProvider):
    """
    Claude (Anthropic) provider implementation.
    
    This class implements the AIProvider interface for Anthropic's Claude API,
    providing response generation capabilities with proper error handling
    and retry logic.
    """
    
    DEFAULT_BASE_URL = "https://api.anthropic.com"
    DEFAULT_MODEL = "claude-3-sonnet-20240229"
    
    def __init__(self, api_key: str, model: str = DEFAULT_MODEL, 
                 base_url: Optional[str] = None, timeout: int = 30, max_retries: int = 3):
        """
        Initialize the Claude provider.
        
        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-3-sonnet-20240229)
            base_url: Optional base URL (default: https://api.anthropic.com)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        super().__init__(api_key, model, base_url or self.DEFAULT_BASE_URL, timeout, max_retries)
        
        # Validate model is supported
        supported_models = [
            "claude-3-haiku-20240307", 
            "claude-3-sonnet-20240229", 
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022"
        ]
        if model not in supported_models:
            logger.warning(f"Model {model} may not be supported. Supported models: {supported_models}")
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using Claude API.
        
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
        
        # Prepare request data - Claude uses a different format
        data = {
            "model": self.model,
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.7),
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        
        # Add system message if provided
        if kwargs.get("system_message"):
            data["system"] = kwargs["system_message"]
        
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        url = f"{self.base_url}/v1/messages"
        
        # Retry logic with exponential backoff
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Claude API request attempt {attempt + 1}/{self.max_retries}")
                
                response = requests.post(
                    url,
                    json=data,
                    headers=headers,
                    timeout=self.timeout
                )
                
                # Handle different HTTP status codes
                if response.status_code == 200:
                    result = response.json()
                    if "content" in result and len(result["content"]) > 0:
                        # Claude returns content as a list of content blocks
                        content = result["content"][0]["text"]
                        logger.debug("Claude API request successful")
                        return content.strip() if content else ""
                    else:
                        raise AIProviderError("Invalid response format from Claude API")
                
                elif response.status_code == 401:
                    raise AIProviderAuthenticationError("Invalid API key for Claude")
                
                elif response.status_code == 429:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderRateLimitError("Claude API rate limit exceeded")
                
                elif response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        wait_time = (2 ** attempt) * 1
                        logger.warning(f"Server error {response.status_code}, waiting {wait_time}s before retry")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise AIProviderConnectionError(f"Claude API server error: {response.status_code}")
                
                else:
                    error_msg = f"Claude API error: {response.status_code} - {response.text}"
                    raise AIProviderError(error_msg)
                    
            except requests.exceptions.Timeout:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Request timeout, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AIProviderTimeoutError("Claude API request timed out")
                    
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Connection error, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AIProviderConnectionError("Failed to connect to Claude API")
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    wait_time = (2 ** attempt) * 1
                    logger.warning(f"Unexpected error: {e}, waiting {wait_time}s before retry")
                    time.sleep(wait_time)
                    continue
                else:
                    raise AIProviderError(f"Claude API request failed: {str(e)}")
        
        raise AIProviderError("All retry attempts failed")
    
    def get_provider_name(self) -> str:
        """
        Get the provider name.
        
        Returns:
            "claude"
        """
        return "claude"
    
    def validate_config(self) -> bool:
        """
        Validate the Claude provider configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        if not super().validate_config():
            return False
        
        # Additional Claude-specific validation
        try:
            if not self.base_url.startswith(("http://", "https://")):
                logger.error("Invalid base URL format")
                return False
            return True
        except Exception as e:
            logger.error(f"Claude configuration validation failed: {e}")
            return False