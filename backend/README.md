# DeepEcho Backend

Python-based backend service providing AI processing, audio transcription, and core business logic.

## Overview

The backend service maintains the existing DeepEcho functionality while adapting to the new frontend-backend separation architecture. It communicates with the Tauri layer via IPC and provides:

- Audio capture (microphone and speaker)
- Real-time speech transcription
- AI response generation
- Configuration management
- Event emission to frontend

## Technology Stack

- **Python 3.8+**: Core language
- **SpeechRecognition**: Audio transcription
- **PyAudioWPatch**: Windows audio capture
- **PyAudio**: macOS audio capture
- **OpenAI Whisper**: Local transcription model
- **Multiple AI SDKs**: DeepSeek, OpenAI, Claude, etc.

## Project Structure

```
backend/
├── src/
│   ├── audio/              # Audio processing
│   │   ├── recorder.py
│   │   ├── transcriber.py
│   │   └── models.py
│   ├── audio_system/       # Platform-specific audio
│   │   ├── audio_interface.py
│   │   ├── audio_factory.py
│   │   ├── windows_audio.py
│   │   └── macos_audio.py
│   ├── ai/                 # AI providers
│   │   ├── adapter.py
│   │   ├── responder.py
│   │   └── providers/
│   ├── config/             # Configuration
│   │   ├── config_manager.py
│   │   └── settings.py
│   ├── api/                # API layer (new)
│   │   ├── server.py
│   │   ├── handlers.py
│   │   └── models.py
│   ├── ipc/                # IPC communication (new)
│   │   ├── ipc_server.py
│   │   └── message_handler.py
│   ├── utils/              # Utilities
│   │   ├── logger.py
│   │   ├── exceptions.py
│   │   └── event_emitter.py
│   └── backend_service.py  # Service entry point (new)
├── tests/
│   ├── unit/
│   ├── integration/
│   └── property/
├── requirements.txt
├── setup.py
└── README.md
```

## Development Setup

### Prerequisites

- Python 3.8+
- FFmpeg (for audio processing)
- Platform-specific audio libraries:
  - **Windows**: PyAudioWPatch (auto-installed)
  - **macOS**: PortAudio, BlackHole virtual audio device

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Development

```bash
# Run backend service
python src/backend_service.py

# Run tests
pytest tests/

# Run with verbose logging
python src/backend_service.py --verbose
```

## Audio Capture

### Microphone Capture

Uses `speech_recognition.Microphone()` to access the default system microphone.

### Speaker Capture

Platform-specific implementations:

**Windows (WASAPI Loopback)**:
```python
# Uses PyAudioWPatch to capture system audio output
device = audio_factory.get_loopback_device()
```

**macOS (BlackHole)**:
```python
# Uses BlackHole virtual audio device
device = audio_factory.get_blackhole_device()
```

## IPC Communication

The backend service communicates with Tauri via:

### Message Format

```json
{
  "type": "command",
  "id": "unique-request-id",
  "command": "start_recording",
  "params": {
    "device_type": "microphone"
  }
}
```

### Response Format

```json
{
  "type": "response",
  "id": "unique-request-id",
  "status": "success",
  "data": {
    "message": "Recording started"
  }
}
```

### Event Format

```json
{
  "type": "event",
  "event": "transcript-updated",
  "data": {
    "id": "transcript-123",
    "timestamp": 1234567890,
    "source": "microphone",
    "text": "Hello world",
    "confidence": 0.95
  }
}
```

## API Endpoints

The backend exposes the following commands via IPC:

### Audio Commands

- `start_recording(device_type)`: Start audio capture
- `stop_recording()`: Stop audio capture
- `get_audio_devices()`: List available devices
- `set_audio_device(device_type, device_id)`: Select device

### Transcription Commands

- `get_transcript()`: Get current transcript

### AI Commands

- `generate_response(context)`: Generate AI response
- `switch_provider(provider)`: Switch AI provider

### Configuration Commands

- `get_config()`: Get current configuration
- `update_config(config)`: Update configuration

### System Commands

- `get_system_info()`: Get system information

## Event System

The backend emits events to notify the frontend:

- `audio-started`: Audio capture started
- `audio-stopped`: Audio capture stopped
- `transcription-complete`: New transcription available
- `response-ready`: AI response generated
- `error`: Error occurred

## AI Provider Support

Supports multiple AI providers:

- **DeepSeek**: deepseek-chat, deepseek-coder
- **OpenAI**: gpt-3.5-turbo, gpt-4, gpt-4o
- **Claude**: claude-3-haiku, claude-3-sonnet, claude-3-opus
- **Grok**: grok-beta, grok-2
- **Volcano Engine**: doubao-pro, doubao-lite
- **GLM**: qwen-turbo, qwen-plus, qwen-max

## Configuration

Configuration is managed via JSON files:

```json
{
  "audio": {
    "use_api_mode": true,
    "record_timeout": 3,
    "energy_threshold": 1000
  },
  "ai_provider": {
    "provider_type": "deepseek",
    "api_key": "your-key-here",
    "model": "deepseek-chat",
    "response_interval": 5
  }
}
```

## Error Handling

Comprehensive error handling:

- Audio device errors
- Transcription errors
- AI provider errors
- Configuration errors
- Network errors

All errors are logged and emitted as events.

## Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Property-based tests
pytest tests/property/

# All tests
pytest tests/
```

## Performance Optimization

- Multi-threaded audio processing
- Queue-based message handling
- Resource usage monitoring
- Memory leak prevention

## Logging

Structured logging with multiple levels:

- DEBUG: Detailed diagnostic information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical errors

Logs are written to:
- Console (stdout)
- File (`logs/deepecho.log`)
- Transcription log (`logs/transcription.log`)

## Migration from Existing Code

The backend preserves existing functionality:

1. **Audio System**: Reuses existing `src/audio/` and `src/audio_system/`
2. **AI Providers**: Reuses existing `src/ai/` and `src/ai/providers/`
3. **Configuration**: Reuses existing `src/config/`
4. **Utilities**: Reuses existing `src/utils/`

New additions:
- `src/api/`: API layer for IPC communication
- `src/ipc/`: IPC server and message handling
- `src/backend_service.py`: Service entry point

## Contributing

See the main project README for contribution guidelines.

## License

MIT License - see LICENSE file in project root.
