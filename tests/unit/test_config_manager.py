"""
Unit tests for configuration manager and system startup logic.

Tests configuration validation, loading, startup dependency checks,
and error handling scenarios.
"""

import unittest
import tempfile
import json
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open

from src.config.config_manager import (
    ConfigManager, SystemConfig, AIProviderConfig, AudioConfig, UIConfig,
    ConfigurationError, get_config_manager, load_config, save_config
)
from src.config.validator import ConfigValidator


class TestConfigManager(unittest.TestCase):
    """Test cases for ConfigManager class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigManager(config_dir=self.temp_dir)
        
        # Sample valid configuration
        self.valid_config = SystemConfig(
            ai_provider=AIProviderConfig(
                provider_type="deepseek",
                api_key="sk-" + "a" * 48,
                model="deepseek-chat",
                base_url="https://api.deepseek.com/v1"
            ),
            audio=AudioConfig(
                record_timeout=3,
                phrase_timeout=3.05,
                use_api_mode=False
            ),
            ui=UIConfig(
                update_interval=5,
                use_new_ui=True
            ),
            default_provider="deepseek"
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init_creates_config_directory(self):
        """Test that ConfigManager creates config directory on initialization."""
        new_temp_dir = os.path.join(self.temp_dir, "new_config")
        manager = ConfigManager(config_dir=new_temp_dir)
        
        self.assertTrue(os.path.exists(new_temp_dir))
        self.assertTrue(os.path.isdir(new_temp_dir))
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        # Save configuration
        success = self.config_manager.save_config(self.valid_config)
        self.assertTrue(success)
        
        # Verify file exists
        self.assertTrue(self.config_manager.config_file.exists())
        
        # Load configuration
        loaded_config = self.config_manager.load_config()
        
        # Verify loaded config matches saved config
        self.assertEqual(loaded_config.ai_provider.provider_type, "deepseek")
        self.assertEqual(loaded_config.ai_provider.api_key, "sk-" + "a" * 48)
        self.assertEqual(loaded_config.ai_provider.model, "deepseek-chat")
        self.assertEqual(loaded_config.default_provider, "deepseek")
    
    def test_load_config_creates_default_when_missing(self):
        """Test that load_config creates default configuration when file is missing."""
        # Ensure no config file exists
        if self.config_manager.config_file.exists():
            self.config_manager.config_file.unlink()
        
        # Load config should create default
        config = self.config_manager.load_config()
        
        # Verify default config properties
        self.assertIsInstance(config, SystemConfig)
        self.assertIsInstance(config.ai_provider, AIProviderConfig)
        self.assertIsInstance(config.audio, AudioConfig)
        self.assertIsInstance(config.ui, UIConfig)
    
    def test_load_config_handles_invalid_json(self):
        """Test that load_config handles invalid JSON gracefully."""
        # Write invalid JSON to config file
        with open(self.config_manager.config_file, 'w') as f:
            f.write("invalid json content")
        
        # Should fall back to default config
        config = self.config_manager.load_config()
        self.assertIsInstance(config, SystemConfig)
    
    def test_save_config_validates_before_saving(self):
        """Test that save_config validates configuration before saving."""
        # Create invalid config
        invalid_config = SystemConfig(
            ai_provider=AIProviderConfig(
                provider_type="invalid_provider",
                api_key="invalid_key",
                model="invalid_model"
            ),
            audio=AudioConfig(),
            ui=UIConfig(),
            default_provider="invalid_provider"
        )
        
        # Should fail to save invalid config
        success = self.config_manager.save_config(invalid_config)
        self.assertFalse(success)
    
    def test_update_ai_provider_valid(self):
        """Test updating AI provider with valid configuration."""
        success, messages = self.config_manager.update_ai_provider(
            "deepseek", 
            "sk-" + "b" * 48, 
            "deepseek-chat"
        )
        
        self.assertTrue(success)
        self.assertIn("API key format is valid", " ".join(messages))
        
        # Verify config was updated
        config = self.config_manager.get_current_config()
        self.assertEqual(config.ai_provider.provider_type, "deepseek")
        self.assertEqual(config.ai_provider.api_key, "sk-" + "b" * 48)
    
    def test_update_ai_provider_invalid(self):
        """Test updating AI provider with invalid configuration."""
        success, messages = self.config_manager.update_ai_provider(
            "deepseek", 
            "invalid_key", 
            "deepseek-chat"
        )
        
        self.assertFalse(success)
        self.assertIn("Invalid API key", " ".join(messages))
    
    def test_update_audio_config(self):
        """Test updating audio configuration."""
        # First set up a valid config
        self.config_manager.save_config(self.valid_config)
        
        success = self.config_manager.update_audio_config(
            record_timeout=5,
            use_api_mode=True
        )
        
        self.assertTrue(success)
        
        # Verify config was updated
        config = self.config_manager.get_current_config()
        self.assertEqual(config.audio.record_timeout, 5)
        self.assertTrue(config.audio.use_api_mode)
    
    def test_update_ui_config(self):
        """Test updating UI configuration."""
        # First set up a valid config
        self.config_manager.save_config(self.valid_config)
        
        success = self.config_manager.update_ui_config(
            update_interval=10,
            use_new_ui=False
        )
        
        self.assertTrue(success)
        
        # Verify config was updated
        config = self.config_manager.get_current_config()
        self.assertEqual(config.ui.update_interval, 10)
        self.assertFalse(config.ui.use_new_ui)
    
    def test_update_ui_config_invalid_interval(self):
        """Test updating UI config with invalid update interval."""
        success = self.config_manager.update_ui_config(update_interval=0)
        self.assertFalse(success)
        
        success = self.config_manager.update_ui_config(update_interval=100)
        self.assertFalse(success)
    
    def test_get_api_key(self):
        """Test getting API key for current provider."""
        # Set up config
        self.config_manager.save_config(self.valid_config)
        
        # Get API key for current provider
        api_key = self.config_manager.get_api_key("deepseek")
        self.assertEqual(api_key, "sk-" + "a" * 48)
        
        # Get API key for different provider
        api_key = self.config_manager.get_api_key("openai")
        self.assertIsNone(api_key)
    
    def test_get_available_providers(self):
        """Test getting list of available providers."""
        providers = self.config_manager.get_available_providers()
        
        expected_providers = ["deepseek", "openai", "grok", "claude", "volcano", "glm"]
        for provider in expected_providers:
            self.assertIn(provider, providers)
    
    def test_get_provider_models(self):
        """Test getting available models for a provider."""
        models = self.config_manager.get_provider_models("deepseek")
        self.assertIn("deepseek-chat", models)
        self.assertIn("deepseek-coder", models)
        
        models = self.config_manager.get_provider_models("openai")
        self.assertIn("gpt-3.5-turbo", models)
        self.assertIn("gpt-4", models)
    
    def test_validate_current_config(self):
        """Test validating current configuration."""
        # Set valid config
        self.config_manager.save_config(self.valid_config)
        
        is_valid, messages = self.config_manager.validate_current_config()
        self.assertTrue(is_valid)
    
    def test_reset_to_defaults(self):
        """Test resetting configuration to defaults."""
        # Set custom config first
        self.config_manager.save_config(self.valid_config)
        
        # Reset to defaults
        default_config = self.config_manager.reset_to_defaults()
        
        self.assertIsInstance(default_config, SystemConfig)
        # Should have created a new config file
        self.assertTrue(self.config_manager.config_file.exists())
    
    def test_export_config(self):
        """Test exporting configuration to file."""
        # Set up config
        self.config_manager.save_config(self.valid_config)
        
        # Export to temporary file
        export_path = os.path.join(self.temp_dir, "exported_config.json")
        success = self.config_manager.export_config(export_path)
        
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_path))
        
        # Verify exported content
        with open(export_path, 'r') as f:
            exported_data = json.load(f)
        
        self.assertEqual(exported_data["default_provider"], "deepseek")
        self.assertEqual(exported_data["ai_provider"]["provider_type"], "deepseek")
    
    def test_import_config(self):
        """Test importing configuration from file."""
        # Create config file to import
        import_data = {
            "ai_provider": {
                "provider_type": "openai",
                "api_key": "sk-" + "c" * 48,
                "model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1",
                "timeout": 30,
                "max_retries": 3
            },
            "audio": {
                "record_timeout": 3,
                "phrase_timeout": 3.05,
                "max_phrases": 10,
                "energy_threshold": 1000,
                "use_api_mode": False
            },
            "ui": {
                "update_interval": 5,
                "processing_interval": 0.1,
                "ui_update_interval": 0.3,
                "use_new_ui": True
            },
            "default_provider": "openai"
        }
        
        import_path = os.path.join(self.temp_dir, "import_config.json")
        with open(import_path, 'w') as f:
            json.dump(import_data, f)
        
        # Import config
        success, messages = self.config_manager.import_config(import_path)
        
        self.assertTrue(success)
        
        # Verify imported config
        config = self.config_manager.get_current_config()
        self.assertEqual(config.ai_provider.provider_type, "openai")
        self.assertEqual(config.ai_provider.api_key, "sk-" + "c" * 48)
    
    def test_import_config_invalid_file(self):
        """Test importing configuration from invalid file."""
        # Create invalid config file
        import_path = os.path.join(self.temp_dir, "invalid_config.json")
        with open(import_path, 'w') as f:
            f.write("invalid json")
        
        # Import should fail
        success, messages = self.config_manager.import_config(import_path)
        self.assertFalse(success)
    
    @patch.dict(os.environ, {'DEEPSEEK_API_KEY': 'sk-env-key-123'})
    def test_get_default_api_key_from_env(self):
        """Test getting default API key from environment variables."""
        # Create new manager to trigger key detection
        manager = ConfigManager(config_dir=os.path.join(self.temp_dir, "env_test"))
        
        # Should detect key from environment
        key = manager._get_default_api_key()
        self.assertEqual(key, 'sk-env-key-123')
    
    @patch('builtins.__import__')
    def test_get_default_api_key_from_keys_module(self, mock_import):
        """Test getting default API key from keys.py module."""
        # Mock keys module
        mock_keys = MagicMock()
        mock_keys.OPENAI_API_KEY = "sk-keys-module-123"
        
        def import_side_effect(name, *args, **kwargs):
            if name == 'keys':
                return mock_keys
            raise ImportError(f"No module named '{name}'")
        
        mock_import.side_effect = import_side_effect
        
        # Should detect key from keys module
        key = self.config_manager._get_default_api_key()
        self.assertEqual(key, "sk-keys-module-123")


class TestSystemStartup(unittest.TestCase):
    """Test cases for system startup logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_validate_dependencies_ffmpeg_available(self, mock_run):
        """Test dependency validation when FFmpeg is available."""
        # Mock successful FFmpeg check
        mock_run.return_value.returncode = 0
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        self.assertTrue(success)
        self.assertIn("Dependencies validation passed", message)
    
    @patch('subprocess.run')
    def test_validate_dependencies_ffmpeg_missing(self, mock_run):
        """Test dependency validation when FFmpeg is missing."""
        # Mock FFmpeg not found
        mock_run.side_effect = FileNotFoundError()
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        self.assertFalse(success)
        self.assertIn("ffmpeg library is not installed", message)
    
    @patch('subprocess.run')
    def test_validate_dependencies_ffmpeg_timeout(self, mock_run):
        """Test dependency validation when FFmpeg times out."""
        # Mock FFmpeg timeout
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 10)
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        self.assertFalse(success)
        self.assertIn("ffmpeg library is not installed", message)
    
    def test_load_configuration_success(self):
        """Test successful configuration loading."""
        from src.main import DeepEchoApplication
        
        # Create app with temporary config directory
        app = DeepEchoApplication()
        app.config_manager = ConfigManager(config_dir=self.temp_dir)
        
        success = app.load_configuration()
        self.assertTrue(success)
        self.assertIsNotNone(app.config)
    
    @patch('src.config.config_manager.ConfigManager.load_config')
    def test_load_configuration_failure(self, mock_load):
        """Test configuration loading failure."""
        # Mock configuration loading failure
        mock_load.side_effect = Exception("Config load error")
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success = app.load_configuration()
        self.assertFalse(success)
    
    def test_parse_arguments(self):
        """Test command line argument parsing."""
        from src.main import parse_arguments
        
        # Mock sys.argv
        import sys
        original_argv = sys.argv
        
        try:
            # Test various argument combinations
            sys.argv = ['main.py', '--api', '--verbose']
            args = parse_arguments()
            self.assertTrue(args['use_api'])
            self.assertTrue(args['verbose'])
            self.assertFalse(args['use_new_ui'])
            
            sys.argv = ['main.py', '--new-ui', '--help']
            args = parse_arguments()
            self.assertTrue(args['use_new_ui'])
            self.assertTrue(args['help'])
            self.assertFalse(args['use_api'])
            
        finally:
            sys.argv = original_argv
    
    def test_show_help(self):
        """Test help message display."""
        from src.main import show_help
        
        # Should not raise any exceptions
        try:
            show_help()
        except Exception as e:
            self.fail(f"show_help() raised an exception: {e}")


class TestGlobalFunctions(unittest.TestCase):
    """Test cases for global convenience functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        # Reset global config manager
        import src.config.config_manager
        src.config.config_manager._config_manager = None
    
    def test_get_config_manager_singleton(self):
        """Test that get_config_manager returns singleton instance."""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        self.assertIs(manager1, manager2)
    
    @patch('src.config.config_manager.get_config_manager')
    def test_load_config_convenience_function(self, mock_get_manager):
        """Test load_config convenience function."""
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager
        
        load_config()
        mock_manager.load_config.assert_called_once()
    
    @patch('src.config.config_manager.get_config_manager')
    def test_save_config_convenience_function(self, mock_get_manager):
        """Test save_config convenience function."""
        mock_manager = MagicMock()
        mock_get_manager.return_value = mock_manager
        
        config = SystemConfig(
            ai_provider=AIProviderConfig("test", "key", "model"),
            audio=AudioConfig(),
            ui=UIConfig(),
            default_provider="test"
        )
        
        save_config(config)
        mock_manager.save_config.assert_called_once_with(config)


class TestConfigurationDataClasses(unittest.TestCase):
    """Test cases for configuration data classes."""
    
    def test_ai_provider_config_creation(self):
        """Test AIProviderConfig creation and defaults."""
        config = AIProviderConfig(
            provider_type="deepseek",
            api_key="test-key",
            model="deepseek-chat"
        )
        
        self.assertEqual(config.provider_type, "deepseek")
        self.assertEqual(config.api_key, "test-key")
        self.assertEqual(config.model, "deepseek-chat")
        self.assertIsNone(config.base_url)
        self.assertEqual(config.timeout, 30)
        self.assertEqual(config.max_retries, 3)
    
    def test_audio_config_defaults(self):
        """Test AudioConfig default values."""
        config = AudioConfig()
        
        self.assertEqual(config.record_timeout, 3)
        self.assertEqual(config.phrase_timeout, 3.05)
        self.assertEqual(config.max_phrases, 10)
        self.assertEqual(config.energy_threshold, 1000)
        self.assertFalse(config.use_api_mode)
    
    def test_ui_config_defaults(self):
        """Test UIConfig default values."""
        config = UIConfig()
        
        self.assertEqual(config.update_interval, 5)
        self.assertEqual(config.processing_interval, 0.1)
        self.assertEqual(config.ui_update_interval, 0.3)
        self.assertTrue(config.use_new_ui)
    
    def test_system_config_creation(self):
        """Test SystemConfig creation."""
        ai_config = AIProviderConfig("test", "key", "model")
        audio_config = AudioConfig()
        ui_config = UIConfig()
        
        system_config = SystemConfig(
            ai_provider=ai_config,
            audio=audio_config,
            ui=ui_config,
            default_provider="test"
        )
        
        self.assertEqual(system_config.ai_provider, ai_config)
        self.assertEqual(system_config.audio, audio_config)
        self.assertEqual(system_config.ui, ui_config)
        self.assertEqual(system_config.default_provider, "test")


if __name__ == '__main__':
    unittest.main()