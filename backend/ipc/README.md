# IPC Module - Backend Service Communication

This module provides Inter-Process Communication (IPC) between the Tauri frontend and Python backend service.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Tauri Frontend                           │
│                  (TypeScript/React)                         │
└────────────────────┬────────────────────────────────────────┘
                     │ TCP Socket (localhost:9876)
                     │ JSON Messages
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    IPC Server                               │
│                  (src/ipc/ipc_server.py)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  - Accept connections                                │  │
│  │  - Route messages to MessageHandler                  │  │
│  │  - Forward events from EventEmitter                  │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────┬───────────────────┘
             │                            │
             ▼                            ▼
┌────────────────────────┐   ┌───────────────────────────────┐
│   Message Handler      │   │     Event Emitter             │
│ (message_handler.py)   │   │   (event_emitter.py)          │
│                        │   │                               │
│ - Route commands       │   │ - Emit events to frontend     │
│ - Execute handlers     │   │ - Queue events                │
│ - Return responses     │   │ - Notify listeners            │
└────────────────────────┘   └───────────────────────────────┘
```

## Components

### 1. Backend Service (`src/backend_service.py`)

Main entry point for the backend service.

**Features:**
- Service initialization and lifecycle management
- Signal handling for graceful shutdown
- Command-line argument parsing
- Configuration loading

**Usage:**
```bash
python backend/backend_service.py --host 127.0.0.1 --port 9876 --log-level INFO
```

**Arguments:**
- `--host`: Host address (default: 127.0.0.1)
- `--port`: Port number (default: 9876)
- `--log-level`: Logging level (default: INFO)
- `--config-dir`: Configuration directory (default: ~/.deepecho)

### 2. IPC Server (`ipc_server.py`)

TCP-based server that handles client connections and message routing.

**Features:**
- Multi-client support
- Asynchronous message processing
- Event broadcasting
- Connection management

**Key Methods:**
```python
server = IPCServer(host="127.0.0.1", port=9876)
server.start()  # Start listening for connections
server.stop()   # Stop server and cleanup
server.broadcast_event("event-type", data)  # Broadcast to all clients
```

### 3. Message Handler (`message_handler.py`)

Routes incoming commands to appropriate handler functions.

**Supported Commands:**

#### Audio Commands
- `start_recording` - Start audio recording
- `stop_recording` - Stop audio recording
- `get_transcript` - Get current transcript
- `get_audio_devices` - List available audio devices
- `set_audio_device` - Set active audio device

#### AI Commands
- `generate_response` - Generate AI response
- `switch_provider` - Switch AI provider

#### Config Commands
- `get_config` - Get current configuration
- `update_config` - Update configuration

#### System Commands
- `get_system_info` - Get system information
- `ping` - Health check

**Message Format:**
```json
{
  "id": "request-id",
  "command": "command-name",
  "params": {
    "param1": "value1"
  }
}
```

**Response Format:**
```json
{
  "id": "request-id",
  "status": "success",
  "data": {
    "result": "data"
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### 4. Event Emitter (`event_emitter.py`)

Manages event emission from backend to frontend.

**Supported Events:**
- `transcript-updated` - New transcript data available
- `response-generated` - AI response generated
- `status-changed` - System status changed
- `error-occurred` - Error occurred
- `config-updated` - Configuration updated
- `audio-started` - Audio recording started
- `audio-stopped` - Audio recording stopped

**Usage:**

```python
from backend.ipc.event_emitter import get_event_emitter

emitter = get_event_emitter()
emitter.start()

# Emit events
emitter.emit_transcript_updated({
    "text": "Hello world",
    "source": "microphone"
})

emitter.emit_response_generated({
    "text": "AI response",
    "provider": "openai"
})
```

## Communication Protocol

### Request-Response Pattern

1. Frontend sends command:
```json
{
  "id": "req-123",
  "command": "start_recording",
  "params": {
    "device_type": "microphone"
  }
}
```

2. Backend processes and responds:
```json
{
  "id": "req-123",
  "status": "success",
  "data": {
    "message": "Recording started",
    "device_type": "microphone"
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

### Event Push Pattern

Backend pushes events to frontend:
```json
{
  "type": "transcript-updated",
  "data": {
    "text": "New transcript",
    "source": "microphone",
    "timestamp": "2024-01-01T00:00:00.000Z"
  },
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## Integration with Existing Backend

The IPC module is designed to wrap existing backend functionality:

```python
# In message_handler.py
def _handle_start_recording(self, params):
    # Will integrate with backend/audio/recorder.py
    device_type = params.get("device_type")
    # recorder.start_recording(device_type)
    return {"status": "recording"}
```

Integration points:
- `src/audio/recorder.py` - Audio recording
- `src/audio/transcriber.py` - Audio transcription
- `src/ai/adapter.py` - AI provider management
- `src/config/config_manager.py` - Configuration management

## Error Handling

All errors are caught and returned in a consistent format:

```json
{
  "id": "req-123",
  "status": "error",
  "error": "Error message",
  "timestamp": "2024-01-01T00:00:00.000Z"
}
```

## Testing

Run structure verification:
```bash
python test_ipc_structure.py
```

## Next Steps

Task 17 will implement the actual integration with existing backend components:
- 17.1: Wrap AudioRecorder for IPC access
- 17.2: Wrap AudioTranscriber for IPC access
- 17.3: Wrap AIAdapter for IPC access
- 17.4: Wrap ConfigManager for IPC access

## Security Considerations

- Server binds to localhost only (127.0.0.1)
- No authentication required (local-only communication)
- Input validation in message handlers
- Error messages don't expose sensitive information

## Performance

- Asynchronous message processing
- Event queuing to prevent blocking
- Multi-threaded client handling
- Configurable timeouts and buffer sizes
