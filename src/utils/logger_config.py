"""
Logger configuration module for loguru-based logging system.

Provides configuration management for the enhanced logging system.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Any, Optional
import os


@dataclass
class LoggerConfig:
    """
    Configuration for the loguru-based logging system.
    """
    
    # Basic configuration
    log_level: str = "INFO"  # DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
    
    # Console output configuration
    console_enabled: bool = True
    console_format: str = (
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
        "<level>{message}</level>"
    )
    
    # File output configuration
    file_enabled: bool = True
    log_file_path: str = "./logs/deepecho.log"
    file_format: str = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | {name}:{function} - {message}"
    )
    
    # File rotation configuration
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    
    # Transcription log configuration
    transcription_log_enabled: bool = True
    transcription_log_file: str = "./logs/transcription.log"
    transcription_log_level: str = "DEBUG"
    
    # Performance configuration
    async_logging: bool = True
    
    # Valid log levels
    VALID_LOG_LEVELS: List[str] = field(
        default_factory=lambda: ["DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
    )
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate configuration parameters.
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Validate log levels
        if self.log_level not in self.VALID_LOG_LEVELS:
            errors.append(f"Invalid log_level: {self.log_level}. Must be one of {self.VALID_LOG_LEVELS}")
        
        if self.transcription_log_level not in self.VALID_LOG_LEVELS:
            errors.append(f"Invalid transcription_log_level: {self.transcription_log_level}. Must be one of {self.VALID_LOG_LEVELS}")
        
        # Validate file sizes
        if self.max_file_size <= 0:
            errors.append(f"Invalid max_file_size: {self.max_file_size}. Must be positive")
        
        # Validate backup count
        if self.backup_count < 0:
            errors.append(f"Invalid backup_count: {self.backup_count}. Must be non-negative")
        
        # Validate file paths
        if self.file_enabled and not self.log_file_path:
            errors.append("log_file_path cannot be empty when file_enabled is True")
        
        if self.transcription_log_enabled and not self.transcription_log_file:
            errors.append("transcription_log_file cannot be empty when transcription_log_enabled is True")
        
        return len(errors) == 0, errors
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LoggerConfig':
        """
        Create LoggerConfig from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            
        Returns:
            LoggerConfig instance
        """
        # Extract only the fields that exist in the dataclass
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_dict = {k: v for k, v in config_dict.items() if k in valid_fields}
        
        return cls(**filtered_dict)
    
    @classmethod
    def from_file(cls, config_path: str) -> 'LoggerConfig':
        """
        Load LoggerConfig from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            LoggerConfig instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config file is invalid
        """
        import json
        
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            
            # Extract logging configuration
            logging_config = config_dict.get('logging', {})
            return cls.from_dict(logging_config)
        
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration file: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Configuration dictionary
        """
        return {
            'log_level': self.log_level,
            'console_enabled': self.console_enabled,
            'console_format': self.console_format,
            'file_enabled': self.file_enabled,
            'log_file_path': self.log_file_path,
            'file_format': self.file_format,
            'max_file_size': self.max_file_size,
            'backup_count': self.backup_count,
            'transcription_log_enabled': self.transcription_log_enabled,
            'transcription_log_file': self.transcription_log_file,
            'transcription_log_level': self.transcription_log_level,
            'async_logging': self.async_logging,
        }
