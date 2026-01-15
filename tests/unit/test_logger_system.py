"""
Unit tests for the enhanced logging system based on loguru.
"""

import pytest
import os
import tempfile
from datetime import datetime
from pathlib import Path

from src.utils.logger_config import LoggerConfig
from src.utils.logger_adapter import LoggerAdapter
from src.utils.logger_factory import LoggerFactory


class TestLoggerConfig:
    """Test LoggerConfig class."""

    def test_default_config(self):
        """Test default configuration values."""
        config = LoggerConfig()
        assert config.log_level == "INFO"
        assert config.console_enabled is True
        assert config.file_enabled is True
        assert config.max_file_size == 10 * 1024 * 1024
        assert config.backup_count == 5

    def test_config_validation_valid(self):
        """Test validation with valid configuration."""
        config = LoggerConfig()
        is_valid, errors = config.validate()
        assert is_valid is True
        assert len(errors) == 0

    def test_config_validation_invalid_log_level(self):
        """Test validation with invalid log level."""
        config = LoggerConfig(log_level="INVALID")
        is_valid, errors = config.validate()
        assert is_valid is False
        assert len(errors) > 0

    def test_config_validation_invalid_file_size(self):
        """Test validation with invalid file size."""
        config = LoggerConfig(max_file_size=-1)
        is_valid, errors = config.validate()
        assert is_valid is False
        assert len(errors) > 0

    def test_config_from_dict(self):
        """Test creating config from dictionary."""
        config_dict = {
            'log_level': 'DEBUG',
            'console_enabled': False,
            'file_enabled': True
        }
        config = LoggerConfig.from_dict(config_dict)
        assert config.log_level == 'DEBUG'
        assert config.console_enabled is False
        assert config.file_enabled is True

    def test_config_to_dict(self):
        """Test converting config to dictionary."""
        config = LoggerConfig(log_level='DEBUG')
        config_dict = config.to_dict()
        assert config_dict['log_level'] == 'DEBUG'
        assert 'console_enabled' in config_dict
        assert 'file_enabled' in config_dict


class TestLoggerAdapter:
    """Test LoggerAdapter class."""

    def test_logger_adapter_creation(self):
        """Test creating logger adapter."""
        config = LoggerConfig()
        adapter = LoggerAdapter("test_logger", config)
        assert adapter.name == "test_logger"
        assert adapter.config == config

    def test_logger_adapter_debug(self, caplog):
        """Test debug logging."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(
                log_level="DEBUG",
                log_file_path=os.path.join(tmpdir, "test.log"),
                console_enabled=False
            )
            adapter = LoggerAdapter("test", config)
            adapter._setup_handlers()
            adapter.debug("Test debug message")

            # Check if file was created
            assert os.path.exists(config.log_file_path)

    def test_logger_adapter_info(self):
        """Test info logging."""
        config = LoggerConfig(console_enabled=False)
        adapter = LoggerAdapter("test", config)
        adapter._setup_handlers()
        # Should not raise exception
        adapter.info("Test info message")

    def test_logger_adapter_warning(self):
        """Test warning logging."""
        config = LoggerConfig(console_enabled=False)
        adapter = LoggerAdapter("test", config)
        adapter._setup_handlers()
        # Should not raise exception
        adapter.warning("Test warning message")

    def test_logger_adapter_error(self):
        """Test error logging."""
        config = LoggerConfig(console_enabled=False)
        adapter = LoggerAdapter("test", config)
        adapter._setup_handlers()
        # Should not raise exception
        adapter.error("Test error message")

    def test_logger_adapter_set_level(self):
        """Test setting log level."""
        config = LoggerConfig(console_enabled=False)
        adapter = LoggerAdapter("test", config)
        adapter._setup_handlers()
        adapter.set_level("DEBUG")
        assert adapter.config.log_level == "DEBUG"

    def test_logger_adapter_enable_console(self):
        """Test enabling/disabling console output."""
        config = LoggerConfig(console_enabled=True)
        adapter = LoggerAdapter("test", config)
        adapter._setup_handlers()
        adapter.error("Test error message")

        # Disable console
        adapter.enable_console_output(False)
        assert adapter.config.console_enabled is False

        # Enable console
        adapter.enable_console_output(True)
        assert adapter.config.console_enabled is True

    def test_logger_adapter_log_transcription(self):
        """Test logging transcription."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = LoggerConfig(
                transcription_log_enabled=True,
                transcription_log_file=os.path.join(tmpdir, "transcription.log"),
                console_enabled=False
            )
            adapter = LoggerAdapter("test", config)
            adapter._setup_handlers()

            # Log transcription
            adapter.log_transcription(
                source="You",
                text="Hello, this is a test transcription",
                timestamp=datetime.now()
            )

            # Check if transcription file was created
            assert os.path.exists(config.transcription_log_file)

    def test_logger_adapter_log_empty_transcription(self):
        """Test logging empty transcription."""
        config = LoggerConfig(console_enabled=False)
        adapter = LoggerAdapter("test", config)
        adapter._setup_handlers()

        # Should not raise exception
        adapter.log_transcription(
            source="You",
            text="",
            timestamp=datetime.now()
        )


class TestLoggerFactory:
    """Test LoggerFactory class."""

    def setup_method(self):
        """Setup before each test."""
        LoggerFactory.shutdown()

    def teardown_method(self):
        """Teardown after each test."""
        LoggerFactory.shutdown()

    def test_factory_singleton(self):
        """Test factory singleton pattern."""
        factory1 = LoggerFactory.get_instance()
        factory2 = LoggerFactory.get_instance()
        assert factory1 is factory2

    def test_factory_initialize(self):
        """Test factory initialization."""
        config = LoggerConfig(console_enabled=False)
        LoggerFactory.initialize(config)
        assert LoggerFactory._initialized is True

    def test_factory_get_logger(self):
        """Test getting logger from factory."""
        LoggerFactory.initialize()

        logger1 = LoggerFactory.get_logger("test1")
        logger2 = LoggerFactory.get_logger("test1")


        assert logger1 is logger2
        assert isinstance(logger1, LoggerAdapter)

    def test_factory_multiple_loggers(self):
        """Test creating multiple loggers."""
        LoggerFactory.initialize()

        logger1 = LoggerFactory.get_logger("test1")
        logger2 = LoggerFactory.get_logger("test2")

        assert logger1 is not logger2
        assert logger1.name == "test1"
        assert logger2.name == "test2"

    def test_factory_set_level(self):
        """Test setting global log level."""
        LoggerFactory.initialize()

        LoggerFactory.set_level("DEBUG")
        assert LoggerFactory._config.log_level == "DEBUG"

    def test_factory_enable_console(self):
        """Test enabling/disabling console output."""
        LoggerFactory.initialize()

        LoggerFactory.enable_console_output(False)
        assert LoggerFactory._config.console_enabled is False

        LoggerFactory.enable_console_output(True)
        logger1 = LoggerFactory.get_logger("testlogger")
        logger1.info("this is info log")
        logger1.debug("this is debug log")
        logger1.error("this is error log")
        assert LoggerFactory._config.console_enabled is True

    def test_factory_shutdown(self):
        """Test factory shutdown."""
        LoggerFactory.initialize()
        LoggerFactory.shutdown()
        assert LoggerFactory._initialized is False
        assert len(LoggerFactory._loggers) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
