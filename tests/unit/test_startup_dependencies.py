"""
Unit tests for startup dependency validation and system initialization.

Tests system requirements validation, dependency checks, and startup
error handling scenarios.
"""

import unittest
import subprocess
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock, call
from pathlib import Path

from src.config.settings import REQUIRED_DEPENDENCIES, ERROR_MESSAGES


class TestDependencyValidation(unittest.TestCase):
    """Test cases for system dependency validation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('subprocess.run')
    def test_ffmpeg_validation_success(self, mock_run):
        """Test successful FFmpeg validation."""
        # Mock successful FFmpeg execution
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        
        self.assertTrue(success)
        self.assertIn("Dependencies validation passed", message)
        mock_run.assert_called_with(
            ["ffmpeg", "-version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=10
        )
    
    @patch('subprocess.run')
    def test_ffmpeg_validation_not_found(self, mock_run):
        """Test FFmpeg validation when FFmpeg is not installed."""
        # Mock FileNotFoundError (FFmpeg not found)
        mock_run.side_effect = FileNotFoundError()
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        
        self.assertFalse(success)
        self.assertEqual(message, ERROR_MESSAGES["ffmpeg_not_found"])
    
    @patch('subprocess.run')
    def test_ffmpeg_validation_timeout(self, mock_run):
        """Test FFmpeg validation timeout."""
        # Mock subprocess timeout
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 10)
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        
        self.assertFalse(success)
        self.assertEqual(message, ERROR_MESSAGES["ffmpeg_not_found"])
    
    @patch('subprocess.run')
    def test_ffmpeg_validation_non_zero_exit(self, mock_run):
        """Test FFmpeg validation with non-zero exit code."""
        # Mock FFmpeg returning non-zero exit code
        mock_process = MagicMock()
        mock_process.returncode = 1
        mock_run.return_value = mock_process
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        
        self.assertFalse(success)
        self.assertEqual(message, ERROR_MESSAGES["ffmpeg_not_found"])
    
    def test_python_version_validation(self):
        """Test Python version validation."""
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        # Current Python version should be >= 3.8
        self.assertGreaterEqual(sys.version_info[:2], (3, 8))
        
        # Test with mocked old Python version
        with patch.object(sys, 'version_info', (3, 7, 0)):
            success, message = app.validate_dependencies()
            self.assertFalse(success)
            self.assertIn("Python 3.8 or higher is required", message)
    
    @patch('builtins.__import__')
    @patch('subprocess.run')
    def test_required_modules_validation(self, mock_run, mock_import):
        """Test validation of required Python modules."""
        # Mock successful FFmpeg check
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Mock missing module
        def import_side_effect(name, *args, **kwargs):
            if name == 'customtkinter':
                raise ImportError(f"No module named '{name}'")
            return MagicMock()
        
        mock_import.side_effect = import_side_effect
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success, message = app.validate_dependencies()
        
        self.assertFalse(success)
        self.assertIn("Required module 'customtkinter' not found", message)


class TestSystemInitialization(unittest.TestCase):
    """Test cases for system initialization logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.main.DeepEchoApplication.validate_dependencies')
    @patch('src.main.DeepEchoApplication.load_configuration')
    @patch('src.main.DeepEchoApplication.initialize_audio_system')
    @patch('src.main.DeepEchoApplication.initialize_transcription')
    @patch('src.main.DeepEchoApplication.initialize_ai_system')
    @patch('src.main.DeepEchoApplication.initialize_ui')
    def test_successful_initialization_sequence(self, mock_ui, mock_ai, mock_transcription, 
                                              mock_audio, mock_config, mock_deps):
        """Test successful system initialization sequence."""
        # Mock all initialization steps as successful
        mock_deps.return_value = (True, "Dependencies OK")
        mock_config.return_value = True
        mock_audio.return_value = True
        mock_transcription.return_value = True
        mock_ai.return_value = True
        mock_ui.return_value = True
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        # Mock main window to avoid GUI
        app.main_window = MagicMock()
        
        with patch.object(app, 'cleanup'):
            result = app.run()
        
        # Should return success (0)
        self.assertEqual(result, 0)
        
        # Verify initialization sequence
        mock_deps.assert_called_once()
        mock_config.assert_called_once()
        mock_audio.assert_called_once()
        mock_transcription.assert_called_once()
        mock_ai.assert_called_once()
        mock_ui.assert_called_once()
    
    @patch('src.main.DeepEchoApplication.validate_dependencies')
    def test_initialization_fails_on_dependency_error(self, mock_deps):
        """Test initialization failure when dependencies are invalid."""
        # Mock dependency validation failure
        mock_deps.return_value = (False, "FFmpeg not found")
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        with patch.object(app, 'cleanup'):
            result = app.run()
        
        # Should return error (1)
        self.assertEqual(result, 1)
    
    @patch('src.main.DeepEchoApplication.validate_dependencies')
    @patch('src.main.DeepEchoApplication.load_configuration')
    def test_initialization_fails_on_config_error(self, mock_config, mock_deps):
        """Test initialization failure when configuration loading fails."""
        # Mock successful dependencies but failed config
        mock_deps.return_value = (True, "Dependencies OK")
        mock_config.return_value = False
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        with patch.object(app, 'cleanup'):
            result = app.run()
        
        # Should return error (1)
        self.assertEqual(result, 1)
    
    @patch('src.main.DeepEchoApplication.validate_dependencies')
    @patch('src.main.DeepEchoApplication.load_configuration')
    @patch('src.main.DeepEchoApplication.initialize_audio_system')
    def test_initialization_fails_on_audio_error(self, mock_audio, mock_config, mock_deps):
        """Test initialization failure when audio system fails."""
        # Mock successful dependencies and config but failed audio
        mock_deps.return_value = (True, "Dependencies OK")
        mock_config.return_value = True
        mock_audio.return_value = False
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        with patch.object(app, 'cleanup'):
            result = app.run()
        
        # Should return error (1)
        self.assertEqual(result, 1)
    
    def test_cleanup_on_exception(self):
        """Test that cleanup is called when an exception occurs."""
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        # Mock an exception during initialization
        with patch.object(app, 'validate_dependencies', side_effect=Exception("Test error")):
            with patch.object(app, 'cleanup') as mock_cleanup:
                result = app.run()
        
        # Should return error and call cleanup
        self.assertEqual(result, 1)
        mock_cleanup.assert_called_once()
    
    def test_signal_handler_cleanup(self):
        """Test that signal handlers trigger cleanup."""
        import signal
        from src.main import DeepEchoApplication
        
        app = DeepEchoApplication()
        
        with patch.object(app, 'cleanup') as mock_cleanup:
            with patch('sys.exit') as mock_exit:
                # Simulate SIGINT
                app._signal_handler(signal.SIGINT, None)
        
        mock_cleanup.assert_called_once()
        mock_exit.assert_called_once_with(0)


class TestAudioSystemInitialization(unittest.TestCase):
    """Test cases for audio system initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.main.LEGACY_AVAILABLE', True)
    @patch('src.main.LegacyAudioRecorder')
    @patch('time.sleep')
    def test_legacy_audio_initialization(self, mock_sleep, mock_audio_recorder):
        """Test legacy audio system initialization."""
        # Mock legacy audio recorders
        mock_mic_recorder = MagicMock()
        mock_speaker_recorder = MagicMock()
        mock_audio_recorder.DefaultMicRecorder.return_value = mock_mic_recorder
        mock_audio_recorder.DefaultSpeakerRecorder.return_value = mock_speaker_recorder
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success = app.initialize_audio_system()
        
        self.assertTrue(success)
        mock_audio_recorder.DefaultMicRecorder.assert_called_once()
        mock_audio_recorder.DefaultSpeakerRecorder.assert_called_once()
        mock_mic_recorder.record_into_queue.assert_called_once()
        mock_speaker_recorder.record_into_queue.assert_called_once()
        mock_sleep.assert_called_once_with(2)
    
    @patch('src.main.LEGACY_AVAILABLE', False)
    def test_audio_initialization_no_legacy(self):
        """Test audio initialization when legacy system is not available."""
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success = app.initialize_audio_system()
        
        self.assertFalse(success)
    
    @patch('src.main.LEGACY_AVAILABLE', True)
    @patch('src.main.LegacyAudioRecorder')
    def test_audio_initialization_exception(self, mock_audio_recorder):
        """Test audio initialization exception handling."""
        # Mock exception during audio recorder creation
        mock_audio_recorder.DefaultMicRecorder.side_effect = Exception("Audio error")
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success = app.initialize_audio_system()
        
        self.assertFalse(success)


class TestTranscriptionInitialization(unittest.TestCase):
    """Test cases for transcription system initialization."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.main.LEGACY_AVAILABLE', True)
    @patch('src.main.TranscriberModels')
    @patch('src.main.LegacyAudioTranscriber')
    @patch('threading.Thread')
    def test_transcription_initialization_success(self, mock_thread, mock_transcriber, mock_models):
        """Test successful transcription initialization."""
        # Mock components
        mock_model = MagicMock()
        mock_models.get_model.return_value = mock_model
        mock_transcriber_instance = MagicMock()
        mock_transcriber.return_value = mock_transcriber_instance
        mock_thread_instance = MagicMock()
        mock_thread.return_value = mock_thread_instance
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        # Mock audio recorders
        app.user_audio_recorder = MagicMock()
        app.speaker_audio_recorder = MagicMock()
        
        success = app.initialize_transcription()
        
        self.assertTrue(success)
        mock_models.get_model.assert_called_once()
        mock_transcriber.assert_called_once()
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    @patch('src.main.LEGACY_AVAILABLE', False)
    def test_transcription_initialization_no_legacy(self):
        """Test transcription initialization when legacy system is not available."""
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success = app.initialize_transcription()
        
        self.assertFalse(success)
    
    @patch('src.main.LEGACY_AVAILABLE', True)
    @patch('src.main.TranscriberModels')
    def test_transcription_initialization_exception(self, mock_models):
        """Test transcription initialization exception handling."""
        # Mock exception during model loading
        mock_models.get_model.side_effect = Exception("Model error")
        
        from src.main import DeepEchoApplication
        app = DeepEchoApplication()
        
        success = app.initialize_transcription()
        
        self.assertFalse(success)


class TestCommandLineArguments(unittest.TestCase):
    """Test cases for command line argument parsing."""
    
    def test_parse_arguments_default(self):
        """Test parsing default arguments."""
        import sys
        original_argv = sys.argv
        
        try:
            sys.argv = ['main.py']
            from src.main import parse_arguments
            args = parse_arguments()
            
            self.assertFalse(args['use_api'])
            self.assertFalse(args['use_new_ui'])
            self.assertFalse(args['use_legacy_ui'])
            self.assertFalse(args['use_legacy'])
            self.assertFalse(args['verbose'])
            self.assertFalse(args['help'])
            
        finally:
            sys.argv = original_argv
    
    def test_parse_arguments_all_flags(self):
        """Test parsing all possible arguments."""
        import sys
        original_argv = sys.argv
        
        try:
            sys.argv = ['main.py', '--api', '--new-ui', '--legacy-ui', '--legacy', '--verbose', '--help']
            from src.main import parse_arguments
            args = parse_arguments()
            
            self.assertTrue(args['use_api'])
            self.assertTrue(args['use_new_ui'])
            self.assertTrue(args['use_legacy_ui'])
            self.assertTrue(args['use_legacy'])
            self.assertTrue(args['verbose'])
            self.assertTrue(args['help'])
            
        finally:
            sys.argv = original_argv
    
    def test_parse_arguments_short_flags(self):
        """Test parsing short flag variants."""
        import sys
        original_argv = sys.argv
        
        try:
            sys.argv = ['main.py', '-v', '-h']
            from src.main import parse_arguments
            args = parse_arguments()
            
            self.assertTrue(args['verbose'])
            self.assertTrue(args['help'])
            
        finally:
            sys.argv = original_argv
    
    def test_main_function_help(self):
        """Test main function with help flag."""
        import sys
        original_argv = sys.argv
        
        try:
            sys.argv = ['main.py', '--help']
            from src.main import main
            
            # Should return 0 for help
            with patch('src.main.show_help') as mock_help:
                result = main()
                self.assertEqual(result, 0)
                mock_help.assert_called_once()
                
        finally:
            sys.argv = original_argv
    
    def test_main_function_verbose(self):
        """Test main function with verbose flag."""
        import sys
        import logging
        original_argv = sys.argv
        
        try:
            sys.argv = ['main.py', '--verbose']
            
            with patch('src.main.DeepEchoApplication') as mock_app_class:
                mock_app = MagicMock()
                mock_app.run.return_value = 0
                mock_app_class.return_value = mock_app
                
                from src.main import main
                result = main()
                
                self.assertEqual(result, 0)
                # Verbose flag should set debug logging level
                self.assertEqual(logging.getLogger().level, logging.DEBUG)
                
        finally:
            sys.argv = original_argv


if __name__ == '__main__':
    unittest.main()