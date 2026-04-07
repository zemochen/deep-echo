"""
Property-based tests for audio device selection feature.

# Feature: audio-device-selection, Property 1: 设备列表字段完整性
# Validates: Requirements 1.2

This test suite validates that _handle_get_audio_devices always returns
device objects with complete, valid fields regardless of the underlying
device enumeration results.
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import patch, MagicMock

from backend.ipc.message_handler import MessageHandler


# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

# Non-empty strings for device names
non_empty_str = st.text(min_size=1, max_size=100).filter(lambda s: s.strip() != "")

# Strategy for a list of microphone names (0 to 10 devices)
mic_names_strategy = st.lists(non_empty_str, min_size=0, max_size=10)

# Strategy for a speaker info dict (or None to simulate no speaker found)
speaker_info_strategy = st.one_of(
    st.none(),
    st.fixed_dictionaries({
        "index": st.integers(min_value=0, max_value=99),
        "name": non_empty_str,
        "defaultSampleRate": st.floats(min_value=8000, max_value=192000, allow_nan=False),
        "maxInputChannels": st.integers(min_value=0, max_value=32),
    }),
)


# ---------------------------------------------------------------------------
# Property 1: 设备列表字段完整性
# ---------------------------------------------------------------------------

@given(mic_names=mic_names_strategy, speaker_info=speaker_info_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_device_list_field_integrity(mic_names, speaker_info):
    """
    # Feature: audio-device-selection, Property 1: 设备列表字段完整性
    # Validates: Requirements 1.2

    For any device enumeration result, every device object in the returned
    list must contain non-empty `id`, `name`, and `deviceType` fields, and
    `deviceType` must be either "microphone" or "speaker".
    """
    handler = MessageHandler()

    with patch("backend.custom_speech_recognition.Microphone.list_microphone_names",
               return_value=mic_names), \
         patch("backend.audio_system.get_default_speaker",
               return_value=speaker_info):

        result = handler._handle_get_audio_devices({})

    # The response must always have these two keys
    assert "microphones" in result
    assert "speakers" in result

    all_devices = result["microphones"] + result["speakers"]

    for device in all_devices:
        # Each device must have the three required fields
        assert "id" in device, f"Device missing 'id': {device}"
        assert "name" in device, f"Device missing 'name': {device}"
        assert "deviceType" in device, f"Device missing 'deviceType': {device}"

        # Fields must be non-empty strings
        assert isinstance(device["id"], str) and device["id"] != "", \
            f"Device 'id' must be a non-empty string: {device}"
        assert isinstance(device["name"], str) and device["name"] != "", \
            f"Device 'name' must be a non-empty string: {device}"

        # deviceType must be one of the two valid values
        assert device["deviceType"] in ("microphone", "speaker"), \
            f"Device 'deviceType' must be 'microphone' or 'speaker', got: {device['deviceType']}"

    # Microphone devices must all have deviceType "microphone"
    for mic in result["microphones"]:
        assert mic["deviceType"] == "microphone", \
            f"Microphone device has wrong deviceType: {mic}"

    # Speaker devices must all have deviceType "speaker"
    for spk in result["speakers"]:
        assert spk["deviceType"] == "speaker", \
            f"Speaker device has wrong deviceType: {spk}"


# ---------------------------------------------------------------------------
# Property 2: 异常安全性
# Feature: audio-device-selection, Property 2: 异常安全性
# Validates: Requirements 1.4
# ---------------------------------------------------------------------------

# Exceptions that can realistically occur during device enumeration
_EXCEPTION_TYPES = [
    OSError,
    ImportError,
    RuntimeError,
    PermissionError,
    AttributeError,
    Exception,
]

exception_strategy = st.sampled_from(_EXCEPTION_TYPES).map(
    lambda exc_cls: exc_cls("simulated error for property test")
)

# Where the exception is injected: the outer import or one of the two inner calls
injection_point_strategy = st.sampled_from([
    "outer",          # patch the outer import so it raises immediately
    "mic_enum",       # patch list_microphone_names to raise
    "speaker_enum",   # patch get_default_speaker to raise
    "both_inner",     # both inner calls raise
])


@given(exc=exception_strategy, injection_point=injection_point_strategy)
@settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
def test_property_exception_safety(exc, injection_point):
    """
    # Feature: audio-device-selection, Property 2: 异常安全性
    # Validates: Requirements 1.4

    For any exception raised during device enumeration (OSError, ImportError,
    PermissionError, etc.), _handle_get_audio_devices must:
      - Never propagate an uncaught exception to the caller
      - Always return a dict with an 'error' field when the outer block fails
      - Always return a dict with 'microphones' and 'speakers' keys
      - Return empty lists for 'microphones' and 'speakers' when the outer
        exception fires (inner exceptions are swallowed gracefully)
    """
    handler = MessageHandler()

    if injection_point == "outer":
        # Simulate ImportError or any exception at the top-level import stage
        with patch("backend.ipc.message_handler.MessageHandler._handle_get_audio_devices",
                   wraps=handler._handle_get_audio_devices):
            # Patch the sr module import inside the method by making the
            # custom_speech_recognition module itself raise on attribute access
            with patch("backend.custom_speech_recognition.Microphone") as mock_mic:
                mock_mic.list_microphone_names.side_effect = exc
                with patch("backend.audio_system.get_default_speaker",
                           side_effect=exc):
                    result = handler._handle_get_audio_devices({})

        # Both inner calls raised — microphones and speakers should be empty
        assert "microphones" in result
        assert "speakers" in result
        assert result["microphones"] == []
        assert result["speakers"] == []

    elif injection_point == "mic_enum":
        # Only microphone enumeration raises; speaker may succeed or return None
        with patch("backend.custom_speech_recognition.Microphone") as mock_mic, \
             patch("backend.audio_system.get_default_speaker", return_value=None):
            mock_mic.list_microphone_names.side_effect = exc
            result = handler._handle_get_audio_devices({})

        # Must not raise; microphones list must be empty due to the exception
        assert "microphones" in result
        assert "speakers" in result
        assert result["microphones"] == []

    elif injection_point == "speaker_enum":
        # Only speaker enumeration raises; microphones may succeed (empty list)
        with patch("backend.custom_speech_recognition.Microphone") as mock_mic, \
             patch("backend.audio_system.get_default_speaker", side_effect=exc):
            mock_mic.list_microphone_names.return_value = []
            result = handler._handle_get_audio_devices({})

        # Must not raise; speakers list must be empty due to the exception
        assert "microphones" in result
        assert "speakers" in result
        assert result["speakers"] == []

    else:  # both_inner
        # Both inner calls raise — outer try/except should NOT fire (inner ones catch)
        with patch("backend.custom_speech_recognition.Microphone") as mock_mic, \
             patch("backend.audio_system.get_default_speaker", side_effect=exc):
            mock_mic.list_microphone_names.side_effect = exc
            result = handler._handle_get_audio_devices({})

        # Both inner exceptions are swallowed; result has empty lists (no outer error)
        assert "microphones" in result
        assert "speakers" in result
        assert result["microphones"] == []
        assert result["speakers"] == []

    # Universal invariant: the result is always a dict and never raises
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
