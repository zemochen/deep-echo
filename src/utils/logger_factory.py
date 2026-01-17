"""
Logger factory module for loguru-based logging system.

Provides factory methods for creating and managing logger instances.
"""

from typing import Optional, Dict
from loguru import logger
import os

from src.utils.logger_config import LoggerConfig
from src.utils.logger_adapter import LoggerAdapter


class LoggerFactory:
    """
    Factory class for creating and managing logger instances.
    
    Implements singleton pattern for global logger management.
    """
    
    _instance: Optional['LoggerFactory'] = None
    _loggers: Dict[str, LoggerAdapter] = {}
    _config: Optional[LoggerConfig] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'LoggerFactory':
        """Implement singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'LoggerFactory':
        """
        Get factory singleton instance.
        
        Returns:
            LoggerFactory instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def initialize(cls, config: Optional[LoggerConfig] = None) -> None:
        """
        Initialize the logger factory.
        
        Args:
            config: LoggerConfig instance (uses default if None)
        """
        instance = cls.get_instance()
        
        if instance._initialized:
            return
        
        # Use provided config or create default
        if config is None:
            config = LoggerConfig()
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            # Log warning using loguru directly
            logger.warning(f"Configuration validation errors: {errors}")
            # Continue with default values
        
        cls._config = config
        cls._configure_loguru(config)
        cls._initialized = True
    
    @classmethod
    def _configure_loguru(cls, config: LoggerConfig) -> None:
        """
        Configure loguru framework.
        
        Args:
            config: LoggerConfig instance
        """
        # Remove default handler
        logger.remove()
        
        # Create log directories if they don't exist
        if config.file_enabled:
            log_dir = os.path.dirname(config.log_file_path)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to create log directory {log_dir}: {e}")
        
        if config.transcription_log_enabled:
            log_dir = os.path.dirname(config.transcription_log_file)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to create transcription log directory {log_dir}: {e}")
        
        # Add console handler if enabled
        if config.console_enabled:
            try:
                logger.add(
                    lambda msg: print(msg, end=''),
                    format=config.console_format,
                    level=config.log_level,
                    colorize=True
                )
            except Exception as e:
                logger.warning(f"Failed to add console handler: {e}")
        
        # Add file handler if enabled
        if config.file_enabled:
            try:
                logger.add(
                    config.log_file_path,
                    format=config.file_format,
                    level=config.log_level,
                    rotation=f"{config.max_file_size} B",
                    retention=config.backup_count,
                    colorize=False
                )
            except Exception as e:
                logger.warning(f"Failed to add file handler: {e}")
        
        # Add transcription handler if enabled
        if config.transcription_log_enabled:
            try:
                logger.add(
                    config.transcription_log_file,
                    format=config.file_format,
                    level=config.transcription_log_level,
                    rotation=f"{config.max_file_size} B",
                    retention=config.backup_count,
                    colorize=False,
                    filter=lambda record: "[You]" in record["message"] or "[Speaker]" in record["message"]
                )
            except Exception as e:
                logger.warning(f"Failed to add transcription handler: {e}")
    
    @classmethod
    def get_logger(cls, name: str) -> LoggerAdapter:
        """
        Get or create a logger instance.
        
        Args:
            name: Logger name (typically __name__ of the module)
            
        Returns:
            LoggerAdapter instance
        """
        instance = cls.get_instance()
        
        # Initialize if not already done
        if not instance._initialized:
            instance.initialize()
        
        # Return existing logger if available
        if name in instance._loggers:
            return instance._loggers[name]
        
        # Create new logger
        config = instance._config or LoggerConfig()
        logger_adapter = LoggerAdapter(name, config)
        instance._loggers[name] = logger_adapter
        
        return logger_adapter
    
    @classmethod
    def set_level(cls, level: str) -> None:
        """
        Set global log level.
        
        Args:
            level: Log level (DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        """
        instance = cls.get_instance()
        
        if instance._config is None:
            return
        
        instance._config.log_level = level
        
        # Update all loggers
        for logger_adapter in instance._loggers.values():
            logger_adapter.set_level(level)
    
    @classmethod
    def enable_console_output(cls, enabled: bool) -> None:
        """
        Enable or disable console output globally.
        
        Args:
            enabled: True to enable, False to disable
        """
        instance = cls.get_instance()
        
        if instance._config is None:
            return
        
        instance._config.console_enabled = enabled
        
        # Update all loggers
        for logger_adapter in instance._loggers.values():
            logger_adapter.enable_console_output(enabled)
    
    @classmethod
    def enable_file_output(cls, enabled: bool) -> None:
        """
        Enable or disable file output globally.
        
        Args:
            enabled: True to enable, False to disable
        """
        instance = cls.get_instance()
        
        if instance._config is None:
            return
        
        instance._config.file_enabled = enabled
        
        # Update all loggers
        for logger_adapter in instance._loggers.values():
            logger_adapter.enable_file_output(enabled)
    
    @classmethod
    def shutdown(cls) -> None:
        """
        Shutdown the logger factory and cleanup resources.
        """
        instance = cls.get_instance()
        
        # Shutdown all loggers
        for logger_adapter in instance._loggers.values():
            logger_adapter.shutdown()
        
        # Clear loggers
        cls._loggers.clear()
        cls._initialized = False
        cls._config = None
        
        # Remove all handlers
        logger.remove()
