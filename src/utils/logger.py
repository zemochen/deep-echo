"""
Logging utility module

Provides centralized logging configuration for the application.
Uses the enhanced loguru-based logging system via LoggerFactory.
"""

from typing import Optional
from src.utils.logger_factory import LoggerFactory
from src.utils.logger_config import LoggerConfig


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None
) -> 'LoggerAdapter':
    """
    Set up and configure a logger.
    
    Args:
        name: Logger name (typically __name__ of the module)
        level: Logging level (default: "INFO")
               Valid values: DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL
        log_file: Optional file path to write logs to
        
    Returns:
        Configured LoggerAdapter instance
        
    Example:
        >>> logger = setup_logger(__name__, level="DEBUG", log_file="./logs/app.log")
        >>> logger.info("Application started")
    """
    # Initialize factory if needed
    if not LoggerFactory.get_instance()._initialized:
        config = LoggerConfig(
            log_level=level,
            console_enabled=True,
            file_enabled=log_file is not None,
            log_file_path=log_file or "./logs/deepecho.log"
        )
        LoggerFactory.initialize(config)
    
    # Get logger from factory
    logger = LoggerFactory.get_logger(name)
    
    # Update level if specified
    if level != "INFO":
        logger.set_level(level)
    
    # Update file path if specified
    if log_file:
        logger.config.log_file_path = log_file
        logger.enable_file_output(True)
    
    return logger


def get_logger(name: str) -> 'LoggerAdapter':
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__ of the module)
        
    Returns:
        LoggerAdapter instance
        
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.debug("Debug message")
        >>> logger.error("Error message")
    """
    # Initialize factory with default config if needed
    if not LoggerFactory.get_instance()._initialized:
        LoggerFactory.initialize()
    
    return LoggerFactory.get_logger(name)


def configure_logging(
    level: str = "INFO",
    console_enabled: bool = True,
    file_enabled: bool = True,
    log_file_path: str = "./logs/deepecho.log",
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> None:
    """
    Configure the global logging system.
    
    Args:
        level: Log level (DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        console_enabled: Enable console output
        file_enabled: Enable file output
        log_file_path: Path to log file
        max_file_size: Maximum file size before rotation (in bytes)
        backup_count: Number of backup files to keep
        
    Example:
        >>> configure_logging(
        ...     level="DEBUG",
        ...     console_enabled=True,
        ...     file_enabled=True,
        ...     log_file_path="./logs/custom.log"
        ... )
    """
    config = LoggerConfig(
        log_level=level,
        console_enabled=console_enabled,
        file_enabled=file_enabled,
        log_file_path=log_file_path,
        max_file_size=max_file_size,
        backup_count=backup_count
    )
    LoggerFactory.initialize(config)


def set_log_level(level: str) -> None:
    """
    Set global log level.
    
    Args:
        level: Log level (DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        
    Example:
        >>> set_log_level("DEBUG")
    """
    LoggerFactory.set_level(level)


def enable_console(enabled: bool) -> None:
    """
    Enable or disable console output globally.
    
    Args:
        enabled: True to enable, False to disable
        
    Example:
        >>> enable_console(False)  # Disable console output
    """
    LoggerFactory.enable_console_output(enabled)


def enable_file_logging(enabled: bool) -> None:
    """
    Enable or disable file logging globally.
    
    Args:
        enabled: True to enable, False to disable
        
    Example:
        >>> enable_file_logging(True)  # Enable file logging
    """
    LoggerFactory.enable_file_output(enabled)


def shutdown_logging() -> None:
    """
    Shutdown the logging system and cleanup resources.
    
    Should be called when the application exits.
    
    Example:
        >>> shutdown_logging()
    """
    LoggerFactory.shutdown()
