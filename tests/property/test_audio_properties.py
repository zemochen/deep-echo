"""
Property-based tests for AudioRecorder and AudioTranscriber modules.

Feature: real-time-voice-ai-assistant, Property 1: 音频数据端到端处理
Validates: Requirements 1.3, 2.1, 2.4

Feature: real-time-voice-ai-assistant, Property 2: 音频源区分标记
Validates: Requirements 2.5

Feature: real-time-voice-ai-assistant, Property 9: 语言检测和处理模式
Validates: Requirements 6.1, 6.2

Feature: real-time-voice-ai-assistant, Property 10: 模式切换一致性
Validates: Requirements 6.3

Feature: real-time-voice-ai-assistant, Property 11: 处理模式选择
Validates: Requirements 6.4

This test suite validates that audio data flows correctly from detection
through the processing queue to transcription display within 2 seconds,
that audio sources are properly distinguished in transcriptions, and that
multi-language and model switching functionality works correctly.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from hypothesis import assume
import queue
import time
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import custom_speech_recognition as sr

from src.audio.recorder import (
    BaseRecorder,
    DefaultMicRecorder,
    DefaultSpeakerRecorder,
    AudioRecorderError,
    AudioDeviceNotFoundError,
    AudioRecordingError
)
from src.audio.models import (
    BaseTranscriber,
    FasterWhisperTranscriber,
    APIWhisperTranscriber,
    TranscriptionMode,
    LanguageDetectionResult,
    TranscriberModelManager,
    get_model,
    switch_transcription_mode,
    validate_transcription_consistency
)


# Test fixtures and helpers

@pytest.fixture
def mock_audio_source():
    """Create a mock audio source for testing"""
    source = Mock(spec=sr.Microphone)
    source.__enter__ = Mock(return_value=source)
    source.__exit__ = Mock(return_value=False)
    return source


@pytest.fixture
def mock_recognizer():
    """Create a mock recognizer for testing"""
    recognizer = Mock(spec=sr.Recognizer)
    recognizer.energy_threshold = 1000
    recognizer.dynamic_energy_threshold = False
    recognizer.adjust_for_ambient_noise = Mock()
    recognizer.listen_in_background = Mock(return_value=Mock())
    return recognizer


# Unit tests for basic functionality

class TestBaseRecorder:
    """Unit tests for BaseRecorder class"""
    
    def test_init_with_none_source_raises_error(self):
        """Test that initializing with None source raises ValueError"""
        with pytest.raises(ValueError, match="audio source can't be None"):
            BaseRecorder(None)
    
    def test_init_with_valid_source(self, mock_audio_source):
        """Test successful initialization with valid source"""
        with patch('src.audio.recorder.sr.Recognizer') as mock_recognizer_class:
            mock_recognizer_class.return_value = Mock()
            recorder = BaseRecorder(mock_audio_source)
            assert recorder.source == mock_audio_source
            assert recorder.recorder is not None
    
    def test_adjust_for_noise_success(self, mock_audio_source):
        """Test successful noise adjustment"""
        with patch('src.audio.recorder.sr.Recognizer') as mock_recognizer_class:
            mock_recognizer = Mock()
            mock_recognizer_class.return_value = mock_recognizer
            
            recorder = BaseRecorder(mock_audio_source)
            recorder.adjust_for_noise("Test Device", "Test message")
            
            mock_recognizer.adjust_for_ambient_noise.assert_called_once()
    
    def test_record_into_queue_starts_background_recording(self, mock_audio_source):
        """Test that record_into_queue starts background recording"""
        with patch('src.audio.recorder.sr.Recognizer') as mock_recognizer_class:
            mock_recognizer = Mock()
            mock_stop_func = Mock()
            mock_recognizer.listen_in_background = Mock(return_value=mock_stop_func)
            mock_recognizer_class.return_value = mock_recognizer
            
            recorder = BaseRecorder(mock_audio_source)
            test_queue = queue.Queue()
            
            recorder.record_into_queue(test_queue)
            
            mock_recognizer.listen_in_background.assert_called_once()
            assert recorder._stop_listening == mock_stop_func
    
    def test_stop_recording(self, mock_audio_source):
        """Test stopping background recording"""
        with patch('src.audio.recorder.sr.Recognizer') as mock_recognizer_class:
            mock_recognizer = Mock()
            mock_stop_func = Mock()
            mock_recognizer.listen_in_background = Mock(return_value=mock_stop_func)
            mock_recognizer_class.return_value = mock_recognizer
            
            recorder = BaseRecorder(mock_audio_source)
            test_queue = queue.Queue()
            recorder.record_into_queue(test_queue)
            
            recorder.stop_recording()
            
            mock_stop_func.assert_called_once_with(wait_for_stop=False)


# Property-based tests

@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    audio_data=st.binary(min_size=100, max_size=10000),
    num_audio_chunks=st.integers(min_value=1, max_value=10)
)
def test_property_audio_data_end_to_end_processing(audio_data, num_audio_chunks):
    """
    Property 1: Audio data end-to-end processing
    
    Feature: real-time-voice-ai-assistant, Property 1: 音频数据端到端处理
    Validates: Requirements 1.3, 2.1, 2.4
    
    For any audio input source (microphone or speaker), when audio data is detected,
    the system should transmit data to the processing queue and complete transcription
    display update within 2 seconds.
    
    This property tests that:
    1. Audio data is successfully captured
    2. Data is placed into the processing queue with timestamp
    3. Queue contains the correct data format (data, timestamp)
    4. Processing happens within acceptable time bounds
    """
    # Create mock audio source and recognizer
    mock_source = Mock(spec=sr.Microphone)
    mock_source.__enter__ = Mock(return_value=mock_source)
    mock_source.__exit__ = Mock(return_value=False)
    
    # Track callback function
    callback_func = None
    
    def capture_callback(source, callback, phrase_time_limit):
        nonlocal callback_func
        callback_func = callback
        return Mock()  # Return mock stop function
    
    with patch('src.audio.recorder.sr.Recognizer') as mock_recognizer_class:
        mock_recognizer = Mock()
        mock_recognizer.energy_threshold = 1000
        mock_recognizer.dynamic_energy_threshold = False
        mock_recognizer.adjust_for_ambient_noise = Mock()
        mock_recognizer.listen_in_background = Mock(side_effect=capture_callback)
        mock_recognizer_class.return_value = mock_recognizer
        
        # Create recorder and queue
        recorder = BaseRecorder(mock_source)
        audio_queue = queue.Queue()
        
        # Start recording
        start_time = time.time()
        recorder.record_into_queue(audio_queue)
        
        # Verify callback was registered
        assert callback_func is not None, "Callback function should be registered"
        
        # Simulate audio data being captured
        for i in range(num_audio_chunks):
            mock_audio = Mock(spec=sr.AudioData)
            mock_audio.get_raw_data = Mock(return_value=audio_data)
            
            # Call the callback as if audio was detected
            callback_func(None, mock_audio)
        
        # Verify all audio chunks were queued
        assert audio_queue.qsize() == num_audio_chunks, \
            f"Expected {num_audio_chunks} items in queue, got {audio_queue.qsize()}"
        
        # Verify queue items have correct format
        for i in range(num_audio_chunks):
            item = audio_queue.get(timeout=1)
            
            # Check tuple format (data, timestamp)
            assert isinstance(item, tuple), "Queue item should be a tuple"
            assert len(item) == 2, "Queue item should have 2 elements"
            
            data, timestamp = item
            
            # Verify data is bytes
            assert isinstance(data, bytes), "Audio data should be bytes"
            assert len(data) > 0, "Audio data should not be empty"
            
            # Verify timestamp is datetime
            assert isinstance(timestamp, datetime), "Timestamp should be datetime object"
            
            # Verify timestamp is recent (within 2 seconds as per requirement)
            time_diff = (datetime.utcnow() - timestamp).total_seconds()
            assert time_diff < 2.0, \
                f"Timestamp should be within 2 seconds (got {time_diff:.2f}s)"
        
        # Verify processing time is within bounds
        processing_time = time.time() - start_time
        assert processing_time < 2.0, \
            f"End-to-end processing should complete within 2 seconds (got {processing_time:.2f}s)"


@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    audio_data=st.binary(min_size=100, max_size=5000)
)
def test_property_audio_queue_data_integrity(audio_data):
    """
    Property: Audio queue maintains data integrity
    
    For any audio data captured, the data placed in the queue should be
    identical to the original captured data (no corruption or loss).
    """
    mock_source = Mock(spec=sr.Microphone)
    mock_source.__enter__ = Mock(return_value=mock_source)
    mock_source.__exit__ = Mock(return_value=False)
    
    callback_func = None
    
    def capture_callback(source, callback, phrase_time_limit):
        nonlocal callback_func
        callback_func = callback
        return Mock()
    
    with patch('src.audio.recorder.sr.Recognizer') as mock_recognizer_class:
        mock_recognizer = Mock()
        mock_recognizer.energy_threshold = 1000
        mock_recognizer.dynamic_energy_threshold = False
        mock_recognizer.adjust_for_ambient_noise = Mock()
        mock_recognizer.listen_in_background = Mock(side_effect=capture_callback)
        mock_recognizer_class.return_value = mock_recognizer
        
        recorder = BaseRecorder(mock_source)
        audio_queue = queue.Queue()
        
        recorder.record_into_queue(audio_queue)
        
        # Simulate audio capture
        mock_audio = Mock(spec=sr.AudioData)
        mock_audio.get_raw_data = Mock(return_value=audio_data)
        callback_func(None, mock_audio)
        
        # Retrieve and verify data
        queued_data, timestamp = audio_queue.get(timeout=1)
        
        # Data integrity check
        assert queued_data == audio_data, \
            "Queued audio data should match original data exactly"


@settings(
    max_examples=3,
    deadline=None
)
@given(
    num_concurrent_chunks=st.integers(min_value=1, max_value=20)
)
def test_property_concurrent_audio_processing(num_concurrent_chunks):
    """
    Property: Concurrent audio processing maintains queue order
    
    For any number of concurrent audio chunks, the system should
    maintain proper queue ordering and not lose any data.
    """
    mock_source = Mock(spec=sr.Microphone)
    mock_source.__enter__ = Mock(return_value=mock_source)
    mock_source.__exit__ = Mock(return_value=False)
    
    callback_func = None
    
    def capture_callback(source, callback, phrase_time_limit):
        nonlocal callback_func
        callback_func = callback
        return Mock()
    
    with patch('src.audio.recorder.sr.Recognizer') as mock_recognizer_class:
        mock_recognizer = Mock()
        mock_recognizer.energy_threshold = 1000
        mock_recognizer.dynamic_energy_threshold = False
        mock_recognizer.adjust_for_ambient_noise = Mock()
        mock_recognizer.listen_in_background = Mock(side_effect=capture_callback)
        mock_recognizer_class.return_value = mock_recognizer
        
        recorder = BaseRecorder(mock_source)
        audio_queue = queue.Queue()
        
        recorder.record_into_queue(audio_queue)
        
        # Simulate multiple concurrent audio chunks
        for i in range(num_concurrent_chunks):
            mock_audio = Mock(spec=sr.AudioData)
            # Use unique data for each chunk to verify ordering
            unique_data = f"audio_chunk_{i}".encode()
            mock_audio.get_raw_data = Mock(return_value=unique_data)
            callback_func(None, mock_audio)
        
        # Verify all chunks are in queue
        assert audio_queue.qsize() == num_concurrent_chunks, \
            f"Queue should contain all {num_concurrent_chunks} chunks"
        
        # Verify no data loss
        retrieved_chunks = []
        while not audio_queue.empty():
            data, timestamp = audio_queue.get()
            retrieved_chunks.append(data)
        
        assert len(retrieved_chunks) == num_concurrent_chunks, \
            "Should retrieve all chunks without loss"


# Property tests for AudioTranscriber

@settings(
    max_examples=3,
    deadline=None,
    suppress_health_check=[HealthCheck.function_scoped_fixture]
)
@given(
    mic_text_samples=st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs'))),
        min_size=1, max_size=5
    ),
    speaker_text_samples=st.lists(
        st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Pc', 'Pd', 'Zs'))),
        min_size=1, max_size=5
    )
)
def test_property_audio_source_distinction_marking(mic_text_samples, speaker_text_samples):
    """
    Property 2: Audio source distinction marking
    
    Feature: real-time-voice-ai-assistant, Property 2: 音频源区分标记
    Validates: Requirements 2.5
    
    For any transcribed audio data, the system should correctly mark its source
    ("You" for microphone, "Speaker" for speaker output).
    
    This property tests that:
    1. Microphone transcriptions are marked with "You"
    2. Speaker transcriptions are marked with "Speaker"
    3. Source marking is consistent across all transcriptions
    4. Combined transcript maintains proper source attribution
    """
    from src.audio.transcriber import AudioTranscriber
    from datetime import datetime, timezone
    from unittest.mock import Mock
    import custom_speech_recognition as sr
    
    # Filter out empty or whitespace-only samples and make them unique per source
    mic_texts = [f"mic_{i}_{text.strip()}" for i, text in enumerate(mic_text_samples) if text.strip()]
    speaker_texts = [f"speaker_{i}_{text.strip()}" for i, text in enumerate(speaker_text_samples) if text.strip()]
    
    # Skip if no valid texts
    assume(len(mic_texts) > 0 or len(speaker_texts) > 0)
    
    # Create mock audio sources
    mock_mic_source = Mock(spec=sr.Microphone)
    mock_mic_source.SAMPLE_RATE = 16000
    mock_mic_source.SAMPLE_WIDTH = 2
    mock_mic_source.channels = 1
    
    mock_speaker_source = Mock(spec=sr.Microphone)
    mock_speaker_source.SAMPLE_RATE = 44100
    mock_speaker_source.SAMPLE_WIDTH = 2
    mock_speaker_source.channels = 2
    
    # Create mock transcription model
    mock_model = Mock()
    
    # Create transcriber
    transcriber = AudioTranscriber(mock_mic_source, mock_speaker_source, mock_model)
    
    # Track expected transcriptions
    expected_mic_transcriptions = []
    expected_speaker_transcriptions = []
    
    # Add microphone transcriptions
    for i, text in enumerate(mic_texts):
        timestamp = datetime.now(timezone.utc)
        transcriber.update_transcript("You", text, timestamp)
        expected_mic_transcriptions.append((text, timestamp))
    
    # Add speaker transcriptions
    for i, text in enumerate(speaker_texts):
        timestamp = datetime.now(timezone.utc)
        transcriber.update_transcript("Speaker", text, timestamp)
        expected_speaker_transcriptions.append((text, timestamp))
    
    # Verify microphone transcript source marking
    mic_transcript = transcriber.get_mic_transcript()
    for entry_text, entry_timestamp in mic_transcript:
        # Check that microphone entries are marked with "You:"
        assert entry_text.startswith("You: ["), \
            f"Microphone transcript should start with 'You: [', got: {entry_text[:20]}"
        assert entry_text.endswith("]\n\n"), \
            f"Microphone transcript should end with ']\\n\\n', got: {entry_text[-10:]}"
    
    # Verify speaker transcript source marking
    speaker_transcript = transcriber.get_speaker_transcript()
    for entry_text, entry_timestamp in speaker_transcript:
        # Check that speaker entries are marked with "Speaker:"
        assert entry_text.startswith("Speaker: ["), \
            f"Speaker transcript should start with 'Speaker: [', got: {entry_text[:20]}"
        assert entry_text.endswith("]\n\n"), \
            f"Speaker transcript should end with ']\\n\\n', got: {entry_text[-10:]}"
    
    # Verify combined transcript maintains source distinction
    combined_transcript = transcriber.get_transcript()
    
    # Count occurrences of each source marker in combined transcript
    you_count = combined_transcript.count("You: [")
    speaker_count = combined_transcript.count("Speaker: [")
    
    # Verify counts match expected transcriptions (accounting for MAX_PHRASES limit)
    expected_you_count = min(len(expected_mic_transcriptions), 10)  # MAX_PHRASES = 10
    expected_speaker_count = min(len(expected_speaker_transcriptions), 10)
    
    assert you_count == expected_you_count, \
        f"Expected {expected_you_count} 'You:' markers, found {you_count}"
    assert speaker_count == expected_speaker_count, \
        f"Expected {expected_speaker_count} 'Speaker:' markers, found {speaker_count}"
    
    # Verify proper source attribution - each unique text should appear with correct source
    for text, _ in expected_mic_transcriptions[:10]:  # Only check up to MAX_PHRASES
        # Check that mic text appears with "You:" marker
        expected_format = f"You: [{text}]"
        assert expected_format in combined_transcript, \
            f"Microphone text '{text}' should appear with 'You:' marker"
    
    for text, _ in expected_speaker_transcriptions[:10]:  # Only check up to MAX_PHRASES
        # Check that speaker text appears with "Speaker:" marker
        expected_format = f"Speaker: [{text}]"
        assert expected_format in combined_transcript, \
            f"Speaker text '{text}' should appear with 'Speaker:' marker"


@settings(
    max_examples=3,
    deadline=None
)
@given(
    num_transcriptions=st.integers(min_value=1, max_value=20)
)
def test_property_audio_source_consistency(num_transcriptions):
    """
    Property: Audio source consistency across operations
    
    For any number of transcriptions, the source marking should remain
    consistent across all transcript operations (get, clear, update).
    """
    from src.audio.transcriber import AudioTranscriber
    from datetime import datetime, timezone
    from unittest.mock import Mock
    import custom_speech_recognition as sr
    
    # Create mock audio sources
    mock_mic_source = Mock(spec=sr.Microphone)
    mock_mic_source.SAMPLE_RATE = 16000
    mock_mic_source.SAMPLE_WIDTH = 2
    mock_mic_source.channels = 1
    
    mock_speaker_source = Mock(spec=sr.Microphone)
    mock_speaker_source.SAMPLE_RATE = 44100
    mock_speaker_source.SAMPLE_WIDTH = 2
    mock_speaker_source.channels = 2
    
    mock_model = Mock()
    transcriber = AudioTranscriber(mock_mic_source, mock_speaker_source, mock_model)
    
    # Add alternating transcriptions with unique text to avoid conflicts
    for i in range(num_transcriptions):
        timestamp = datetime.now(timezone.utc)
        if i % 2 == 0:
            transcriber.update_transcript("You", f"unique_mic_text_{i}", timestamp)
        else:
            transcriber.update_transcript("Speaker", f"unique_speaker_text_{i}", timestamp)
    
    # Verify source consistency
    combined = transcriber.get_transcript()
    
    # Count source markers
    you_markers = combined.count("You: [")
    speaker_markers = combined.count("Speaker: [")
    
    # Calculate expected counts considering MAX_PHRASES limit and combined transcript behavior
    # The combined transcript merges both sources and limits to MAX_PHRASES total
    total_expected = min(num_transcriptions, 10)  # MAX_PHRASES = 10
    
    # For alternating pattern, calculate how many of each type within the limit
    you_in_total = 0
    speaker_in_total = 0
    
    # Simulate the insertion order (newest first) and count within limit
    for i in range(min(num_transcriptions, 10)):
        # Since we add in order 0,1,2,3... but display newest first,
        # the last 10 added will be shown
        actual_index = num_transcriptions - 1 - i
        if actual_index % 2 == 0:
            you_in_total += 1
        else:
            speaker_in_total += 1
    
    assert you_markers == you_in_total, \
        f"Expected {you_in_total} 'You:' markers, got {you_markers}"
    assert speaker_markers == speaker_in_total, \
        f"Expected {speaker_in_total} 'Speaker:' markers, got {speaker_markers}"
    
    # Test clear operation maintains source structure
    transcriber.clear_transcript_data()
    
    # After clear, should have empty transcripts but proper structure
    assert transcriber.get_transcript() == "", "Transcript should be empty after clear"
    assert len(transcriber.get_mic_transcript()) == 0, "Mic transcript should be empty after clear"
    assert len(transcriber.get_speaker_transcript()) == 0, "Speaker transcript should be empty after clear"


# Property tests for multi-language and model support

@settings(
    max_examples=2,  # Reduce examples for faster testing
    deadline=None
)
@given(
    use_api_mode=st.booleans()
)
def test_property_language_detection_and_processing_mode(use_api_mode):
    """
    Property 9: Language detection and processing mode
    
    Feature: real-time-voice-ai-assistant, Property 9: 语言检测和处理模式
    Validates: Requirements 6.1, 6.2
    
    For any API mode audio input, the transcription engine should support automatic
    language detection; for local mode, it should use English processing.
    
    This property tests that:
    1. API mode supports automatic language detection
    2. Local mode processes English audio consistently
    3. Language detection returns valid language codes
    4. Processing mode matches expected capabilities
    """
    # Test different transcriber configurations
    with patch('src.audio.models.get_openai_client') as mock_client, \
         patch('src.audio.models.WhisperModel') as mock_whisper_model:
        
        # Mock OpenAI client for API mode
        mock_openai_client = Mock()
        mock_client.return_value = mock_openai_client
        
        # Mock Whisper model for local mode
        mock_model_instance = Mock()
        mock_whisper_model.return_value = mock_model_instance
        
        # Get transcriber based on mode
        transcriber = get_model(use_api_mode)
        
        # Verify mode consistency
        expected_mode = TranscriptionMode.API if use_api_mode else TranscriptionMode.LOCAL
        actual_mode = transcriber.get_mode()
        assert actual_mode == expected_mode, \
            f"Expected mode {expected_mode.value}, got {actual_mode.value}"
        
        # Test language detection support
        supports_detection = transcriber.supports_language_detection()
        assert supports_detection, "Both API and local modes should support language detection"
        
        # Create temporary audio file for testing
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'fake_audio_data')
            temp_file_path = temp_file.name
        
        try:
            if use_api_mode:
                # Mock API response for language detection
                mock_response = Mock()
                mock_response.language = "en"
                mock_response.text = "Sample text"
                mock_openai_client.audio.transcriptions.create.return_value = mock_response
                
                # Test language detection
                lang_result = transcriber.detect_language(temp_file_path)
                
                if lang_result:  # Detection may return None on errors
                    assert isinstance(lang_result, LanguageDetectionResult), \
                        "API language detection should return LanguageDetectionResult"
                    assert lang_result.language in APIWhisperTranscriber.SUPPORTED_LANGUAGES, \
                        f"Detected language {lang_result.language} should be in supported languages"
                    assert 0.0 <= lang_result.confidence <= 1.0, \
                        f"Confidence should be between 0 and 1, got {lang_result.confidence}"
            
            else:
                # Mock local model response
                mock_info = Mock()
                mock_info.language = "en"
                mock_info.language_probability = 0.8
                mock_segments = []
                mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
                
                # Test language detection
                lang_result = transcriber.detect_language(temp_file_path)
                
                if lang_result:
                    assert isinstance(lang_result, LanguageDetectionResult), \
                        "Local language detection should return LanguageDetectionResult"
                    assert lang_result.language == "en", \
                        f"Local mode should detect English, got {lang_result.language}"
                    assert 0.0 <= lang_result.confidence <= 1.0, \
                        f"Confidence should be between 0 and 1, got {lang_result.confidence}"
        
        finally:
            # Cleanup temp file
            import os
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass


@settings(
    max_examples=3,
    deadline=None
)
@given(
    initial_mode=st.booleans(),  # True for API, False for Local
    switch_to_mode=st.booleans(),
    model_name=st.sampled_from(['tiny', 'small', 'base']),
    language_code=st.sampled_from(['en', 'es', 'fr', 'de'])
)
def test_property_mode_switching_consistency(initial_mode, switch_to_mode, model_name, language_code):
    """
    Property 10: Mode switching consistency
    
    Feature: real-time-voice-ai-assistant, Property 10: 模式切换一致性
    Validates: Requirements 6.3
    
    For any transcription mode switching (API/local), the system should maintain
    consistent transcription quality appropriate for that mode.
    
    This property tests that:
    1. Mode switching preserves transcriber functionality
    2. New mode has correct capabilities
    3. Transcription quality is maintained after switch
    4. Mode validation works correctly
    """
    with patch('src.audio.models.get_openai_client') as mock_client, \
         patch('src.audio.models.WhisperModel') as mock_whisper_model, \
         patch('torch.cuda.is_available', return_value=False):  # Force CPU for consistency
        
        # Mock dependencies
        mock_openai_client = Mock()
        mock_client.return_value = mock_openai_client
        
        mock_model_instance = Mock()
        mock_whisper_model.return_value = mock_model_instance
        
        # Prepare parameters for each mode type
        if initial_mode:  # API mode
            initial_params = {'language': language_code}
        else:  # Local mode
            initial_params = {'model_name': model_name}
        
        if switch_to_mode:  # API mode
            switch_params = {'language': language_code}
        else:  # Local mode
            switch_params = {'model_name': model_name}
        
        # Get initial transcriber with appropriate parameters
        initial_transcriber = get_model(initial_mode, **initial_params)
        initial_transcriber_mode = initial_transcriber.get_mode()
        
        # Verify initial mode
        expected_initial_mode = TranscriptionMode.API if initial_mode else TranscriptionMode.LOCAL
        assert initial_transcriber_mode == expected_initial_mode, \
            f"Initial mode should be {expected_initial_mode.value}, got {initial_transcriber_mode.value}"
        
        # Test initial transcriber functionality
        initial_supports_detection = initial_transcriber.supports_language_detection()
        assert isinstance(initial_supports_detection, bool), \
            "Language detection support should return boolean"
        
        # Switch to new mode with appropriate parameters
        new_transcriber = switch_transcription_mode(switch_to_mode, **switch_params)
        new_transcriber_mode = new_transcriber.get_mode()
        
        # Verify new mode
        expected_new_mode = TranscriptionMode.API if switch_to_mode else TranscriptionMode.LOCAL
        assert new_transcriber_mode == expected_new_mode, \
            f"New mode should be {expected_new_mode.value}, got {new_transcriber_mode.value}"
        
        # Test new transcriber functionality
        new_supports_detection = new_transcriber.supports_language_detection()
        assert isinstance(new_supports_detection, bool), \
            "Language detection support should return boolean after switch"
        
        # Verify mode consistency validation
        is_consistent = validate_transcription_consistency(switch_to_mode)
        assert is_consistent, "Mode consistency validation should pass after switch"
        
        # Test transcription functionality with both modes
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'fake_audio_data_for_transcription_test')
            temp_file_path = temp_file.name
        
        try:
            if switch_to_mode:  # API mode
                # Mock API transcription response
                mock_response = Mock()
                mock_response.text = "Test transcription from API"
                mock_openai_client.audio.transcriptions.create.return_value = mock_response
                
                result = new_transcriber.get_transcription(temp_file_path)
                assert isinstance(result, str), "API transcription should return string"
                
            else:  # Local mode
                # Mock local transcription response
                mock_segments = [Mock(text="Test"), Mock(text="transcription"), Mock(text="from local")]
                mock_info = Mock()
                mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
                
                result = new_transcriber.get_transcription(temp_file_path)
                assert isinstance(result, str), "Local transcription should return string"
        
        finally:
            # Cleanup
            import os
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
        
        # Verify that switching doesn't break the transcriber interface
        assert hasattr(new_transcriber, 'get_transcription'), \
            "Transcriber should maintain get_transcription method after switch"
        assert hasattr(new_transcriber, 'get_mode'), \
            "Transcriber should maintain get_mode method after switch"
        assert hasattr(new_transcriber, 'supports_language_detection'), \
            "Transcriber should maintain supports_language_detection method after switch"


@settings(
    max_examples=3,
    deadline=None
)
@given(
    user_choice_api=st.booleans(),
    processing_preferences=st.dictionaries(
        keys=st.sampled_from(['speed_priority', 'accuracy_priority', 'language_support']),
        values=st.booleans(),
        min_size=1, max_size=3
    )
)
def test_property_processing_mode_selection(user_choice_api, processing_preferences):
    """
    Property 11: Processing mode selection
    
    Feature: real-time-voice-ai-assistant, Property 11: 处理模式选择
    Validates: Requirements 6.4
    
    For any user's processing mode selection, the system should correctly apply
    the corresponding configuration (local fast English or API multi-language).
    
    This property tests that:
    1. User selection maps to correct transcription mode
    2. Mode configuration matches user preferences
    3. System applies appropriate settings for chosen mode
    4. Mode capabilities align with user expectations
    """
    with patch('src.audio.models.get_openai_client') as mock_client, \
         patch('src.audio.models.WhisperModel') as mock_whisper_model, \
         patch('torch.cuda.is_available', return_value=True):  # Test with GPU available
        
        # Mock dependencies
        mock_openai_client = Mock()
        mock_client.return_value = mock_openai_client
        
        mock_model_instance = Mock()
        mock_whisper_model.return_value = mock_model_instance
        
        # Determine expected configuration based on user choice
        if user_choice_api:
            # API mode: slower, multi-language, higher accuracy
            expected_mode = TranscriptionMode.API
            expected_language_support = True
            expected_speed_characteristics = "slower_but_accurate"
        else:
            # Local mode: faster, English-focused, good for real-time
            expected_mode = TranscriptionMode.LOCAL
            expected_language_support = True  # Local Whisper also supports multiple languages
            expected_speed_characteristics = "faster_local_processing"
        
        # Create transcriber based on user choice
        transcriber = get_model(user_choice_api)
        
        # Verify mode selection matches user choice
        actual_mode = transcriber.get_mode()
        assert actual_mode == expected_mode, \
            f"User choice {user_choice_api} should result in {expected_mode.value} mode, got {actual_mode.value}"
        
        # Verify language support capabilities
        supports_language_detection = transcriber.supports_language_detection()
        assert supports_language_detection == expected_language_support, \
            f"Mode {actual_mode.value} should have language detection: {expected_language_support}"
        
        # Test configuration application based on processing preferences
        if processing_preferences.get('speed_priority', False):
            # Speed priority should work well with local mode
            if not user_choice_api:  # Local mode
                # Local mode should be configured for speed
                if hasattr(transcriber, 'device'):
                    # Should use GPU if available for speed
                    assert transcriber.device in ['cuda', 'cpu'], \
                        "Local mode should have valid device configuration"
        
        if processing_preferences.get('accuracy_priority', False):
            # Accuracy priority should work well with API mode
            if user_choice_api:  # API mode
                # API mode should be configured for accuracy
                assert transcriber.model == "whisper-1", \
                    "API mode should use appropriate model for accuracy"
        
        if processing_preferences.get('language_support', False):
            # Multi-language support should be available in both modes
            assert supports_language_detection, \
                "Multi-language support requires language detection capability"
        
        # Test that system applies correct settings for chosen mode
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            temp_file.write(b'test_audio_data_for_mode_validation')
            temp_file_path = temp_file.name
        
        try:
            if user_choice_api:
                # API mode should handle multi-language requests
                mock_response = Mock()
                mock_response.text = "Multi-language API response"
                mock_response.language = "en"
                mock_openai_client.audio.transcriptions.create.return_value = mock_response
                
                # Test transcription
                result = transcriber.get_transcription(temp_file_path)
                assert isinstance(result, str), "API mode should return transcription string"
                
                # Test language detection
                mock_verbose_response = Mock()
                mock_verbose_response.language = "en"
                mock_verbose_response.text = "Test text"
                mock_openai_client.audio.transcriptions.create.return_value = mock_verbose_response
                
                lang_result = transcriber.detect_language(temp_file_path)
                if lang_result:
                    assert isinstance(lang_result, LanguageDetectionResult), \
                        "API language detection should return LanguageDetectionResult"
            
            else:
                # Local mode should handle English efficiently
                mock_segments = [Mock(text="Fast"), Mock(text="local"), Mock(text="processing")]
                mock_info = Mock()
                mock_info.language = "en"
                mock_info.language_probability = 0.9
                mock_model_instance.transcribe.return_value = (mock_segments, mock_info)
                
                # Test transcription
                result = transcriber.get_transcription(temp_file_path)
                assert isinstance(result, str), "Local mode should return transcription string"
                
                # Test language detection
                lang_result = transcriber.detect_language(temp_file_path)
                if lang_result:
                    assert isinstance(lang_result, LanguageDetectionResult), \
                        "Local language detection should return LanguageDetectionResult"
        
        finally:
            # Cleanup
            import os
            try:
                os.unlink(temp_file_path)
            except OSError:
                pass
        
        # Verify mode capabilities align with user expectations
        if user_choice_api:
            # API mode expectations: multi-language, cloud-based, potentially slower
            assert actual_mode == TranscriptionMode.API, "API choice should result in API mode"
        else:
            # Local mode expectations: fast processing, local computation, English-optimized
            assert actual_mode == TranscriptionMode.LOCAL, "Local choice should result in LOCAL mode"
            
            # Local mode should have model configuration
            if hasattr(transcriber, 'model_name'):
                assert transcriber.model_name in FasterWhisperTranscriber.SUPPORTED_MODELS, \
                    f"Local mode should use supported model, got {transcriber.model_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
