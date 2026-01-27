"""
Logger adapter module for loguru-based logging system.

Provides a unified logging interface for the application.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from loguru import logger

from backend.utils.logger_config import LoggerConfig


class LoggerAdapter:
    """
    Logger adapter based on loguru framework.
    
    Provides a unified logging interface for the application.
    """
    
    def __init__(self, name: str, config: LoggerConfig):
        """
        Initialize the logger adapter.
        
        Args:
            name: Logger name (typically __name__ of the module)
            config: LoggerConfig instance
        """
        self.name = name
        self.config = config
        self._console_handler_id: Optional[int] = None
        self._file_handler_id: Optional[int] = None
        self._transcription_handler_id: Optional[int] = None
        
        # Bind logger context
        self._logger = logger.bind(name=name)
    
    def _setup_handlers(self) -> None:
        """
        Setup loguru handlers based on configuration.
        """
        # Remove default handler
        logger.remove()
        
        # Add console handler if enabled
        if self.config.console_enabled:
            self._console_handler_id = logger.add(
                lambda msg: print(msg, end=''),
                format=self.config.console_format,
                level=self.config.log_level,
                colorize=True
            )
        
        # Add file handler if enabled
        if self.config.file_enabled:
            self._file_handler_id = logger.add(
                self.config.log_file_path,
                format=self.config.file_format,
                level=self.config.log_level,
                rotation=f"{self.config.max_file_size} B",
                retention=self.config.backup_count,
                colorize=False
            )
    
    def log_transcription(
        self,
        source: str,
        text: str,
        timestamp: datetime,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log audio transcription.
        
        Args:
            source: Audio source identifier ("You" or "Speaker")
            text: Transcribed text
            timestamp: Transcription timestamp
            metadata: Optional additional metadata
        """
        if not self.config.transcription_log_enabled:
            return
        
        # Skip empty or invalid transcriptions
        if not text or not text.strip():
            self._logger.warning(f"Empty transcription from {source}")
            return
        
        # Format transcription message
        text_length = len(text)
        preview = text[:50] + "..." if len(text) > 50 else text
        
        message = (
            f"[{source}] Length: {text_length} | "
            f"Preview: {preview} | "
            f"Time: {timestamp.isoformat()}"
        )
        
        # Log at configured transcription level
        if self.config.transcription_log_level == "DEBUG":
            self._logger.debug(message)
        elif self.config.transcription_log_level == "INFO":
            self._logger.info(message)
        else:
            self._logger.log(self.config.transcription_log_level, message)
        
        # Also log to transcription file if enabled
        if self.config.transcription_log_enabled and self._transcription_handler_id is None:
            self._setup_transcription_handler()
    
    def _setup_transcription_handler(self) -> None:
        """
        Setup dedicated transcription log handler.
        """
        if self._transcription_handler_id is not None:
            return
        
        self._transcription_handler_id = logger.add(
            self.config.transcription_log_file,
            format=self.config.file_format,
            level=self.config.transcription_log_level,
            rotation=f"{self.config.max_file_size} B",
            retention=self.config.backup_count,
            colorize=False,
            filter=lambda record: "[You]" in record["message"] or "[Speaker]" in record["message"]
        )
    
    def debug(self, message: str, **kwargs) -> None:
        """Log DEBUG level message."""
        self._logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs) -> None:
        """Log INFO level message."""
        self._logger.info(message, **kwargs)
    
    def success(self, message: str, **kwargs) -> None:
        """Log SUCCESS level message."""
        self._logger.success(message, **kwargs)
    
    def warning(self, message: str, **kwargs) -> None:
        """Log WARNING level message."""
        self._logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs) -> None:
        """Log ERROR level message."""
        self._logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs) -> None:
        """Log CRITICAL level message."""
        self._logger.critical(message, **kwargs)
    
    def set_level(self, level: str) -> None:
        """
        Set log level.
        
        Args:
            level: Log level (DEBUG, INFO, SUCCESS, WARNING, ERROR, CRITICAL)
        """
        if level not in self.config.VALID_LOG_LEVELS:
            self._logger.warning(f"Invalid log level: {level}")
            return
        
        self.config.log_level = level
        
        # Update handlers
        if self._console_handler_id is not None:
            logger.remove(self._console_handler_id)
            self._console_handler_id = logger.add(
                lambda msg: print(msg, end=''),
                format=self.config.console_format,
                level=level,
                colorize=True
            )
        
        if self._file_handler_id is not None:
            logger.remove(self._file_handler_id)
            self._file_handler_id = logger.add(
                self.config.log_file_path,
                format=self.config.file_format,
                level=level,
                rotation=f"{self.config.max_file_size} B",
                retention=self.config.backup_count,
                colorize=False
            )
    
    def enable_console_output(self, enabled: bool) -> None:
        """
        Enable or disable console output.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.config.console_enabled = enabled
        
        if enabled and self._console_handler_id is None:
            self._console_handler_id = logger.add(
                lambda msg: print(msg, end=''),
                format=self.config.console_format,
                level=self.config.log_level,
                colorize=True
            )
        elif not enabled and self._console_handler_id is not None:
            logger.remove(self._console_handler_id)
            self._console_handler_id = None
    
    def enable_file_output(self, enabled: bool) -> None:
        """
        Enable or disable file output.
        
        Args:
            enabled: True to enable, False to disable
        """
        self.config.file_enabled = enabled
        
        if enabled and self._file_handler_id is None:
            self._file_handler_id = logger.add(
                self.config.log_file_path,
                format=self.config.file_format,
                level=self.config.log_level,
                rotation=f"{self.config.max_file_size} B",
                retention=self.config.backup_count,
                colorize=False
            )
        elif not enabled and self._file_handler_id is not None:
            logger.remove(self._file_handler_id)
            self._file_handler_id = None
    
    def shutdown(self) -> None:
        """
        Shutdown the logger and cleanup resources.
        """
        if self._console_handler_id is not None:
            logger.remove(self._console_handler_id)
        
        if self._file_handler_id is not None:
            logger.remove(self._file_handler_id)
        
        if self._transcription_handler_id is not None:
            logger.remove(self._transcription_handler_id)
