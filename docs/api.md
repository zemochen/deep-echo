# DeepEcho API Documentation

## Overview

This document describes the API interface between the frontend, Tauri middleware, and Python backend.

## Tauri Commands

Tauri commands are invoked from the frontend and handled by the Rust middleware layer.

### Audio Commands

#### start_recording

Start audio recording from specified device.

**Signature:**
```rust
#[tauri::command]
async fn start_recording(device_type: String) -> Result<String, String>
```

**Parameters:**
- `device_type` (String): Type of device - "microphone" or "speaker"

**Returns:**
- Success: `"Recording started"`
- Error: Error message string

**Example:**
```typescript
try {
  const result = await invoke('start_recording', { 
    deviceType: 'microphone' 
  });
  console.log(result); // "Recording started"
} catch (error) {
  console.error('Failed to start recording:', error);
}
```

#### stop_recording

Stop audio recording.

**Signature:**
```rust
#[tauri::command]
async fn stop_recording() -> Result<String, String>
```

**Returns:**
- Success: `"Recording stopped"`
- Error: Error message string

**Example:**
```typescript
const result = await invoke('stop_recording');
```

#### get_audio_devices

Get list of available audio devices.

**Signature:**
```rust
#[tauri::command]
async fn get_audio_devices() -> Result<Vec<AudioDevice>, String>
```

**Returns:**
- Success: Array of `AudioDevice` objects
- Error: Error message string

**AudioDevice Type:**
```typescript
interface AudioDevice {
  id: string;
  name: string;
  type: 'microphone' | 'speaker';
  isDefault: boolean;
}
```

**Example:**
```typescript
const devices = await invoke('get_audio_devices');
console.log(devices);
// [
//   { id: "0", name: "Built-in Microphone", type: "microphone", isDefault: true },
//   { id: "1", name: "External Mic", type: "microphone", isDefault: false }
// ]
```

#### set_audio_device

Set the audio device to use for recording.

**Signature:**
```rust
#[tauri::command]
async fn set_audio_device(device_type: String, device_id: String) -> Result<String, String>
```

**Parameters:**
- `device_type` (String): Type of device - "microphone" or "speaker"
- `device_id` (String): Device ID from `get_audio_devices`

**Returns:**
- Success: `"Device set successfully"`
- Error: Error message string

**Example:**
```typescript
await invoke('set_audio_device', {
  deviceType: 'microphone',
  deviceId: '1'
});
```

### Transcription Commands

#### get_transcript

Get the current transcript.

**Signature:**
```rust
#[tauri::command]
async fn get_transcript() -> Result<TranscriptData, String>
```

**Returns:**
- Success: `TranscriptData` object
- Error: Error message string

**TranscriptData Type:**
```typescript
interface TranscriptData {
  id: string;
  timestamp: number;
  source: 'microphone' | 'speaker';
  text: string;
  confidence: number;
}
```

**Example:**
```typescript
const transcript = await invoke('get_transcript');
console.log(transcript);
// {
//   id: "transcript-123",
//   timestamp: 1234567890,
//   source: "microphone",
//   text: "Hello world",
//   confidence: 0.95
// }
```

### AI Commands

#### generate_response

Generate an AI response based on context.

**Signature:**
```rust
#[tauri::command]
async fn generate_response(context: String) -> Result<String, String>
```

**Parameters:**
- `context` (String): Context for AI response generation

**Returns:**
- Success: Generated response text
- Error: Error message string

**Example:**
```typescript
const response = await invoke('generate_response', {
  context: 'User said: Hello, how are you?'
});
console.log(response); // "I'm doing well, thank you for asking!"
```

#### switch_provider

Switch the AI provider.

**Signature:**
```rust
#[tauri::command]
async fn switch_provider(provider: String) -> Result<String, String>
```

**Parameters:**
- `provider` (String): Provider name - "deepseek", "openai", "claude", "grok", etc.

**Returns:**
- Success: `"Provider switched to {provider}"`
- Error: Error message string

**Example:**
```typescript
await invoke('switch_provider', { provider: 'deepseek' });
```

### Configuration Commands

#### get_config

Get the current configuration.

**Signature:**
```rust
#[tauri::command]
async fn get_config() -> Result<ConfigData, String>
```

**Returns:**
- Success: `ConfigData` object
- Error: Error message string

**ConfigData Type:**
```typescript
interface ConfigData {
  audio: {
    recordTimeout: number;
    energyThreshold: number;
    device?: string;
  };
  ai: {
    provider: string;
    model: string;
    apiKey: string;
  };
  ui: {
    updateInterval: number;
    theme: 'light' | 'dark';
  };
}
```

**Example:**
```typescript
const config = await invoke('get_config');
console.log(config.ai.provider); // "deepseek"
```

#### update_config

Update the configuration.

**Signature:**
```rust
#[tauri::command]
async fn update_config(config: ConfigData) -> Result<String, String>
```

**Parameters:**
- `config` (ConfigData): New configuration object

**Returns:**
- Success: `"Configuration updated"`
- Error: Error message string

**Example:**
```typescript
await invoke('update_config', {
  config: {
    audio: { recordTimeout: 5, energyThreshold: 1000 },
    ai: { provider: 'openai', model: 'gpt-4', apiKey: 'sk-...' },
    ui: { updateInterval: 3, theme: 'dark' }
  }
});
```

### System Commands

#### get_system_info

Get system information.

**Signature:**
```rust
#[tauri::command]
async fn get_system_info() -> Result<SystemInfo, String>
```

**Returns:**
- Success: `SystemInfo` object
- Error: Error message string

**SystemInfo Type:**
```typescript
interface SystemInfo {
  platform: 'windows' | 'macos' | 'linux';
  version: string;
  arch: string;
  memory: {
    total: number;
    available: number;
  };
  cpu: {
    cores: number;
    usage: number;
  };
}
```

**Example:**
```typescript
const info = await invoke('get_system_info');
console.log(info.platform); // "macos"
```

## Tauri Events

Events are emitted from the backend and can be listened to in the frontend.

### transcript-updated

Emitted when a new transcript is available.

**Payload Type:**
```typescript
interface TranscriptData {
  id: string;
  timestamp: number;
  source: 'microphone' | 'speaker';
  text: string;
  confidence: number;
}
```

**Example:**
```typescript
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen('transcript-updated', (event) => {
  const transcript = event.payload as TranscriptData;
  console.log('New transcript:', transcript.text);
});

// Later: unlisten();
```

### response-generated

Emitted when an AI response is generated.

**Payload Type:**
```typescript
interface ResponseData {
  id: string;
  timestamp: number;
  provider: string;
  text: string;
  context: string;
}
```

**Example:**
```typescript
await listen('response-generated', (event) => {
  const response = event.payload as ResponseData;
  console.log('AI response:', response.text);
});
```

### status-changed

Emitted when system status changes.

**Payload Type:**
```typescript
interface SystemStatus {
  state: 'idle' | 'recording' | 'processing' | 'error';
  message: string;
  details?: Record<string, any>;
}
```

**Example:**
```typescript
await listen('status-changed', (event) => {
  const status = event.payload as SystemStatus;
  console.log('Status:', status.state, status.message);
});
```

### error-occurred

Emitted when an error occurs.

**Payload Type:**
```typescript
interface ErrorInfo {
  code: string;
  message: string;
  details?: string;
  timestamp: number;
}
```

**Example:**
```typescript
await listen('error-occurred', (event) => {
  const error = event.payload as ErrorInfo;
  console.error('Error:', error.message);
});
```

### config-updated

Emitted when configuration is updated.

**Payload Type:**
```typescript
interface ConfigData {
  audio: { recordTimeout: number; energyThreshold: number; device?: string };
  ai: { provider: string; model: string; apiKey: string };
  ui: { updateInterval: number; theme: 'light' | 'dark' };
}
```

**Example:**
```typescript
await listen('config-updated', (event) => {
  const config = event.payload as ConfigData;
  console.log('Config updated:', config);
});
```

## Backend IPC Protocol

Communication between Tauri and Python backend uses JSON messages over stdin/stdout.

### Message Format

#### Command Request

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

#### Command Response

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

#### Error Response

```json
{
  "type": "response",
  "id": "unique-request-id",
  "status": "error",
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Audio device not found",
    "details": "Device ID 'invalid' does not exist"
  }
}
```

#### Event Message

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

## Error Codes

### Audio Errors

- `DEVICE_NOT_FOUND`: Audio device not found
- `DEVICE_BUSY`: Audio device is busy
- `RECORDING_FAILED`: Failed to start recording
- `RECORDING_NOT_ACTIVE`: No active recording to stop

### Transcription Errors

- `TRANSCRIPTION_FAILED`: Failed to transcribe audio
- `MODEL_NOT_LOADED`: Transcription model not loaded
- `INVALID_AUDIO`: Invalid audio data

### AI Errors

- `PROVIDER_NOT_CONFIGURED`: AI provider not configured
- `API_KEY_INVALID`: Invalid API key
- `GENERATION_FAILED`: Failed to generate response
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded

### Configuration Errors

- `CONFIG_NOT_FOUND`: Configuration file not found
- `CONFIG_INVALID`: Invalid configuration format
- `CONFIG_WRITE_FAILED`: Failed to write configuration

### System Errors

- `SYSTEM_INFO_FAILED`: Failed to get system information
- `PERMISSION_DENIED`: Permission denied
- `RESOURCE_UNAVAILABLE`: System resource unavailable

## Rate Limiting

Some operations may be rate-limited:

- AI response generation: Depends on provider limits
- Configuration updates: 1 per second
- System info queries: 10 per second

## Best Practices

### Error Handling

Always wrap command invocations in try-catch:

```typescript
try {
  const result = await invoke('start_recording', { deviceType: 'microphone' });
} catch (error) {
  console.error('Command failed:', error);
  // Handle error appropriately
}
```

### Event Cleanup

Always unlisten from events when component unmounts:

```typescript
useEffect(() => {
  const setupListener = async () => {
    const unlisten = await listen('transcript-updated', handleTranscript);
    return unlisten;
  };
  
  const unlistenPromise = setupListener();
  
  return () => {
    unlistenPromise.then(unlisten => unlisten());
  };
}, []);
```

### Type Safety

Use TypeScript types for all API interactions:

```typescript
import { invoke } from '@tauri-apps/api/tauri';
import type { TranscriptData, ConfigData } from './types/api';

const transcript = await invoke<TranscriptData>('get_transcript');
const config = await invoke<ConfigData>('get_config');
```

## Versioning

API version: 1.0.0

Breaking changes will increment the major version.
