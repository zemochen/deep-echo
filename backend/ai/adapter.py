"""
AI Adapter for managing multiple AI providers.

This module provides a unified interface for managing and switching between
different AI providers, enabling seamless provider switching and configuration.
"""

import logging
from typing import Optional, Dict, Any, Type
from datetime import datetime

from .providers.base_provider import AIProvider, AIProviderError
from .providers.deepseek_provider import DeepSeekProvider
from .providers.openai_provider import OpenAIProvider
from .providers.grok_provider import GrokProvider
from .providers.claude_provider import ClaudeProvider
from .providers.volcano_provider import VolcanoEngineProvider
from .providers.glm_provider import GLMProvider
from backend.ipc.event_emitter import get_event_emitter

logger = logging.getLogger(__name__)


class AIAdapter:
    """
    AI Adapter for managing multiple AI providers.
    
    This class provides a unified interface for managing different AI providers,
    allowing seamless switching between providers and maintaining consistent
    behavior across different AI services.
    """
    
    # Registry of available providers
    PROVIDER_REGISTRY: Dict[str, Type[AIProvider]] = {
        "deepseek": DeepSeekProvider,
        "openai": OpenAIProvider,
        "grok": GrokProvider,
        "claude": ClaudeProvider,
        "volcano": VolcanoEngineProvider,
        "glm": GLMProvider
    }
    
    # Default configurations for each provider
    DEFAULT_CONFIGS = {
        "deepseek": {
            "models": ["deepseek-chat", "deepseek-coder"],
            "default_model": "deepseek-chat"
        },
        "openai": {
            "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o", "gpt-4o-mini"],
            "default_model": "gpt-3.5-turbo"
        },
        "grok": {
            "models": ["grok-beta", "grok-2"],
            "default_model": "grok-beta"
        },
        "claude": {
            "models": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229", "claude-3-opus-20240229"],
            "default_model": "claude-3-sonnet-20240229"
        },
        "volcano": {
            "models": ["doubao-pro-4k", "doubao-lite-4k", "deepseek-v3-241226"],
            "default_model": "doubao-pro-4k"
        },
        "glm": {
            "models": ["glm-4", "glm-4-plus", "glm-4-flash"],
            "default_model": "glm-4"
        }
    }
    
    def __init__(self, provider: Optional[AIProvider] = None):
        """
        Initialize the AI adapter.
        
        Args:
            provider: Optional initial AI provider instance
        """
        self._current_provider: Optional[AIProvider] = provider
        self._provider_history: list = []
        
        if provider:
            self._provider_history.append(provider.get_provider_name())
            logger.info(f"AI Adapter initialized with {provider.get_provider_name()} provider")
        else:
            logger.info("AI Adapter initialized without provider")
    
    def set_provider(self, provider: AIProvider) -> None:
        """
        Set the current AI provider.
        
        Args:
            provider: AI provider instance to set as current
            
        Raises:
            ValueError: If provider is None or invalid
        """
        if not provider:
            raise ValueError("Provider cannot be None")
        
        if not isinstance(provider, AIProvider):
            raise ValueError("Provider must be an instance of AIProvider")
        
        # Validate provider configuration
        if not provider.validate_config():
            raise ValueError(f"Invalid configuration for provider: {provider.get_provider_name()}")
        
        old_provider = self._current_provider.get_provider_name() if self._current_provider else "None"
        self._current_provider = provider
        self._provider_history.append(provider.get_provider_name())
        
        logger.info(f"AI provider switched from {old_provider} to {provider.get_provider_name()}")
    
    def create_provider(self, provider_type: str, api_key: str, model: Optional[str] = None, 
                       **kwargs) -> AIProvider:
        """
        Create a new provider instance.
        
        Args:
            provider_type: Type of provider ("deepseek", "openai", etc.)
            api_key: API key for the provider
            model: Optional model name (uses default if not specified)
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Configured AI provider instance
            
        Raises:
            ValueError: If provider type is not supported
        """
        provider_type = provider_type.lower()
        
        if provider_type not in self.PROVIDER_REGISTRY:
            available_providers = ", ".join(self.PROVIDER_REGISTRY.keys())
            raise ValueError(f"Unsupported provider type: {provider_type}. "
                           f"Available providers: {available_providers}")
        
        # Use default model if not specified
        if not model:
            model = self.DEFAULT_CONFIGS[provider_type]["default_model"]
        
        provider_class = self.PROVIDER_REGISTRY[provider_type]
        
        try:
            provider = provider_class(
                api_key=api_key,
                model=model,
                **kwargs
            )
            logger.info(f"Created {provider_type} provider with model {model}")
            return provider
        except Exception as e:
            logger.error(f"Failed to create {provider_type} provider: {e}")
            raise ValueError(f"Failed to create {provider_type} provider: {e}")
    
    def switch_provider(self, provider_type: str, api_key: str, model: Optional[str] = None, 
                       **kwargs) -> None:
        """
        Switch to a new provider by creating and setting it.
        
        Args:
            provider_type: Type of provider to switch to
            api_key: API key for the new provider
            model: Optional model name
            **kwargs: Additional provider-specific parameters
        """
        new_provider = self.create_provider(provider_type, api_key, model, **kwargs)
        self.set_provider(new_provider)
    
    def generate_response(self, prompt: str, **kwargs) -> str:
        """
        Generate a response using the current AI provider.
        
        Args:
            prompt: The input prompt to generate a response for
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated response text
            
        Raises:
            RuntimeError: If no provider is set
            AIProviderError: If the provider fails to generate a response
        """
        if not self._current_provider:
            raise RuntimeError("No AI provider is currently set")
        
        try:
            response = self._current_provider.generate_response(prompt, **kwargs)
            logger.debug(f"Generated response using {self._current_provider.get_provider_name()}")
            
            # Emit response-generated event
            try:
                event_emitter = get_event_emitter()
                event_emitter.emit_response_generated({
                    "id": f"response_{datetime.utcnow().timestamp()}",
                    "timestamp": datetime.utcnow().isoformat(),
                    "provider": self._current_provider.get_provider_name(),
                    "model": self._current_provider.get_model_name(),
                    "text": response,
                    "context": prompt[:200]  # Include first 200 chars of context
                })
            except Exception as e:
                logger.warning(f"Failed to emit response-generated event: {e}")
            
            return response
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            
            # Emit error event
            try:
                event_emitter = get_event_emitter()
                event_emitter.emit_error_occurred({
                    "error": str(e),
                    "component": "ai_adapter",
                    "timestamp": datetime.utcnow().isoformat()
                })
            except Exception as emit_error:
                logger.warning(f"Failed to emit error event: {emit_error}")
            
            raise
    
    def get_current_provider(self) -> Optional[str]:
        """
        Get the name of the current AI provider.
        
        Returns:
            Current provider name or None if no provider is set
        """
        return self._current_provider.get_provider_name() if self._current_provider else None
    
    def get_current_model(self) -> Optional[str]:
        """
        Get the current model name.
        
        Returns:
            Current model name or None if no provider is set
        """
        return self._current_provider.get_model_name() if self._current_provider else None
    
    def get_provider_config(self) -> Optional[Dict[str, Any]]:
        """
        Get the current provider configuration.
        
        Returns:
            Provider configuration dictionary or None if no provider is set
        """
        return self._current_provider.get_config() if self._current_provider else None
    
    def get_available_providers(self) -> list:
        """
        Get list of available provider types.
        
        Returns:
            List of available provider type names
        """
        return list(self.PROVIDER_REGISTRY.keys())
    
    def get_provider_models(self, provider_type: str) -> list:
        """
        Get available models for a specific provider type.
        
        Args:
            provider_type: Provider type name
            
        Returns:
            List of available model names
            
        Raises:
            ValueError: If provider type is not supported
        """
        provider_type = provider_type.lower()
        if provider_type not in self.DEFAULT_CONFIGS:
            raise ValueError(f"Unsupported provider type: {provider_type}")
        
        return self.DEFAULT_CONFIGS[provider_type]["models"]
    
    def get_provider_history(self) -> list:
        """
        Get the history of providers used in this session.
        
        Returns:
            List of provider names in chronological order
        """
        return self._provider_history.copy()
    
    def validate_current_provider(self) -> bool:
        """
        Validate the current provider configuration.
        
        Returns:
            True if current provider is valid, False otherwise
        """
        if not self._current_provider:
            return False
        
        return self._current_provider.validate_config()
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the AI adapter.
        
        Returns:
            Dictionary containing adapter status information
        """
        return {
            "current_provider": self.get_current_provider(),
            "current_model": self.get_current_model(),
            "available_providers": self.get_available_providers(),
            "provider_history": self.get_provider_history(),
            "is_valid": self.validate_current_provider()
        }
    
    def cleanup(self) -> None:
        """
        Clean up AI adapter resources.
        
        This method performs cleanup operations for the AI adapter,
        such as clearing provider history and resetting state.
        """
        try:
            # Clear provider history
            self._provider_history.clear()
            
            # Log cleanup
            if self._current_provider:
                logger.info(f"Cleaning up AI adapter with provider: {self.get_current_provider()}")
            else:
                logger.info("Cleaning up AI adapter (no active provider)")
            
            # Note: We don't set _current_provider to None to allow graceful shutdown
            # The provider itself doesn't need cleanup as it's stateless
            
        except Exception as e:
            logger.error(f"Error during AI adapter cleanup: {e}")
