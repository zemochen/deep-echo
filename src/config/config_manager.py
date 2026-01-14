"""
Configuration Manager for DeepEcho Real-time Voice AI Assistant.

This module provides comprehensive configuration management including:
- AI provider configurations
- System settings
- Configuration file handling
- Validation and error handling
"""

import json
import os
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path

from src.config.validator import ConfigValidator
from src.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AIProviderConfig:
    """Configuration for an AI provider."""
    provider_type: str
    api_key: str
    model: str
    base_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3


@dataclass
class AudioConfig:
    """Configuration for audio processing."""
    record_timeout: int = 3
    phrase_timeout: float = 3.05
    max_phrases: int = 10
    energy_threshold: int = 1000
    use_api_mode: bool = False
    whisper_model: str = "small"
    whisper_model_path: Optional[str] = None


@dataclass
class UIConfig:
    """Configuration for user interface."""
    update_interval: int = 5
    processing_interval: float = 0.1
    ui_update_interval: float = 0.3
    use_new_ui: bool = True


@dataclass
class SystemConfig:
    """Complete system configuration."""
    ai_provider: AIProviderConfig
    audio: AudioConfig
    ui: UIConfig
    default_provider: str = "deepseek"


class ConfigManager:
    """
    Configuration manager for the DeepEcho system.
    
    Handles loading, saving, validation, and management of all system configurations
    including AI providers, audio settings, and UI preferences.
    """
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory to store configuration files. 
                       Defaults to ~/.deepecho/
        """
        self.config_dir = Path(config_dir) if config_dir else Path.home() / ".deepecho"
        self.config_file = self.config_dir / "config.json"
        self.validator = ConfigValidator()
        self._current_config: Optional[SystemConfig] = None
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Default configurations for each provider
        self.default_provider_configs = {
            "deepseek": {
                "model": "deepseek-chat",
                "base_url": "https://api.deepseek.com/v1"
            },
            "openai": {
                "model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1"
            },
            "grok": {
                "model": "grok-beta",
                "base_url": "https://api.x.ai/v1"
            },
            "claude": {
                "model": "claude-3-sonnet",
                "base_url": "https://api.anthropic.com/v1"
            },
            "volcano": {
                "model": "doubao-pro",
                "base_url": None
            },
            "glm": {
                "model": "glm-4",
                "base_url": "https://open.bigmodel.cn/api/paas/v4"
            }
        }
    
    def load_config(self) -> SystemConfig:
        """
        Load configuration from file or create default configuration.
        
        Returns:
            SystemConfig: Loaded or default system configuration
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            if self.config_file.exists():
                logger.info(f"Loading configuration from {self.config_file}")
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                # Convert dict to SystemConfig
                config = self._dict_to_config(config_data)
                
                # Validate configuration
                is_valid, messages = self._validate_config(config)
                if not is_valid:
                    logger.warning(f"Configuration validation failed: {messages}")
                    # Try to fix common issues or use defaults
                    config = self._fix_config_issues(config, messages)
                
                self._current_config = config
                logger.info("Configuration loaded successfully")
                return config
            else:
                logger.info("No configuration file found, creating default configuration")
                return self._create_default_config()
                
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            logger.info("Using default configuration")
            return self._create_default_config()
    
    def save_config(self, config: SystemConfig) -> bool:
        """
        Save configuration to file.
        
        Args:
            config: System configuration to save
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            # Validate before saving
            is_valid, messages = self._validate_config(config)
            if not is_valid:
                logger.error(f"Cannot save invalid configuration: {messages}")
                return False
            
            # Convert to dict and save
            config_dict = self._config_to_dict(config)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            self._current_config = config
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get_current_config(self) -> SystemConfig:
        """
        Get current configuration, loading if necessary.
        
        Returns:
            SystemConfig: Current system configuration
        """
        if self._current_config is None:
            self._current_config = self.load_config()
        return self._current_config
    
    def update_ai_provider(self, provider_type: str, api_key: str, 
                          model: Optional[str] = None) -> Tuple[bool, List[str]]:
        """
        Update AI provider configuration.
        
        Args:
            provider_type: Type of AI provider
            api_key: API key for the provider
            model: Model name (optional, uses default if not provided)
            
        Returns:
            Tuple of (success, messages)
        """
        try:
            # Validate provider and key
            is_valid, messages = self.validator.validate_provider_config(
                provider_type, api_key, model or self.default_provider_configs[provider_type]["model"]
            )
            
            if not is_valid:
                return False, messages
            
            # Get current config
            config = self.get_current_config()
            
            # Update AI provider config
            default_config = self.default_provider_configs.get(provider_type, {})
            config.ai_provider = AIProviderConfig(
                provider_type=provider_type,
                api_key=api_key,
                model=model or default_config.get("model", "default"),
                base_url=default_config.get("base_url"),
                timeout=config.ai_provider.timeout,
                max_retries=config.ai_provider.max_retries
            )
            config.default_provider = provider_type
            
            # Save updated config
            if self.save_config(config):
                messages.append(f"AI provider updated to {provider_type}")
                return True, messages
            else:
                return False, ["Failed to save configuration"]
                
        except Exception as e:
            logger.error(f"Error updating AI provider: {e}")
            return False, [f"Error updating AI provider: {str(e)}"]
    
    def update_audio_config(self, **kwargs) -> bool:
        """
        Update audio configuration.
        
        Args:
            **kwargs: Audio configuration parameters
            
        Returns:
            bool: True if updated successfully
        """
        try:
            config = self.get_current_config()
            
            # Update audio config fields
            for key, value in kwargs.items():
                if hasattr(config.audio, key):
                    setattr(config.audio, key, value)
                else:
                    logger.warning(f"Unknown audio config parameter: {key}")
            
            return self.save_config(config)
            
        except Exception as e:
            logger.error(f"Error updating audio configuration: {e}")
            return False
    
    def update_ui_config(self, **kwargs) -> bool:
        """
        Update UI configuration.
        
        Args:
            **kwargs: UI configuration parameters
            
        Returns:
            bool: True if updated successfully
        """
        try:
            config = self.get_current_config()
            
            # Validate update interval if provided
            if 'update_interval' in kwargs:
                is_valid, message = self.validator.validate_update_interval(kwargs['update_interval'])
                if not is_valid:
                    logger.error(f"Invalid update interval: {message}")
                    return False
            
            # Update UI config fields
            for key, value in kwargs.items():
                if hasattr(config.ui, key):
                    setattr(config.ui, key, value)
                else:
                    logger.warning(f"Unknown UI config parameter: {key}")
            
            return self.save_config(config)
            
        except Exception as e:
            logger.error(f"Error updating UI configuration: {e}")
            return False
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a specific provider.
        
        Args:
            provider: Provider name
            
        Returns:
            API key if available, None otherwise
        """
        config = self.get_current_config()
        if config.ai_provider.provider_type == provider:
            return config.ai_provider.api_key
        return None
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available AI providers.
        
        Returns:
            List of provider names
        """
        return list(self.default_provider_configs.keys())
    
    def get_provider_models(self, provider: str) -> List[str]:
        """
        Get available models for a provider.
        
        Args:
            provider: Provider name
            
        Returns:
            List of available models
        """
        return self.validator.get_available_models(provider)
    
    def validate_current_config(self) -> Tuple[bool, List[str]]:
        """
        Validate current configuration.
        
        Returns:
            Tuple of (is_valid, messages)
        """
        config = self.get_current_config()
        return self._validate_config(config)
    
    def reset_to_defaults(self) -> SystemConfig:
        """
        Reset configuration to defaults.
        
        Returns:
            Default system configuration
        """
        config = self._create_default_config()
        self.save_config(config)
        return config
    
    def export_config(self, file_path: str) -> bool:
        """
        Export configuration to a file.
        
        Args:
            file_path: Path to export file
            
        Returns:
            bool: True if exported successfully
        """
        try:
            config = self.get_current_config()
            config_dict = self._config_to_dict(config)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration exported to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, file_path: str) -> Tuple[bool, List[str]]:
        """
        Import configuration from a file.
        
        Args:
            file_path: Path to import file
            
        Returns:
            Tuple of (success, messages)
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            config = self._dict_to_config(config_data)
            is_valid, messages = self._validate_config(config)
            
            if is_valid:
                self.save_config(config)
                messages.append("Configuration imported successfully")
                return True, messages
            else:
                return False, messages
                
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False, [f"Error importing configuration: {str(e)}"]
    
    def _create_default_config(self) -> SystemConfig:
        """Create default system configuration."""
        # Try to get API key from environment or keys.py
        api_key = self._get_default_api_key()
        provider_type = "deepseek" if api_key else "openai"
        
        default_config = self.default_provider_configs[provider_type]
        
        ai_config = AIProviderConfig(
            provider_type=provider_type,
            api_key=api_key or "your-api-key-here",
            model=default_config["model"],
            base_url=default_config["base_url"]
        )
        
        audio_config = AudioConfig()
        ui_config = UIConfig()
        
        config = SystemConfig(
            ai_provider=ai_config,
            audio=audio_config,
            ui=ui_config,
            default_provider=provider_type
        )
        
        # Save default config
        self.save_config(config)
        return config
    
    def _get_default_api_key(self) -> Optional[str]:
        """Try to get API key from environment variables or keys.py."""
        # Try environment variables first
        env_keys = {
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
            "grok": "GROK_API_KEY",
            "claude": "CLAUDE_API_KEY",
            "volcano": "VOLCENGINE_API_KEY",
            "glm": "GLM_API_KEY"
        }
        
        for provider, env_var in env_keys.items():
            key = os.getenv(env_var)
            if key:
                return key
        
        # Try to import from keys.py as fallback
        try:
            import keys
            if hasattr(keys, 'OPENAI_API_KEY') and keys.OPENAI_API_KEY:
                return keys.OPENAI_API_KEY
            if hasattr(keys, 'VOLCENGINE_API_KEY') and keys.VOLCENGINE_API_KEY:
                return keys.VOLCENGINE_API_KEY
        except ImportError:
            pass
        
        return None
    
    def _validate_config(self, config: SystemConfig) -> Tuple[bool, List[str]]:
        """Validate system configuration."""
        messages = []
        is_valid = True
        
        # Validate AI provider config
        provider_valid, provider_messages = self.validator.validate_provider_config(
            config.ai_provider.provider_type,
            config.ai_provider.api_key,
            config.ai_provider.model
        )
        messages.extend(provider_messages)
        if not provider_valid:
            is_valid = False
        
        # Validate UI config
        if hasattr(config.ui, 'update_interval'):
            interval_valid, interval_msg = self.validator.validate_update_interval(config.ui.update_interval)
            messages.append(interval_msg)
            if not interval_valid:
                is_valid = False
        
        return is_valid, messages
    
    def _fix_config_issues(self, config: SystemConfig, messages: List[str]) -> SystemConfig:
        """Try to fix common configuration issues."""
        # If API key is invalid, try to get a new one from environment
        if any("Invalid API key" in msg for msg in messages):
            new_key = self._get_default_api_key()
            if new_key:
                config.ai_provider.api_key = new_key
                logger.info("Updated API key from environment")
        
        # If model is invalid, use default model for provider
        if any("not available" in msg for msg in messages):
            provider = config.ai_provider.provider_type
            if provider in self.default_provider_configs:
                config.ai_provider.model = self.default_provider_configs[provider]["model"]
                logger.info(f"Reset to default model for {provider}")
        
        return config
    
    def _config_to_dict(self, config: SystemConfig) -> Dict[str, Any]:
        """Convert SystemConfig to dictionary."""
        return {
            "ai_provider": asdict(config.ai_provider),
            "audio": asdict(config.audio),
            "ui": asdict(config.ui),
            "default_provider": config.default_provider
        }
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> SystemConfig:
        """Convert dictionary to SystemConfig."""
        ai_config = AIProviderConfig(**config_dict["ai_provider"])
        audio_config = AudioConfig(**config_dict.get("audio", {}))
        ui_config = UIConfig(**config_dict.get("ui", {}))
        
        return SystemConfig(
            ai_provider=ai_config,
            audio=audio_config,
            ui=ui_config,
            default_provider=config_dict.get("default_provider", "deepseek")
        )


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


# Global configuration manager instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """Get global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config() -> SystemConfig:
    """Load system configuration (convenience function)."""
    return get_config_manager().load_config()


def save_config(config: SystemConfig) -> bool:
    """Save system configuration (convenience function)."""
    return get_config_manager().save_config(config)


def get_current_config() -> SystemConfig:
    """Get current system configuration (convenience function)."""
    return get_config_manager().get_current_config()