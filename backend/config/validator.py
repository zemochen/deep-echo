"""
Configuration Validator for DeepEcho Real-time Voice AI Assistant.

This module provides validation functionality for AI provider configurations,
API keys, and system settings.
"""

import re
from typing import Dict, List, Tuple, Optional
from backend.utils.logger import get_logger

logger = get_logger(__name__)


class ConfigValidator:
    """
    Configuration validator for AI providers and system settings.
    
    This class provides validation methods for API keys, provider configurations,
    and system settings with detailed feedback messages.
    """
    
    def __init__(self):
        """Initialize the configuration validator."""
        self.provider_patterns = {
            "openai": r"^sk-[a-zA-Z0-9]{48}$",
            "deepseek": r"^sk-[a-zA-Z0-9]{48}$",
            "grok": r"^xai-[a-zA-Z0-9]{48}$",
            "claude": r"^sk-ant-[a-zA-Z0-9]{48}$",
            "volcano": r"^[a-zA-Z0-9]{32}$",
            "glm": r"^[a-zA-Z0-9]{32}\.[a-zA-Z0-9]{32}$"
        }
        
        self.provider_models = {
            "deepseek": ["deepseek-chat", "deepseek-coder"],
            "openai": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
            "grok": ["grok-beta", "grok-2"],
            "claude": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
            "volcano": ["doubao-pro", "doubao-lite"],
            "glm": ["glm-4", "glm-3-turbo"]
        }
    
    def validate_api_key(self, provider: str, api_key: str) -> Tuple[bool, str]:
        """
        Validate an API key for a specific provider.
        
        Args:
            provider: AI provider name
            api_key: API key to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not provider or not api_key:
            return False, "Provider and API key are required"
        
        provider = provider.lower()
        
        if provider not in self.provider_patterns:
            return False, f"Unknown provider: {provider}"
        
        pattern = self.provider_patterns[provider]
        
        if not re.match(pattern, api_key):
            return False, f"Invalid API key format for {provider}"
        
        return True, f"API key format is valid for {provider}"
    
    def validate_model(self, provider: str, model: str) -> Tuple[bool, str]:
        """
        Validate a model for a specific provider.
        
        Args:
            provider: AI provider name
            model: Model name to validate
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not provider or not model:
            return False, "Provider and model are required"
        
        provider = provider.lower()
        
        if provider not in self.provider_models:
            return False, f"Unknown provider: {provider}"
        
        available_models = self.provider_models[provider]
        
        if model not in available_models:
            return False, f"Model '{model}' not available for {provider}. Available: {', '.join(available_models)}"
        
        return True, f"Model '{model}' is valid for {provider}"
    
    def validate_provider_config(self, provider: str, api_key: str, model: str) -> Tuple[bool, List[str]]:
        """
        Validate a complete provider configuration.
        
        Args:
            provider: AI provider name
            api_key: API key
            model: Model name
            
        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        messages = []
        is_valid = True
        
        # Validate API key
        key_valid, key_msg = self.validate_api_key(provider, api_key)
        messages.append(key_msg)
        if not key_valid:
            is_valid = False
        
        # Validate model
        model_valid, model_msg = self.validate_model(provider, model)
        messages.append(model_msg)
        if not model_valid:
            is_valid = False
        
        return is_valid, messages
    
    def get_available_models(self, provider: str) -> List[str]:
        """
        Get available models for a provider.
        
        Args:
            provider: AI provider name
            
        Returns:
            List of available model names
        """
        provider = provider.lower()
        return self.provider_models.get(provider, [])
    
    def get_supported_providers(self) -> List[str]:
        """
        Get list of supported providers.
        
        Returns:
            List of supported provider names
        """
        return list(self.provider_models.keys())
    
    def validate_update_interval(self, interval: int) -> Tuple[bool, str]:
        """
        Validate update interval setting.
        
        Args:
            interval: Update interval in seconds
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not isinstance(interval, int):
            return False, "Update interval must be an integer"
        
        if interval < 1:
            return False, "Update interval must be at least 1 second"
        
        if interval > 60:
            return False, "Update interval should not exceed 60 seconds"
        
        return True, f"Update interval {interval} seconds is valid"
    
    def validate_system_config(self, config: Dict) -> Tuple[bool, List[str]]:
        """
        Validate complete system configuration.
        
        Args:
            config: System configuration dictionary
            
        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        messages = []
        is_valid = True
        
        # Validate required fields
        required_fields = ["ai_provider", "api_key", "model"]
        for field in required_fields:
            if field not in config:
                messages.append(f"Missing required field: {field}")
                is_valid = False
        
        if not is_valid:
            return is_valid, messages
        
        # Validate provider configuration
        provider_valid, provider_messages = self.validate_provider_config(
            config["ai_provider"], 
            config["api_key"], 
            config["model"]
        )
        messages.extend(provider_messages)
        if not provider_valid:
            is_valid = False
        
        # Validate optional fields
        if "update_interval" in config:
            interval_valid, interval_msg = self.validate_update_interval(config["update_interval"])
            messages.append(interval_msg)
            if not interval_valid:
                is_valid = False
        
        return is_valid, messages
    
    def suggest_fixes(self, provider: str, api_key: str) -> List[str]:
        """
        Suggest fixes for invalid configurations.
        
        Args:
            provider: AI provider name
            api_key: API key that failed validation
            
        Returns:
            List of suggested fixes
        """
        suggestions = []
        
        if not provider:
            suggestions.append("Select a valid AI provider from the dropdown")
            return suggestions
        
        if not api_key:
            suggestions.append(f"Enter a valid API key for {provider}")
            return suggestions
        
        provider = provider.lower()
        
        if provider == "openai":
            suggestions.extend([
                "OpenAI API keys should start with 'sk-'",
                "Check your OpenAI account dashboard for the correct API key",
                "Ensure the API key is exactly 51 characters long"
            ])
        elif provider == "deepseek":
            suggestions.extend([
                "DeepSeek API keys should start with 'sk-'",
                "Check your DeepSeek account for the correct API key format"
            ])
        elif provider == "grok":
            suggestions.extend([
                "Grok API keys should start with 'xai-'",
                "Check your X.AI account for the correct API key"
            ])
        elif provider == "claude":
            suggestions.extend([
                "Claude API keys should start with 'sk-ant-'",
                "Check your Anthropic account for the correct API key"
            ])
        elif provider == "volcano":
            suggestions.extend([
                "Volcano Engine API keys are typically 32 characters long",
                "Check your ByteDance Volcano Engine console"
            ])
        elif provider == "glm":
            suggestions.extend([
                "GLM API keys should contain a dot separator",
                "Check your Zhipu AI account for the correct format"
            ])
        
        return suggestions


# Global validator instance
_validator = ConfigValidator()


def validate_api_key(provider: str, api_key: str) -> Tuple[bool, str]:
    """Validate API key (convenience function)."""
    return _validator.validate_api_key(provider, api_key)


def validate_model(provider: str, model: str) -> Tuple[bool, str]:
    """Validate model (convenience function)."""
    return _validator.validate_model(provider, model)


def validate_provider_config(provider: str, api_key: str, model: str) -> Tuple[bool, List[str]]:
    """Validate provider configuration (convenience function)."""
    return _validator.validate_provider_config(provider, api_key, model)


def get_available_models(provider: str) -> List[str]:
    """Get available models (convenience function)."""
    return _validator.get_available_models(provider)


def get_supported_providers() -> List[str]:
    """Get supported providers (convenience function)."""
    return _validator.get_supported_providers()


def suggest_fixes(provider: str, api_key: str) -> List[str]:
    """Suggest fixes (convenience function)."""
    return _validator.suggest_fixes(provider, api_key)