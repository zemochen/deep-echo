# Communication Protocol Specification

## Overview

This document defines the complete communication protocol between the frontend (TypeScript/React), Tauri middleware (Rust), and Python backend.

## Architecture Layers

```
┌─────────────────────────────────────┐
│   Frontend (TypeScript/React)      │
│   - UI Components                   │
│   - State Management                │
│   - Event Listeners                 │
└──────────────┬──────────────────────┘
               │ Tauri API (invoke/listen)
               │
┌──────────────▼──────────────────────┐
│   Tauri Middleware (Rust)           │
│   - Command Handlers                │
│   - Event Emitters                  │
│   - IPC Manager                     │
└──────────────┬──────────────────────┘
               │ IPC (stdin/stdout JSON)
               │
┌──────────────▼──────────────────────┐
│   Python Backend                    │
│   - Audio Processing                │
│   - Transcription                   │
│   - AI Response Generation          │
└─────────────────────────────────────┘
```

## Layer 1: Frontend ↔ Tauri Communication

### Command Invocation

Frontend invokes Tauri commands using the `@tauri-apps/api` package:

```typescript
import { invoke } from '@tauri-apps/api/tauri';

// Generic command invocation
const result = await invoke<ReturnType>('command_name', {
  param1: value1,
  param2: value2
});
```

### Event Listening

Frontend listens to events emitted by Tauri:

```typescript
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen<PayloadType>('event-name', (event) => {
  const payload = event.payload;
  // Handle event
});

// Cleanup
unlisten();
```

## Layer 2: Tauri ↔ Python Communication

### Message Format

All messages between Tauri and Python use JSON format over stdin/stdout.

#### Command Request (Tauri → Python)

```json
{
  "type": "command",
  "id": "unique-request-id",
  "command": "command_name",
  "params": {
    "param1": "value1",
    "param2": "value2"
  }
}
```

**Fields:**
- `type`: Always "command" for requests
- `id`: Unique identifier for request-response matching
- `command`: Name of the command to execute
- `params`: Command parameters as key-value pairs

#### Command Response (Python → Tauri)

**Success Response:**
```json
{
  "type": "response",
  "id": "unique-request-id",
  "status": "success",
  "data": {
    "result": "value"
  }
}
```

**Error Response:**
```json
{
  "type": "response",
  "id": "unique-request-id",
  "status": "error",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional error details"
  }
}
```

**Fields:**
- `type`: Always "response" for responses
- `id`: Matches the request ID
- `status`: "success" or "error"
- `data`: Response data (success only)
- `error`: Error information (error only)

#### Event Message (Python → Tauri)

```json
{
  "type": "event",
  "event": "event-name",
  "data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

**Fields:**
- `type`: Always "event" for events
- `event`: Name of the event
- `data`: Event payload

## Command Specifications

### Audio Commands

#### start_recording

Start audio recording from specified device.

**Frontend Invocation:**
```typescript
await invoke('start_recording', { 
  deviceType: 'microphone' // or 'speaker'
});
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-001",
  "command": "start_recording",
  "params": {
    "device_type": "microphone"
  }
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-001",
  "status": "success",
  "data": {
    "message": "Recording started"
  }
}
```

#### stop_recording

Stop audio recording.

**Frontend Invocation:**
```typescript
await invoke('stop_recording');
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-002",
  "command": "stop_recording",
  "params": {}
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-002",
  "status": "success",
  "data": {
    "message": "Recording stopped"
  }
}
```

#### get_audio_devices

Get list of available audio devices.

**Frontend Invocation:**
```typescript
const devices = await invoke<AudioDevice[]>('get_audio_devices');
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-003",
  "command": "get_audio_devices",
  "params": {}
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-003",
  "status": "success",
  "data": {
    "devices": [
      {
        "id": "0",
        "name": "Built-in Microphone",
        "device_type": "microphone"
      },
      {
        "id": "1",
        "name": "BlackHole 2ch",
        "device_type": "speaker"
      }
    ]
  }
}
```

#### set_audio_device

Set the audio device to use.

**Frontend Invocation:**
```typescript
await invoke('set_audio_device', {
  deviceType: 'microphone',
  deviceId: '1'
});
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-004",
  "command": "set_audio_device",
  "params": {
    "device_type": "microphone",
    "device_id": "1"
  }
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-004",
  "status": "success",
  "data": {
    "message": "Device set successfully"
  }
}
```

### Transcription Commands

#### get_transcript

Get the current transcript.

**Frontend Invocation:**
```typescript
const transcript = await invoke<TranscriptData>('get_transcript');
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-005",
  "command": "get_transcript",
  "params": {}
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-005",
  "status": "success",
  "data": {
    "id": "transcript-123",
    "timestamp": 1234567890,
    "source": "microphone",
    "text": "Hello world",
    "confidence": 0.95
  }
}
```

### AI Commands

#### generate_response

Generate an AI response.

**Frontend Invocation:**
```typescript
const response = await invoke<string>('generate_response', {
  context: 'User said: Hello'
});
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-006",
  "command": "generate_response",
  "params": {
    "context": "User said: Hello"
  }
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-006",
  "status": "success",
  "data": {
    "response": "Hello! How can I help you today?"
  }
}
```

#### switch_provider

Switch AI provider.

**Frontend Invocation:**
```typescript
await invoke('switch_provider', { provider: 'deepseek' });
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-007",
  "command": "switch_provider",
  "params": {
    "provider": "deepseek"
  }
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-007",
  "status": "success",
  "data": {
    "message": "Provider switched to deepseek"
  }
}
```

### Configuration Commands

#### get_config

Get current configuration.

**Frontend Invocation:**
```typescript
const config = await invoke<ConfigData>('get_config');
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-008",
  "command": "get_config",
  "params": {}
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-008",
  "status": "success",
  "data": {
    "audio": {
      "record_timeout": 5,
      "energy_threshold": 1000,
      "device": null
    },
    "ai": {
      "provider": "deepseek",
      "model": "deepseek-chat",
      "api_key": "sk-..."
    },
    "ui": {
      "update_interval": 3,
      "theme": "dark"
    }
  }
}
```

#### update_config

Update configuration.

**Frontend Invocation:**
```typescript
await invoke('update_config', { config: newConfig });
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-009",
  "command": "update_config",
  "params": {
    "config": {
      "audio": {
        "record_timeout": 5,
        "energy_threshold": 1000
      },
      "ai": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key": "sk-..."
      },
      "ui": {
        "update_interval": 3,
        "theme": "light"
      }
    }
  }
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-009",
  "status": "success",
  "data": {
    "message": "Configuration updated"
  }
}
```

### System Commands

#### get_system_info

Get system information.

**Frontend Invocation:**
```typescript
const info = await invoke<SystemInfo>('get_system_info');
```

**Tauri → Python:**
```json
{
  "type": "command",
  "id": "req-010",
  "command": "get_system_info",
  "params": {}
}
```

**Python → Tauri:**
```json
{
  "type": "response",
  "id": "req-010",
  "status": "success",
  "data": {
    "platform": "macos",
    "version": "14.0",
    "arch": "arm64"
  }
}
```

## Event Specifications

### transcript-updated

Emitted when new transcript is available.

**Python → Tauri:**
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

**Tauri → Frontend:**
```typescript
await listen<TranscriptData>('transcript-updated', (event) => {
  const transcript = event.payload;
  // Update UI
});
```

### response-generated

Emitted when AI response is generated.

**Python → Tauri:**
```json
{
  "type": "event",
  "event": "response-generated",
  "data": {
    "id": "response-456",
    "timestamp": 1234567890,
    "provider": "deepseek",
    "text": "Hello! How can I help you?",
    "context": "User said: Hello"
  }
}
```

**Tauri → Frontend:**
```typescript
await listen<ResponseData>('response-generated', (event) => {
  const response = event.payload;
  // Update UI
});
```

### status-changed

Emitted when system status changes.

**Python → Tauri:**
```json
{
  "type": "event",
  "event": "status-changed",
  "data": {
    "state": "recording",
    "message": "Recording audio from microphone",
    "details": {
      "device": "Built-in Microphone"
    }
  }
}
```

**Tauri → Frontend:**
```typescript
await listen<SystemStatus>('status-changed', (event) => {
  const status = event.payload;
  // Update UI
});
```

### error-occurred

Emitted when an error occurs.

**Python → Tauri:**
```json
{
  "type": "event",
  "event": "error-occurred",
  "data": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Audio device not found",
    "details": "Device ID 'invalid' does not exist"
  }
}
```

**Tauri → Frontend:**
```typescript
await listen<ErrorInfo>('error-occurred', (event) => {
  const error = event.payload;
  // Show error notification
});
```

### config-updated

Emitted when configuration is updated.

**Python → Tauri:**
```json
{
  "type": "event",
  "event": "config-updated",
  "data": {
    "audio": {
      "record_timeout": 5,
      "energy_threshold": 1000
    },
    "ai": {
      "provider": "openai",
      "model": "gpt-4",
      "api_key": "sk-..."
    },
    "ui": {
      "update_interval": 3,
      "theme": "light"
    }
  }
}
```

**Tauri → Frontend:**
```typescript
await listen<ConfigData>('config-updated', (event) => {
  const config = event.payload;
  // Update UI
});
```

## Error Codes

### Audio Errors

| Code | Description |
|------|-------------|
| `DEVICE_NOT_FOUND` | Audio device not found |
| `DEVICE_BUSY` | Audio device is busy |
| `RECORDING_FAILED` | Failed to start recording |
| `RECORDING_NOT_ACTIVE` | No active recording to stop |
| `DEVICE_PERMISSION_DENIED` | Permission denied to access device |

### Transcription Errors

| Code | Description |
|------|-------------|
| `TRANSCRIPTION_FAILED` | Failed to transcribe audio |
| `MODEL_NOT_LOADED` | Transcription model not loaded |
| `INVALID_AUDIO` | Invalid audio data |
| `MODEL_LOAD_FAILED` | Failed to load transcription model |

### AI Errors

| Code | Description |
|------|-------------|
| `PROVIDER_NOT_CONFIGURED` | AI provider not configured |
| `API_KEY_INVALID` | Invalid API key |
| `GENERATION_FAILED` | Failed to generate response |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded |
| `PROVIDER_NOT_FOUND` | AI provider not found |
| `MODEL_NOT_SUPPORTED` | Model not supported by provider |

### Configuration Errors

| Code | Description |
|------|-------------|
| `CONFIG_NOT_FOUND` | Configuration file not found |
| `CONFIG_INVALID` | Invalid configuration format |
| `CONFIG_WRITE_FAILED` | Failed to write configuration |
| `CONFIG_VALIDATION_FAILED` | Configuration validation failed |

### System Errors

| Code | Description |
|------|-------------|
| `SYSTEM_INFO_FAILED` | Failed to get system information |
| `PERMISSION_DENIED` | Permission denied |
| `RESOURCE_UNAVAILABLE` | System resource unavailable |
| `INTERNAL_ERROR` | Internal system error |

## Data Type Mappings

### Rust ↔ TypeScript

| Rust Type | TypeScript Type | Notes |
|-----------|----------------|-------|
| `String` | `string` | UTF-8 encoded |
| `u32`, `u64` | `number` | JavaScript number |
| `f32`, `f64` | `number` | JavaScript number |
| `bool` | `boolean` | |
| `Option<T>` | `T \| undefined` | Optional field |
| `Vec<T>` | `T[]` | Array |
| `HashMap<K, V>` | `Record<K, V>` | Object |
| `serde_json::Value` | `any` | Dynamic JSON |

### Rust ↔ Python

| Rust Type | Python Type | JSON Type |
|-----------|-------------|-----------|
| `String` | `str` | `string` |
| `u32`, `u64` | `int` | `number` |
| `f32`, `f64` | `float` | `number` |
| `bool` | `bool` | `boolean` |
| `Option<T>` | `T \| None` | `null` or value |
| `Vec<T>` | `list[T]` | `array` |
| `HashMap<K, V>` | `dict[K, V]` | `object` |

## Protocol Versioning

Current protocol version: **1.0.0**

Version format: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes to protocol
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

## Best Practices

### Frontend

1. **Type Safety**: Always use TypeScript types for API calls
2. **Error Handling**: Wrap all `invoke` calls in try-catch
3. **Event Cleanup**: Always unlisten from events on unmount
4. **Loading States**: Show loading indicators during async operations

### Tauri Middleware

1. **Async Operations**: Use async/await for all I/O operations
2. **Error Propagation**: Convert all errors to user-friendly messages
3. **Timeout Handling**: Implement timeouts for long-running operations
4. **Resource Cleanup**: Clean up resources on shutdown

### Python Backend

1. **JSON Validation**: Validate all incoming JSON messages
2. **Error Reporting**: Include detailed error information
3. **Event Throttling**: Throttle high-frequency events
4. **Graceful Shutdown**: Handle shutdown signals properly

## Security Considerations

1. **Input Validation**: Validate all inputs at each layer
2. **API Key Protection**: Never expose API keys in frontend
3. **File Access**: Restrict file access to allowed directories
4. **Command Injection**: Sanitize all command parameters
5. **Rate Limiting**: Implement rate limiting for expensive operations

## Performance Guidelines

1. **Batch Operations**: Batch multiple operations when possible
2. **Event Throttling**: Throttle high-frequency events (e.g., audio visualization)
3. **Lazy Loading**: Load resources on demand
4. **Caching**: Cache frequently accessed data
5. **Async Processing**: Use async operations to avoid blocking

## Testing

### Unit Tests

- Test each command handler independently
- Test event emission and listening
- Test error handling paths

### Integration Tests

- Test complete command flow (Frontend → Tauri → Python)
- Test event flow (Python → Tauri → Frontend)
- Test error propagation across layers

### Property Tests

- Test protocol consistency across all layers
- Test data serialization/deserialization
- Test error handling completeness
