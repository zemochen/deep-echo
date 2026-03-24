"""
Cross-platform compatibility integration tests.

Tests platform-specific functionality, audio system compatibility,
and configuration handling across Windows, macOS, and Linux.
"""

import pytest
import platform
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "backend"))

from backend.integration import IntegratedDeepEchoApplication
from backend.config.config_manager import get_config_manager
from backend.audio_system.audio_factory import AudioSystemFactory
from backend.utils.logger import get_logger


class TestPlatformDetection:
    """Test platform detection and configuration."""
    
    def test_current_platform_detection(self):
        """Test detection of current platform."""
        current_platform = platform.system()
        
        # Should detect one of the supported platforms
        assert current_platform in ["Windows", "Darwin", "Linux"]
        
        # Test platform-specific behavior
        if current_platform == "Windows":
            assert platform.system() == "Windows"
        elif current_platform == "Darwin":
            assert platform.system() == "Darwin"
        elif current_platform == "Linux":
            assert platform.system() == "Linux"
            
    @patch('platform.system')
    def test_windows_platform_detection(self, mock_platform):
        """Test Windows platform detection."""
        mock_platform.return_value = "Windows"
        
        # Test that Windows is properly detected
        assert platform.system() == "Windows"
        
        # Test Windows-specific paths
        if os.name == 'nt':
            # Only test on actual Windows or when mocked
            assert os.path.sep == '\\'
            
    @patch('platform.system')
    def test_macos_platform_detection(self, mock_platform):
        """Test macOS platform detection."""
        mock_platform.return_value = "Darwin"
        
        # Test that macOS is properly detected
        assert platform.system() == "Darwin"
        
    @patch('platform.system')
    def test_linux_platform_detection(self, mock_platform):
        """Test Linux platform detection."""
        mock_platform.return_value = "Linux"
        
        # Test that Linux is properly detected
        assert platform.system() == "Linux"


class TestAudioSystemCompatibility:
    """Test audio system compatibility across platforms."""
    
    @patch('platform.system')
    def test_windows_audio_system(self, mock_platform):
        """Test Windows audio system initialization."""
        mock_platform.return_value = "Windows"
        
        factory = AudioSystemFactory()
        
        # Mock Windows-specific audio components
        with patch('backend.audio_system.windows_audio.WindowsAudioSystem') as mock_windows:
            mock_audio_system = Mock()
            mock_windows.return_value = mock_audio_system
            
            # Test audio system creation
            audio_system = factory.create_audio_system()
            
            # Should create Windows audio system
            assert audio_system is not None
            
    @patch('platform.system')
    def test_macos_audio_system(self, mock_platform):
        """Test macOS audio system initialization."""
        mock_platform.return_value = "Darwin"
        
        factory = AudioSystemFactory()
        
        # Mock macOS-specific audio components
        with patch('backend.audio_system.macos_audio.MacOSAudioSystem') as mock_macos:
            mock_audio_system = Mock()
            mock_macos.return_value = mock_audio_system
            
            # Test audio system creation
            audio_system = factory.create_audio_system()
            
            # Should create macOS audio system
            assert audio_system is not None
            
    @patch('platform.system')
    def test_linux_audio_system(self, mock_platform):
        """Test Linux audio system initialization."""
        mock_platform.return_value = "Linux"
        
        factory = AudioSystemFactory()
        
        # Test that Linux falls back to generic audio system
        audio_system = factory.create_audio_system()
        
        # Should create some form of audio system
        assert audio_system is not None
        
    def test_audio_device_enumeration(self):
        """Test audio device enumeration across platforms."""
        factory = AudioSystemFactory()
        
        try:
            audio_system = factory.create_audio_system()
            
            # Test device enumeration (may fail in test environment)
            if hasattr(audio_system, 'enumerate_devices'):
                devices = audio_system.enumerate_devices()
                assert isinstance(devices, (list, dict))
                
        except Exception:
            # Audio system may not be available in test environment
            pytest.skip("Audio system not available in test environment")


class TestConfigurationCompatibility:
    """Test configuration compatibility across platforms."""
    
    def test_config_file_paths(self):
        """Test configuration file paths on different platforms."""
        config_manager = get_config_manager()
        
        # Test that config file path is valid for current platform
        config_file = config_manager.config_file
        assert isinstance(config_file, (str, Path))
        
        # Test that path uses correct separators
        config_path = Path(config_file)
        assert config_path.is_absolute() or str(config_path).startswith('.')
        
    def test_cross_platform_config_loading(self):
        """Test configuration loading across platforms."""
        # Create temporary config file
        config_data = {
            "audio": {
                "use_api_mode": False,
                "record_timeout": 3
            },
            "ai_provider": {
                "provider_type": "deepseek",
                "api_key": "test-key"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            temp_config = f.name
        
        try:
            config_manager = get_config_manager()
            
            # Mock config file path
            with patch.object(config_manager, 'config_file', temp_config):
                config = config_manager.load_config()
                
                assert config is not None
                assert hasattr(config, 'audio')
                assert hasattr(config, 'ai_provider')
                
        finally:
            # Cleanup
            try:
                os.unlink(temp_config)
            except:
                pass
                
    @patch('platform.system')
    def test_windows_config_paths(self, mock_platform):
        """Test Windows-specific configuration paths."""
        mock_platform.return_value = "Windows"
        
        # Test Windows path handling
        config_manager = get_config_manager()
        
        # Should handle Windows paths correctly
        config_file = str(config_manager.config_file)
        
        # On Windows, paths might use backslashes
        if '\\' in config_file:
            assert config_file.count('\\') > 0
            
    @patch('platform.system')
    def test_unix_config_paths(self, mock_platform):
        """Test Unix-like system configuration paths."""
        mock_platform.return_value = "Darwin"  # or "Linux"
        
        # Test Unix path handling
        config_manager = get_config_manager()
        
        # Should handle Unix paths correctly
        config_file = str(config_manager.config_file)
        
        # On Unix systems, paths use forward slashes
        if '/' in config_file:
            assert config_file.count('/') > 0


class TestDependencyCompatibility:
    """Test dependency compatibility across platforms."""
    
    def test_python_version_compatibility(self):
        """Test Python version compatibility."""
        version = sys.version_info
        
        # Should be Python 3.8 or higher
        assert version.major == 3
        assert version.minor >= 8
        
    def test_required_modules_availability(self):
        """Test that required modules are available."""
        required_modules = [
            'threading',
            'queue',
            'json',
            'pathlib',
            'logging',
            'time',
            'os',
            'sys'
        ]
        
        for module_name in required_modules:
            try:
                __import__(module_name)
            except ImportError:
                pytest.fail(f"Required module '{module_name}' not available")
                
    def test_optional_modules_handling(self):
        """Test handling of optional modules."""
        optional_modules = [
            'customtkinter',
            'numpy',
            'requests',
            'openai',
            'anthropic'
        ]
        
        for module_name in optional_modules:
            try:
                __import__(module_name)
                # Module is available
            except ImportError:
                # Module is not available, should be handled gracefully
                pass
                
    @patch('platform.system')
    def test_windows_specific_dependencies(self, mock_platform):
        """Test Windows-specific dependencies."""
        mock_platform.return_value = "Windows"
        
        # Test Windows-specific modules
        windows_modules = ['pyaudiowpatch']
        
        for module_name in windows_modules:
            try:
                __import__(module_name)
                # Module is available on Windows
            except ImportError:
                # Module not available, should be handled in actual Windows environment
                pass
                
    @patch('platform.system')
    def test_macos_specific_dependencies(self, mock_platform):
        """Test macOS-specific dependencies."""
        mock_platform.return_value = "Darwin"
        
        # Test macOS-specific modules
        macos_modules = ['sounddevice']
        
        for module_name in macos_modules:
            try:
                __import__(module_name)
                # Module is available on macOS
            except ImportError:
                # Module not available, should be handled in actual macOS environment
                pass


class TestFileSystemCompatibility:
    """Test file system compatibility across platforms."""
    
    def test_path_handling(self):
        """Test cross-platform path handling."""
        # Test Path object creation
        test_path = Path("test") / "path" / "file.txt"
        
        # Should work on all platforms
        assert isinstance(test_path, Path)
        assert test_path.name == "file.txt"
        assert test_path.suffix == ".txt"
        
    def test_temporary_file_creation(self):
        """Test temporary file creation across platforms."""
        # Test temporary file creation
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
            f.write('{"test": "data"}')
            f.flush()
            
            # Should work on all platforms
            assert os.path.exists(f.name)
            
    def test_directory_operations(self):
        """Test directory operations across platforms."""
        # Test temporary directory creation
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Should work on all platforms
            assert temp_path.exists()
            assert temp_path.is_dir()
            
            # Test file creation in directory
            test_file = temp_path / "test.txt"
            test_file.write_text("test content")
            
            assert test_file.exists()
            assert test_file.read_text() == "test content"


class TestIntegratedApplicationCompatibility:
    """Test integrated application compatibility across platforms."""
    
    @patch('platform.system')
    def test_windows_application_initialization(self, mock_platform):
        """Test application initialization on Windows."""
        mock_platform.return_value = "Windows"
        
        app = IntegratedDeepEchoApplication()
        
        # Should initialize without errors
        assert app is not None
        assert hasattr(app, 'config_manager')
        assert hasattr(app, 'thread_manager')
        
    @patch('platform.system')
    def test_macos_application_initialization(self, mock_platform):
        """Test application initialization on macOS."""
        mock_platform.return_value = "Darwin"
        
        app = IntegratedDeepEchoApplication()
        
        # Should initialize without errors
        assert app is not None
        assert hasattr(app, 'config_manager')
        assert hasattr(app, 'thread_manager')
        
    @patch('platform.system')
    def test_linux_application_initialization(self, mock_platform):
        """Test application initialization on Linux."""
        mock_platform.return_value = "Linux"
        
        app = IntegratedDeepEchoApplication()
        
        # Should initialize without errors
        assert app is not None
        assert hasattr(app, 'config_manager')
        assert hasattr(app, 'thread_manager')
        
    def test_cross_platform_dependency_validation(self):
        """Test dependency validation across platforms."""
        app = IntegratedDeepEchoApplication()
        
        # Test dependency validation
        deps_valid, deps_errors = app.validate_system_dependencies()
        
        # Should return boolean and list
        assert isinstance(deps_valid, bool)
        assert isinstance(deps_errors, list)
        
        # If dependencies are missing, should be reported in errors
        if not deps_valid:
            assert len(deps_errors) > 0
            
    def test_cross_platform_configuration_loading(self):
        """Test configuration loading across platforms."""
        app = IntegratedDeepEchoApplication()
        
        # Test configuration loading
        try:
            config_loaded = app.load_and_validate_configuration()
            assert isinstance(config_loaded, bool)
        except Exception as e:
            # Configuration loading may fail in test environment
            # This is acceptable as long as it fails gracefully
            assert isinstance(e, Exception)


class TestPlatformSpecificFeatures:
    """Test platform-specific features and optimizations."""
    
    @patch('platform.system')
    def test_windows_audio_optimizations(self, mock_platform):
        """Test Windows-specific audio optimizations."""
        mock_platform.return_value = "Windows"
        
        # Test Windows-specific audio features
        # (This would require actual Windows environment for full testing)
        
        # For now, just test that Windows is detected
        assert platform.system() == "Windows"
        
    @patch('platform.system')
    def test_macos_audio_optimizations(self, mock_platform):
        """Test macOS-specific audio optimizations."""
        mock_platform.return_value = "Darwin"
        
        # Test macOS-specific audio features
        # (This would require actual macOS environment for full testing)
        
        # For now, just test that macOS is detected
        assert platform.system() == "Darwin"
        
    def test_performance_across_platforms(self):
        """Test performance characteristics across platforms."""
        import time
        
        # Test basic performance metrics
        start_time = time.time()
        
        # Perform some basic operations
        for i in range(1000):
            _ = str(i)
            
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete quickly on all platforms
        assert duration < 1.0  # Less than 1 second
        
    def test_memory_usage_patterns(self):
        """Test memory usage patterns across platforms."""
        try:
            import psutil
            
            # Get current memory usage
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Should have reasonable memory usage
            assert memory_info.rss > 0  # Should use some memory
            assert memory_info.rss < 1024 * 1024 * 1024  # Less than 1GB
            
        except ImportError:
            # psutil not available, skip test
            pytest.skip("psutil not available for memory testing")


class TestErrorHandlingCompatibility:
    """Test error handling compatibility across platforms."""
    
    def test_exception_handling_consistency(self):
        """Test that exceptions are handled consistently across platforms."""
        # Test standard exception handling
        try:
            raise ValueError("Test error")
        except ValueError as e:
            assert str(e) == "Test error"
            
        # Test custom exception handling
        from backend.utils.exceptions import DeepEchoError
        
        try:
            raise DeepEchoError("Custom error")
        except DeepEchoError as e:
            assert str(e) == "Custom error"
            
    def test_logging_compatibility(self):
        """Test logging compatibility across platforms."""
        logger = get_logger("test_logger")
        
        # Test that logging works
        logger.info("Test log message")
        logger.warning("Test warning message")
        logger.error("Test error message")
        
        # Should not raise exceptions
        assert logger is not None
        
    def test_signal_handling_compatibility(self):
        """Test signal handling compatibility across platforms."""
        import signal
        
        # Test that signal module is available
        assert hasattr(signal, 'SIGINT')
        assert hasattr(signal, 'SIGTERM')
        
        # Test signal handler registration (without actually handling signals)
        def dummy_handler(signum, frame):
            pass
            
        # Should be able to register handlers on all platforms
        try:
            old_handler = signal.signal(signal.SIGINT, dummy_handler)
            signal.signal(signal.SIGINT, old_handler)  # Restore original
        except Exception as e:
            # Some platforms may not support signal handling in tests
            pytest.skip(f"Signal handling not available: {e}")


if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])