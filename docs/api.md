# DeepEcho API Documentation

## Overview

This document provides comprehensive API documentation for the DeepEcho system, covering:
- **Tauri Commands**: Frontend-to-backend command interface
- **Event System**: Backend-to-frontend event notifications
- **Data Models**: Type definitions for all API data structures
- **IPC Protocol**: Low-level communication protocol between Tauri and Python backend
- **Error Handling**: Error codes and best practices

**API Version**: 1.0.0

## Table of Contents

1. [Tauri Commands](#tauri-commands)
   - [Audio Commands](#audio-commands)
   - [Transcription Commands](#transcription-commands)
   - [AI Commands](#ai-commands)
   - [Configuration Commands](#configuration-commands)
   - [System Commands](#system-commands)
   - [File Commands](#file-commands)
   - [Python Service Commands](#python-service-commands)
2. [Event System](#event-system)
3. [Data Models](#data-models)
4. [IPC Protocol](#ipc-protocol)
5. [Error Codes](#error-codes)
6. [Best Practices](#best-practices)

---

## Tauri Commands

Tauri commands are invoked from the frontend using the `@tauri-apps/api/tauri` invoke function. All commands are asynchronous and return Promises.

### Audio Commands

Commands for managing audio recording from microphone and speaker devices.

#### `start_recording`

Start audio recording from the specified device type.

**Rust Signature:**
```rust
#[tauri::command]
async fn start_recording(device_type: String, state: State<'_, AudioState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function start_recording(deviceType: string): Promise<string>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deviceType` | `string` | Yes | Type of device: `"microphone"` or `"speaker"` |

**Returns:**
- **Success**: `"Recording started from {device_type}"`
- **Error**: Error message string

**Errors:**
- `"Invalid device type"` - Device type must be "microphone" or "speaker"
- `"Recording is already in progress"` - Cannot start recording while already recording

**Example:**
```typescript
import { invoke } from '@tauri-apps/api/tauri';

try {
  const result = await invoke('start_recording', { 
    deviceType: 'microphone' 
  });
  console.log(result); // "Recording started from microphone"
} catch (error) {
  console.error('Failed to start recording:', error);
}
```

**Validates Requirements:** 5.1, 5.2, 5.3

---

#### `stop_recording`

Stop the currently active audio recording.

**Rust Signature:**
```rust
#[tauri::command]
async fn stop_recording(state: State<'_, AudioState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function stop_recording(): Promise<string>
```

**Parameters:** None

**Returns:**
- **Success**: `"Recording stopped"`
- **Error**: Error message string

**Errors:**
- `"No recording in progress"` - Cannot stop recording when not recording

**Example:**
```typescript
try {
  const result = await invoke('stop_recording');
  console.log(result); // "Recording stopped"
} catch (error) {
  console.error('Failed to stop recording:', error);
}
```

**Validates Requirements:** 5.1, 5.2

---

#### `get_audio_devices`

Retrieve a list of all available audio input and output devices.

**Rust Signature:**
```rust
#[tauri::command]
async fn get_audio_devices() -> Result<Vec<AudioDevice>, String>
```

**TypeScript Signature:**
```typescript
function get_audio_devices(): Promise<AudioDevice[]>
```

**Parameters:** None

**Returns:**
- **Success**: Array of `AudioDevice` objects
- **Error**: Error message string

**AudioDevice Type:**
```typescript
interface AudioDevice {
  id: string;           // Unique device identifier
  name: string;         // Human-readable device name
  deviceType: string;   // "microphone" or "speaker"
}
```

**Platform-Specific Devices:**
- **Windows**: Includes WASAPI loopback device for speaker capture
- **macOS**: Includes BlackHole virtual audio device for speaker capture
- **All Platforms**: Includes default microphone device

**Example:**
```typescript
const devices = await invoke<AudioDevice[]>('get_audio_devices');
console.log(devices);
// [
//   { id: "default-mic", name: "Default Microphone", deviceType: "microphone" },
//   { id: "wasapi-loopback", name: "WASAPI Loopback (Speakers)", deviceType: "speaker" }
// ]
```

**Validates Requirements:** 5.6, 6.3

---

#### `set_audio_device`

Set the audio device to use for recording.

**Rust Signature:**
```rust
#[tauri::command]
async fn set_audio_device(device_type: String, device_id: String) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function set_audio_device(deviceType: string, deviceId: string): Promise<string>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `deviceType` | `string` | Yes | Type of device: `"microphone"` or `"speaker"` |
| `deviceId` | `string` | Yes | Device ID from `get_audio_devices` |

**Returns:**
- **Success**: `"Set {device_type} device to: {device_id}"`
- **Error**: Error message string

**Errors:**
- `"Invalid device type"` - Device type must be "microphone" or "speaker"
- `"Device ID cannot be empty"` - Device ID is required

**Example:**
```typescript
await invoke('set_audio_device', {
  deviceType: 'microphone',
  deviceId: 'default-mic'
});
```

**Validates Requirements:** 5.6

### Transcription Commands

Commands for retrieving transcription results from audio processing.

#### `get_transcript`

Retrieve the latest transcript from audio transcription.

**Rust Signature:**
```rust
#[tauri::command]
async fn get_transcript(state: State<'_, TranscriptionState>) -> Result<TranscriptData, String>
```

**TypeScript Signature:**
```typescript
function get_transcript(): Promise<TranscriptData>
```

**Parameters:** None

**Returns:**
- **Success**: `TranscriptData` object containing the latest transcript
- **Error**: Error message string

**TranscriptData Type:**
```typescript
interface TranscriptData {
  id: string;           // Unique transcript identifier
  timestamp: number;    // Unix timestamp (seconds since epoch)
  source: string;       // "microphone" or "speaker"
  text: string;         // Transcribed text content
  confidence: number;   // Confidence score (0.0 to 1.0)
}
```

**Example:**
```typescript
const transcript = await invoke<TranscriptData>('get_transcript');
console.log(transcript);
// {
//   id: "transcript-123",
//   timestamp: 1705449600,
//   source: "microphone",
//   text: "Hello world",
//   confidence: 0.95
// }
```

**Notes:**
- Returns the most recent transcript from the transcription queue
- If no transcripts are available, returns a mock transcript with confidence 0.0
- Transcripts are generated continuously during active recording

**Validates Requirements:** 4.1, 7.1

---

### AI Commands

Commands for AI response generation and provider management.

#### `generate_response`

Generate an AI response based on the provided context.

**Rust Signature:**
```rust
#[tauri::command]
async fn generate_response(context: String, state: State<'_, AIState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function generate_response(context: string): Promise<string>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `context` | `string` | Yes | Context string for AI response generation |

**Returns:**
- **Success**: Generated response text as string
- **Error**: Error message string

**Errors:**
- `"Context cannot be empty"` - Context parameter is required and cannot be empty

**Example:**
```typescript
const response = await invoke<string>('generate_response', {
  context: 'User said: Hello, how are you?'
});
console.log(response); 
// "I'm doing well, thank you for asking! How can I help you today?"
```

**Notes:**
- Response generation time varies by provider and model
- Context should include relevant conversation history
- Maximum context length depends on the AI provider's limits

**Validates Requirements:** 4.1, 4.3, 7.2

---

#### `switch_provider`

Switch the active AI provider for response generation.

**Rust Signature:**
```rust
#[tauri::command]
async fn switch_provider(provider: String, state: State<'_, AIState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function switch_provider(provider: string): Promise<string>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `provider` | `string` | Yes | AI provider name |

**Valid Providers:**
- `"openai"` - OpenAI (GPT models)
- `"claude"` - Anthropic Claude
- `"deepseek"` - DeepSeek
- `"grok"` - xAI Grok
- `"glm"` - Zhipu GLM
- `"volcano"` - Volcano Engine

**Returns:**
- **Success**: `"Switched to provider: {provider}"`
- **Error**: Error message string

**Errors:**
- `"Invalid provider"` - Provider name not in valid providers list

**Example:**
```typescript
try {
  await invoke('switch_provider', { provider: 'deepseek' });
  console.log('Provider switched successfully');
} catch (error) {
  console.error('Failed to switch provider:', error);
}
```

**Notes:**
- Provider must be configured with valid API keys before switching
- Switching providers does not affect ongoing response generation
- Provider configuration is persisted in the configuration file

**Validates Requirements:** 4.3, 9.1, 9.2

---

### Configuration Commands

Commands for managing application configuration.

#### `get_config`

Retrieve the current application configuration.

**Rust Signature:**
```rust
#[tauri::command]
async fn get_config(state: State<'_, ConfigState>) -> Result<ConfigData, String>
```

**TypeScript Signature:**
```typescript
function get_config(): Promise<ConfigData>
```

**Parameters:** None

**Returns:**
- **Success**: `ConfigData` object with current configuration
- **Error**: Error message string

**ConfigData Type:**
```typescript
interface ConfigData {
  audio: AudioConfig;
  ai: AIConfig;
  ui: UIConfig;
}

interface AudioConfig {
  recordTimeout: number;      // Recording timeout in seconds
  energyThreshold: number;    // Audio energy threshold for voice detection
  device?: string;            // Optional device ID
}

interface AIConfig {
  provider: string;           // Current AI provider name
  model: string;              // Model name/identifier
  apiKey: string;             // API key (may be masked)
}

interface UIConfig {
  updateInterval: number;     // UI update interval in milliseconds
  theme: 'light' | 'dark';    // UI theme
}
```

**Example:**
```typescript
const config = await invoke<ConfigData>('get_config');
console.log(config);
// {
//   audio: { recordTimeout: 5, energyThreshold: 300, device: "default-mic" },
//   ai: { provider: "deepseek", model: "deepseek-chat", apiKey: "sk-***" },
//   ui: { updateInterval: 1000, theme: "dark" }
// }
```

**Validates Requirements:** 9.1, 9.2

---

#### `update_config`

Update the application configuration.

**Rust Signature:**
```rust
#[tauri::command]
async fn update_config(config: ConfigData, state: State<'_, ConfigState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function update_config(config: ConfigData): Promise<string>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `config` | `ConfigData` | Yes | New configuration data |

**Returns:**
- **Success**: `"Configuration updated successfully"`
- **Error**: Error message string

**Validation Rules:**
- `audio.recordTimeout` must be > 0
- `audio.energyThreshold` must be > 0
- `ai.provider` cannot be empty
- `ai.model` cannot be empty
- `ui.updateInterval` must be > 0
- `ui.theme` must be "light" or "dark"

**Errors:**
- `"Audio record timeout must be greater than 0"`
- `"Audio energy threshold must be greater than 0"`
- `"AI provider cannot be empty"`
- `"AI model cannot be empty"`
- `"UI update interval must be greater than 0"`
- `"UI theme must be 'light' or 'dark'"`

**Example:**
```typescript
await invoke('update_config', {
  config: {
    audio: { recordTimeout: 10, energyThreshold: 500 },
    ai: { provider: 'openai', model: 'gpt-4', apiKey: 'sk-...' },
    ui: { updateInterval: 2000, theme: 'dark' }
  }
});
```

**Notes:**
- Configuration is validated before being applied
- Invalid configuration will not be saved
- Configuration changes trigger a `config-updated` event

**Validates Requirements:** 9.1, 9.2, 9.3, 9.5

---

### System Commands

Commands for retrieving system information and managing system resources.

#### `get_system_info`

Retrieve information about the host system.

**Rust Signature:**
```rust
#[tauri::command]
async fn get_system_info() -> Result<SystemInfo, String>
```

**TypeScript Signature:**
```typescript
function get_system_info(): Promise<SystemInfo>
```

**Parameters:** None

**Returns:**
- **Success**: `SystemInfo` object
- **Error**: Error message string

**SystemInfo Type:**
```typescript
interface SystemInfo {
  platform: string;    // Operating system: "windows", "macos", "linux"
  version: string;     // Application version
  arch: string;        // System architecture: "x86_64", "aarch64", etc.
}
```

**Example:**
```typescript
const info = await invoke<SystemInfo>('get_system_info');
console.log(info);
// {
//   platform: "macos",
//   version: "1.0.0",
//   arch: "aarch64"
// }
```

**Validates Requirements:** 6.4, 10.1, 10.2

---

### File Commands

Commands for secure file system operations. All file operations are restricted to allowed directories for security.

#### `read_file`

Read the contents of a file as a string.

**Rust Signature:**
```rust
#[tauri::command]
async fn read_file(path: String, state: State<'_, FileServiceState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function read_file(path: string): Promise<string>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | File path to read |

**Returns:**
- **Success**: File contents as string
- **Error**: Error message string

**Errors:**
- `"Path not allowed"` - Path is outside allowed directories
- `"File not found"` - File does not exist
- `"Permission denied"` - Insufficient permissions to read file

**Example:**
```typescript
const contents = await invoke<string>('read_file', {
  path: '/path/to/config.json'
});
console.log(contents);
```

**Validates Requirements:** 6.1, 6.5

---

#### `write_file`

Write string contents to a file.

**Rust Signature:**
```rust
#[tauri::command]
async fn write_file(path: String, contents: String, state: State<'_, FileServiceState>) -> Result<FileOperationResult, String>
```

**TypeScript Signature:**
```typescript
function write_file(path: string, contents: string): Promise<FileOperationResult>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | File path to write |
| `contents` | `string` | Yes | Contents to write |

**Returns:**
- **Success**: `FileOperationResult` object
- **Error**: Error message string

**FileOperationResult Type:**
```typescript
interface FileOperationResult {
  success: boolean;
  message: string;
}
```

**Example:**
```typescript
const result = await invoke<FileOperationResult>('write_file', {
  path: '/path/to/output.txt',
  contents: 'Hello, world!'
});
```

**Validates Requirements:** 6.2, 6.5

---

#### `append_file`

Append string contents to an existing file.

**Rust Signature:**
```rust
#[tauri::command]
async fn append_file(path: String, contents: String, state: State<'_, FileServiceState>) -> Result<FileOperationResult, String>
```

**TypeScript Signature:**
```typescript
function append_file(path: string, contents: string): Promise<FileOperationResult>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | File path to append to |
| `contents` | `string` | Yes | Contents to append |

**Returns:**
- **Success**: `FileOperationResult` object
- **Error**: Error message string

**Example:**
```typescript
await invoke('append_file', {
  path: '/path/to/log.txt',
  contents: '\nNew log entry'
});
```

**Validates Requirements:** 6.2, 6.5

---

#### `delete_file`

Delete a file from the file system.

**Rust Signature:**
```rust
#[tauri::command]
async fn delete_file(path: String, state: State<'_, FileServiceState>) -> Result<FileOperationResult, String>
```

**TypeScript Signature:**
```typescript
function delete_file(path: string): Promise<FileOperationResult>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | File path to delete |

**Returns:**
- **Success**: `FileOperationResult` object
- **Error**: Error message string

**Example:**
```typescript
await invoke('delete_file', {
  path: '/path/to/temp.txt'
});
```

**Validates Requirements:** 6.2, 6.5

---

#### `file_exists`

Check if a file exists.

**Rust Signature:**
```rust
#[tauri::command]
async fn file_exists(path: String, state: State<'_, FileServiceState>) -> Result<bool, String>
```

**TypeScript Signature:**
```typescript
function file_exists(path: string): Promise<boolean>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | File path to check |

**Returns:**
- **Success**: `true` if file exists, `false` otherwise
- **Error**: Error message string

**Example:**
```typescript
const exists = await invoke<boolean>('file_exists', {
  path: '/path/to/file.txt'
});
if (exists) {
  console.log('File exists');
}
```

**Validates Requirements:** 6.1, 6.5

---

#### `get_file_metadata`

Get metadata information about a file.

**Rust Signature:**
```rust
#[tauri::command]
async fn get_file_metadata(path: String, state: State<'_, FileServiceState>) -> Result<FileMetadata, String>
```

**TypeScript Signature:**
```typescript
function get_file_metadata(path: string): Promise<FileMetadata>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | File path |

**Returns:**
- **Success**: `FileMetadata` object
- **Error**: Error message string

**FileMetadata Type:**
```typescript
interface FileMetadata {
  path: string;
  name: string;
  size: number;
  isFile: boolean;
  isDirectory: boolean;
  modified: number;    // Unix timestamp
  created: number;     // Unix timestamp
}
```

**Example:**
```typescript
const metadata = await invoke<FileMetadata>('get_file_metadata', {
  path: '/path/to/file.txt'
});
console.log(`File size: ${metadata.size} bytes`);
```

**Validates Requirements:** 6.1, 6.5

---

#### `list_directory`

List all files and directories in a directory.

**Rust Signature:**
```rust
#[tauri::command]
async fn list_directory(path: String, state: State<'_, FileServiceState>) -> Result<Vec<FileMetadata>, String>
```

**TypeScript Signature:**
```typescript
function list_directory(path: string): Promise<FileMetadata[]>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | Directory path |

**Returns:**
- **Success**: Array of `FileMetadata` objects
- **Error**: Error message string

**Example:**
```typescript
const files = await invoke<FileMetadata[]>('list_directory', {
  path: '/path/to/directory'
});
files.forEach(file => {
  console.log(`${file.name} (${file.isDirectory ? 'dir' : 'file'})`);
});
```

**Validates Requirements:** 6.1, 6.5

---

#### `create_directory`

Create a new directory.

**Rust Signature:**
```rust
#[tauri::command]
async fn create_directory(path: String, state: State<'_, FileServiceState>) -> Result<FileOperationResult, String>
```

**TypeScript Signature:**
```typescript
function create_directory(path: string): Promise<FileOperationResult>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | Directory path to create |

**Returns:**
- **Success**: `FileOperationResult` object
- **Error**: Error message string

**Example:**
```typescript
await invoke('create_directory', {
  path: '/path/to/new/directory'
});
```

**Validates Requirements:** 6.2, 6.5

---

#### `delete_directory`

Delete a directory.

**Rust Signature:**
```rust
#[tauri::command]
async fn delete_directory(path: String, recursive: bool, state: State<'_, FileServiceState>) -> Result<FileOperationResult, String>
```

**TypeScript Signature:**
```typescript
function delete_directory(path: string, recursive: boolean): Promise<FileOperationResult>
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `path` | `string` | Yes | Directory path to delete |
| `recursive` | `boolean` | Yes | Whether to delete recursively |

**Returns:**
- **Success**: `FileOperationResult` object
- **Error**: Error message string

**Example:**
```typescript
await invoke('delete_directory', {
  path: '/path/to/directory',
  recursive: true
});
```

**Validates Requirements:** 6.2, 6.5

---

### Python Service Commands

Commands for managing the Python backend service lifecycle.

#### `start_python_service`

Start the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn start_python_service(state: State<'_, PythonServiceState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function start_python_service(): Promise<string>
```

**Parameters:** None

**Returns:**
- **Success**: `"Python service started successfully"`
- **Error**: Error message string

**Errors:**
- `"Service is already running"` - Cannot start when already running
- `"Failed to start Python service"` - Service startup failed

**Example:**
```typescript
try {
  await invoke('start_python_service');
  console.log('Backend service started');
} catch (error) {
  console.error('Failed to start service:', error);
}
```

**Validates Requirements:** 2.1, 4.1

---

#### `stop_python_service`

Stop the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn stop_python_service(state: State<'_, PythonServiceState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function stop_python_service(): Promise<string>
```

**Parameters:** None

**Returns:**
- **Success**: `"Python service stopped successfully"`
- **Error**: Error message string

**Errors:**
- `"Service is not running"` - Cannot stop when not running
- `"Failed to stop Python service"` - Service shutdown failed

**Example:**
```typescript
await invoke('stop_python_service');
```

**Validates Requirements:** 2.1, 4.1

---

#### `restart_python_service`

Restart the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn restart_python_service(state: State<'_, PythonServiceState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function restart_python_service(): Promise<string>
```

**Parameters:** None

**Returns:**
- **Success**: `"Python service restarted successfully"`
- **Error**: Error message string

**Example:**
```typescript
await invoke('restart_python_service');
```

**Validates Requirements:** 2.1, 4.1, 8.5

---

#### `get_python_service_status`

Get the current status of the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn get_python_service_status(state: State<'_, PythonServiceState>) -> Result<ServiceStatusResponse, String>
```

**TypeScript Signature:**
```typescript
function get_python_service_status(): Promise<ServiceStatusResponse>
```

**Parameters:** None

**Returns:**
- **Success**: `ServiceStatusResponse` object
- **Error**: Error message string

**ServiceStatusResponse Type:**
```typescript
interface ServiceStatusResponse {
  state: string;           // "stopped", "starting", "running", "stopping", "failed"
  isRunning: boolean;      // Whether service is currently running
  pid: number | null;      // Process ID if running
  restartCount: number;    // Number of times service has been restarted
  isMonitoring: boolean;   // Whether health monitoring is active
}
```

**Example:**
```typescript
const status = await invoke<ServiceStatusResponse>('get_python_service_status');
console.log(`Service state: ${status.state}`);
console.log(`PID: ${status.pid}`);
console.log(`Restart count: ${status.restartCount}`);
```

**Validates Requirements:** 2.1, 4.1, 4.7

---

#### `start_service_monitoring`

Start health monitoring for the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn start_service_monitoring(state: State<'_, PythonServiceState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function start_service_monitoring(): Promise<string>
```

**Parameters:** None

**Returns:**
- **Success**: `"Service monitoring started"`
- **Error**: Error message string

**Errors:**
- `"Service monitoring is already running"` - Cannot start when already monitoring

**Example:**
```typescript
await invoke('start_service_monitoring');
```

**Notes:**
- Monitoring performs periodic health checks on the service
- Automatically restarts the service if it becomes unresponsive
- Monitoring runs in a background thread

**Validates Requirements:** 4.7, 8.5

---

#### `stop_service_monitoring`

Stop health monitoring for the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn stop_service_monitoring(state: State<'_, PythonServiceState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function stop_service_monitoring(): Promise<string>
```

**Parameters:** None

**Returns:**
- **Success**: `"Service monitoring stopped"`
- **Error**: Error message string

**Errors:**
- `"Service monitoring is not running"` - Cannot stop when not monitoring

**Example:**
```typescript
await invoke('stop_service_monitoring');
```

**Validates Requirements:** 4.7, 8.5

---

#### `check_service_health`

Perform a manual health check on the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn check_service_health(state: State<'_, PythonServiceState>) -> Result<bool, String>
```

**TypeScript Signature:**
```typescript
function check_service_health(): Promise<boolean>
```

**Parameters:** None

**Returns:**
- **Success**: `true` if service is healthy, `false` otherwise
- **Error**: Error message string

**Example:**
```typescript
const isHealthy = await invoke<boolean>('check_service_health');
if (!isHealthy) {
  console.warn('Service is not healthy');
}
```

**Validates Requirements:** 4.7, 8.5

---

#### `reset_service_restart_count`

Reset the restart counter for the Python backend service.

**Rust Signature:**
```rust
#[tauri::command]
async fn reset_service_restart_count(state: State<'_, PythonServiceState>) -> Result<String, String>
```

**TypeScript Signature:**
```typescript
function reset_service_restart_count(): Promise<string>
```

**Parameters:** None

**Returns:**
- **Success**: `"Restart count reset successfully"`
- **Error**: Error message string

**Example:**
```typescript
await invoke('reset_service_restart_count');
```

**Validates Requirements:** 4.7

---

## Event System

> **📖 For comprehensive event documentation including all event types, payload structures, and usage examples, see [api-events-datamodels.md](./api-events-datamodels.md#event-system)**

Events are emitted from the Python backend and forwarded through Tauri to the frontend. The frontend can listen to events using the `@tauri-apps/api/event` module.

### Available Events

| Event Name | Description | Frequency | Validates Requirements |
|------------|-------------|-----------|----------------------|
| `transcript-updated` | New transcript available | High | 7.1, 1.2 |
| `response-generated` | AI response generated | Medium | 7.2, 1.3 |
| `status-changed` | System status changed | Low | 7.3, 1.8 |
| `error-occurred` | Error occurred | Low | 7.6, 8.1, 8.4 |
| `config-updated` | Configuration updated | Low | 7.6, 9.3 |

### Quick Example

```typescript
import { listen } from '@tauri-apps/api/event';

// Listen to transcript updates
const unlisten = await listen('transcript-updated', (event) => {
  const transcript = event.payload as TranscriptData;
  console.log('New transcript:', transcript.text);
});

// Cleanup when done
unlisten();
```

### React Hook Pattern

```typescript
import { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';

function MyComponent() {
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    
    const setupListener = async () => {
      unlisten = await listen('transcript-updated', (event) => {
        // Handle event
      });
    };
    
    setupListener();
    
    return () => {
      if (unlisten) unlisten();
    };
  }, []);
}
```

---

## Data Models

> **📖 For complete data model documentation including all type definitions, field descriptions, and examples, see [api-events-datamodels.md](./api-events-datamodels.md#data-models)**

### Core Types Summary

| Type | Description | Used In |
|------|-------------|---------|
| `TranscriptData` | Transcription result | `get_transcript`, `transcript-updated` event |
| `ResponseData` | AI response | `response-generated` event |
| `SystemStatus` | System state | `status-changed` event |
| `ConfigData` | Configuration | `get_config`, `update_config`, `config-updated` event |
| `AudioDevice` | Audio device info | `get_audio_devices` |
| `SystemInfo` | System information | `get_system_info` |
| `ErrorInfo` | Error information | `error-occurred` event |
| `FileMetadata` | File/directory metadata | File commands |
| `ServiceStatusResponse` | Python service status | `get_python_service_status` |

---

## IPC Protocol

Communication between Tauri middleware and Python backend uses JSON messages over stdin/stdout pipes.

### Protocol Overview

- **Transport**: stdin/stdout pipes
- **Format**: Line-delimited JSON
- **Encoding**: UTF-8
- **Message Types**: Command requests, command responses, and event notifications

### Message Format

#### Command Request

Sent from Tauri to Python backend to execute a command.

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

**Fields:**
- `type`: Always `"command"` for requests
- `id`: Unique request identifier (UUID recommended)
- `command`: Command name (snake_case)
- `params`: Command parameters (object)

---

#### Command Response (Success)

Sent from Python backend to Tauri when command succeeds.

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

**Fields:**
- `type`: Always `"response"`
- `id`: Matches the request ID
- `status`: `"success"` for successful commands
- `data`: Response data (structure varies by command)

---

#### Command Response (Error)

Sent from Python backend to Tauri when command fails.

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

**Fields:**
- `type`: Always `"response"`
- `id`: Matches the request ID
- `status`: `"error"` for failed commands
- `error`: Error object with code, message, and optional details

---

#### Event Message

Sent from Python backend to Tauri to notify of events.

```json
{
  "type": "event",
  "event": "transcript-updated",
  "data": {
    "id": "transcript-123",
    "timestamp": 1705449600,
    "source": "microphone",
    "text": "Hello world",
    "confidence": 0.95
  }
}
```

**Fields:**
- `type`: Always `"event"`
- `event`: Event name (kebab-case)
- `data`: Event payload (structure varies by event)

---

### Protocol Rules

1. **Line-Delimited**: Each message must be on a single line terminated with `\n`
2. **UTF-8 Encoding**: All messages must be UTF-8 encoded
3. **Valid JSON**: All messages must be valid JSON
4. **Request-Response**: Command requests expect exactly one response with matching ID
5. **Async Events**: Events can be sent at any time, independent of requests
6. **Error Handling**: Invalid messages should be logged but not crash the process

### Example Communication Flow

```
Frontend → Tauri: invoke('start_recording', { deviceType: 'microphone' })
Tauri → Python: {"type":"command","id":"req-001","command":"start_recording","params":{"device_type":"microphone"}}
Python → Tauri: {"type":"response","id":"req-001","status":"success","data":{"message":"Recording started"}}
Tauri → Frontend: Promise resolves with "Recording started"

Python → Tauri: {"type":"event","event":"transcript-updated","data":{...}}
Tauri → Frontend: Emits 'transcript-updated' event
```

---

## Error Codes

Comprehensive list of error codes used throughout the system.

### Audio Errors

| Code | Description | Possible Causes | Resolution |
|------|-------------|-----------------|------------|
| `DEVICE_NOT_FOUND` | Audio device not found | Invalid device ID, device disconnected | Check device ID, reconnect device |
| `DEVICE_BUSY` | Audio device is busy | Device in use by another application | Close other applications using the device |
| `RECORDING_FAILED` | Failed to start recording | Permission denied, device error | Check permissions, restart device |
| `RECORDING_NOT_ACTIVE` | No active recording to stop | Stop called without start | Ensure recording is started first |
| `AUDIO_INITIALIZATION_FAILED` | Failed to initialize audio system | Driver issues, missing dependencies | Reinstall audio drivers, check dependencies |

### Transcription Errors

| Code | Description | Possible Causes | Resolution |
|------|-------------|-----------------|------------|
| `TRANSCRIPTION_FAILED` | Failed to transcribe audio | Model error, invalid audio | Check model, verify audio quality |
| `MODEL_NOT_LOADED` | Transcription model not loaded | Model file missing, loading error | Download model, check file path |
| `INVALID_AUDIO` | Invalid audio data | Corrupted audio, wrong format | Verify audio format, re-record |
| `TRANSCRIPTION_TIMEOUT` | Transcription timed out | Audio too long, model slow | Reduce audio length, use faster model |

### AI Errors

| Code | Description | Possible Causes | Resolution |
|------|-------------|-----------------|------------|
| `PROVIDER_NOT_CONFIGURED` | AI provider not configured | Missing configuration, invalid provider | Configure provider in settings |
| `API_KEY_INVALID` | Invalid API key | Wrong key, expired key | Update API key in configuration |
| `GENERATION_FAILED` | Failed to generate response | API error, network issue | Check network, verify API status |
| `RATE_LIMIT_EXCEEDED` | API rate limit exceeded | Too many requests | Wait and retry, upgrade API plan |
| `CONTEXT_TOO_LONG` | Context exceeds maximum length | Too much conversation history | Reduce context length |
| `MODEL_NOT_AVAILABLE` | Requested model not available | Invalid model name, model deprecated | Use different model |

### Configuration Errors

| Code | Description | Possible Causes | Resolution |
|------|-------------|-----------------|------------|
| `CONFIG_NOT_FOUND` | Configuration file not found | File deleted, wrong path | Create default configuration |
| `CONFIG_INVALID` | Invalid configuration format | Corrupted file, syntax error | Fix JSON syntax, restore backup |
| `CONFIG_WRITE_FAILED` | Failed to write configuration | Permission denied, disk full | Check permissions, free disk space |
| `CONFIG_VALIDATION_FAILED` | Configuration validation failed | Invalid values | Fix configuration values |

### System Errors

| Code | Description | Possible Causes | Resolution |
|------|-------------|-----------------|------------|
| `SYSTEM_INFO_FAILED` | Failed to get system information | System API error | Restart application |
| `PERMISSION_DENIED` | Permission denied | Insufficient permissions | Grant required permissions |
| `RESOURCE_UNAVAILABLE` | System resource unavailable | Resource in use, system limit | Free resources, increase limits |
| `FILE_NOT_FOUND` | File not found | Invalid path, file deleted | Verify file path |
| `FILE_ACCESS_DENIED` | File access denied | Permission issue, file locked | Check permissions, close file |

### Service Errors

| Code | Description | Possible Causes | Resolution |
|------|-------------|-----------------|------------|
| `SERVICE_START_FAILED` | Failed to start Python service | Python not found, script error | Check Python installation |
| `SERVICE_STOP_FAILED` | Failed to stop Python service | Process not responding | Force kill process |
| `SERVICE_NOT_RUNNING` | Service is not running | Service crashed, not started | Start service |
| `SERVICE_HEALTH_CHECK_FAILED` | Service health check failed | Service unresponsive | Restart service |
| `IPC_COMMUNICATION_FAILED` | IPC communication failed | Pipe broken, process crashed | Restart service |

### Error Handling Best Practices

1. **Always Check Error Codes**: Use error codes for programmatic error handling
2. **Display User-Friendly Messages**: Show `error.message` to users, log `error.details` for debugging
3. **Implement Retry Logic**: For transient errors (network, rate limits), implement exponential backoff
4. **Log All Errors**: Log errors with full context for debugging
5. **Graceful Degradation**: Continue operation when possible, even after errors

**Example Error Handling:**
```typescript
try {
  await invoke('start_recording', { deviceType: 'microphone' });
} catch (error) {
  const errorInfo = error as ErrorInfo;
  
  switch (errorInfo.code) {
    case 'DEVICE_NOT_FOUND':
      showNotification('Microphone not found. Please connect a microphone.');
      break;
    case 'DEVICE_BUSY':
      showNotification('Microphone is busy. Please close other applications.');
      break;
    case 'PERMISSION_DENIED':
      showNotification('Microphone permission denied. Please grant permission.');
      break;
    default:
      showNotification(`Error: ${errorInfo.message}`);
      console.error('Unexpected error:', errorInfo);
  }
}
```

---

## Rate Limiting

Some operations have rate limits to prevent system overload and comply with external API limits.

### Command Rate Limits

| Command | Rate Limit | Window | Notes |
|---------|------------|--------|-------|
| `start_recording` | 10/minute | 60s | Prevents rapid start/stop cycles |
| `stop_recording` | 10/minute | 60s | Prevents rapid start/stop cycles |
| `generate_response` | Provider-dependent | Varies | Depends on AI provider's limits |
| `update_config` | 1/second | 1s | Prevents configuration thrashing |
| `get_system_info` | 10/second | 1s | Prevents excessive system queries |
| `get_audio_devices` | 5/second | 1s | Device enumeration is expensive |

### AI Provider Rate Limits

Rate limits vary by provider and plan:

| Provider | Typical Limit | Notes |
|----------|---------------|-------|
| OpenAI | 3-60 RPM | Depends on plan tier |
| Claude | 5-50 RPM | Depends on plan tier |
| DeepSeek | 60 RPM | Standard tier |
| Grok | Varies | Check provider documentation |
| GLM | Varies | Check provider documentation |

**RPM** = Requests Per Minute

### Rate Limit Handling

When a rate limit is exceeded:

1. **Error Response**: Command returns error with code `RATE_LIMIT_EXCEEDED`
2. **Retry-After Header**: Error details include suggested retry delay
3. **Exponential Backoff**: Implement exponential backoff for retries

**Example:**
```typescript
async function generateResponseWithRetry(context: string, maxRetries = 3) {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await invoke('generate_response', { context });
    } catch (error) {
      const errorInfo = error as ErrorInfo;
      
      if (errorInfo.code === 'RATE_LIMIT_EXCEEDED') {
        const delay = Math.pow(2, attempt) * 1000; // Exponential backoff
        console.log(`Rate limited, retrying in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      } else {
        throw error; // Re-throw non-rate-limit errors
      }
    }
  }
  
  throw new Error('Max retries exceeded');
}
```

---

## Best Practices

### Error Handling

Always wrap command invocations in try-catch blocks:

```typescript
try {
  const result = await invoke('start_recording', { deviceType: 'microphone' });
  console.log('Recording started:', result);
} catch (error) {
  console.error('Command failed:', error);
  
  // Handle specific error codes
  const errorInfo = error as ErrorInfo;
  if (errorInfo.code === 'DEVICE_NOT_FOUND') {
    showNotification('Please connect a microphone');
  } else {
    showNotification(`Error: ${errorInfo.message}`);
  }
}
```

**Key Points:**
- Always catch errors from invoke calls
- Check error codes for specific handling
- Display user-friendly messages
- Log detailed error information for debugging

---

### Event Cleanup

Always unlisten from events when components unmount to prevent memory leaks:

```typescript
import { useEffect } from 'react';
import { listen } from '@tauri-apps/api/event';

function MyComponent() {
  useEffect(() => {
    let unlisten: (() => void) | undefined;
    
    const setupListener = async () => {
      unlisten = await listen('transcript-updated', (event) => {
        // Handle event
        console.log('Transcript:', event.payload);
      });
    };
    
    setupListener();
    
    // Cleanup function
    return () => {
      if (unlisten) {
        unlisten();
      }
    };
  }, []); // Empty dependency array = setup once on mount
  
  return <div>My Component</div>;
}
```

**Key Points:**
- Store unlisten function for cleanup
- Call unlisten in useEffect cleanup
- Use empty dependency array for one-time setup
- Handle async setup properly

---

### Type Safety

Use TypeScript types for all API interactions:

```typescript
import { invoke } from '@tauri-apps/api/tauri';
import type { TranscriptData, ConfigData, AudioDevice } from './types/api';

// Type-safe command invocations
const transcript = await invoke<TranscriptData>('get_transcript');
const config = await invoke<ConfigData>('get_config');
const devices = await invoke<AudioDevice[]>('get_audio_devices');

// Type-safe event handling
await listen<TranscriptData>('transcript-updated', (event) => {
  const transcript = event.payload; // TypeScript knows this is TranscriptData
  console.log(transcript.text); // Autocomplete works!
});
```

**Key Points:**
- Always specify type parameters for invoke and listen
- Import types from centralized type definitions
- Leverage TypeScript's type checking and autocomplete
- Avoid using `any` type

---

### Performance Optimization

#### Debounce Frequent Operations

```typescript
import { debounce } from 'lodash';

// Debounce config updates
const debouncedUpdateConfig = debounce(async (config: ConfigData) => {
  await invoke('update_config', { config });
}, 1000); // Wait 1 second after last change

// Usage
function handleConfigChange(newConfig: ConfigData) {
  debouncedUpdateConfig(newConfig);
}
```

#### Batch Event Processing

```typescript
const transcriptBuffer: TranscriptData[] = [];

await listen<TranscriptData>('transcript-updated', (event) => {
  transcriptBuffer.push(event.payload);
});

// Process buffered transcripts periodically
setInterval(() => {
  if (transcriptBuffer.length > 0) {
    processTranscripts(transcriptBuffer.splice(0));
  }
}, 1000);
```

#### Cache System Information

```typescript
let cachedSystemInfo: SystemInfo | null = null;
let cacheTimestamp = 0;
const CACHE_TTL = 60000; // 1 minute

async function getSystemInfo(): Promise<SystemInfo> {
  const now = Date.now();
  
  if (cachedSystemInfo && (now - cacheTimestamp) < CACHE_TTL) {
    return cachedSystemInfo;
  }
  
  cachedSystemInfo = await invoke<SystemInfo>('get_system_info');
  cacheTimestamp = now;
  
  return cachedSystemInfo;
}
```

---

### Security Considerations

#### Validate User Input

```typescript
function validateDeviceType(deviceType: string): boolean {
  return deviceType === 'microphone' || deviceType === 'speaker';
}

async function startRecording(deviceType: string) {
  if (!validateDeviceType(deviceType)) {
    throw new Error('Invalid device type');
  }
  
  await invoke('start_recording', { deviceType });
}
```

#### Sanitize File Paths

```typescript
import { join, normalize } from '@tauri-apps/api/path';

async function readConfigFile(filename: string) {
  // Prevent path traversal attacks
  const sanitized = filename.replace(/\.\./g, '');
  const configDir = await join(await appDataDir(), 'config');
  const fullPath = await join(configDir, sanitized);
  
  return await invoke('read_file', { path: fullPath });
}
```

#### Mask Sensitive Data

```typescript
function maskApiKey(apiKey: string): string {
  if (apiKey.length <= 8) return '***';
  return apiKey.substring(0, 4) + '***' + apiKey.substring(apiKey.length - 4);
}

// Display masked API key in UI
console.log('API Key:', maskApiKey(config.ai.apiKey));
```

---

### Testing

#### Mock Tauri Commands

```typescript
// In tests
import { mockIPC } from '@tauri-apps/api/mocks';

beforeEach(() => {
  mockIPC((cmd, args) => {
    if (cmd === 'get_transcript') {
      return {
        id: 'test-1',
        timestamp: Date.now(),
        source: 'microphone',
        text: 'Test transcript',
        confidence: 0.95
      };
    }
  });
});
```

#### Test Event Handling

```typescript
import { emit } from '@tauri-apps/api/event';

test('handles transcript-updated event', async () => {
  const handler = jest.fn();
  
  await listen('transcript-updated', handler);
  
  await emit('transcript-updated', {
    id: 'test-1',
    timestamp: Date.now(),
    source: 'microphone',
    text: 'Test',
    confidence: 0.95
  });
  
  expect(handler).toHaveBeenCalled();
});
```

---

## API Reference Summary

### Quick Reference

**Commands by Category:**
- **Audio**: `start_recording`, `stop_recording`, `get_audio_devices`, `set_audio_device`
- **Transcription**: `get_transcript`
- **AI**: `generate_response`, `switch_provider`
- **Configuration**: `get_config`, `update_config`
- **System**: `get_system_info`
- **Files**: `read_file`, `write_file`, `append_file`, `delete_file`, `file_exists`, `get_file_metadata`, `list_directory`, `create_directory`, `delete_directory`
- **Python Service**: `start_python_service`, `stop_python_service`, `restart_python_service`, `get_python_service_status`, `start_service_monitoring`, `stop_service_monitoring`, `check_service_health`, `reset_service_restart_count`

**Events:**
- `transcript-updated`: New transcript available
- `response-generated`: AI response generated
- `status-changed`: System status changed
- `error-occurred`: Error occurred
- `config-updated`: Configuration updated

**Key Data Types:**
- `TranscriptData`, `ResponseData`, `SystemStatus`, `ConfigData`, `AudioDevice`, `SystemInfo`, `ErrorInfo`, `FileMetadata`, `ServiceStatusResponse`

---

## Additional Resources

- **[Event System & Data Models Documentation](./api-events-datamodels.md)**: Comprehensive event and data model documentation
- **[Architecture Documentation](./architecture.md)**: System architecture overview
- **[Protocol Documentation](./protocol.md)**: Detailed IPC protocol specification
- **[Development Guide](./development.md)**: Development setup and guidelines
- **[Deployment Guide](./deployment.md)**: Deployment instructions

---

## Versioning

**Current API Version**: 1.0.0

**Version History:**
- **1.0.0** (2024-01-16): Initial release with full command and event system

**Versioning Policy:**
- **Major version** (X.0.0): Breaking changes to API
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

**Breaking Changes:**
Breaking changes will be announced in advance and will increment the major version number. Deprecated features will be supported for at least one major version before removal.

---

## Support

For issues, questions, or contributions:
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check docs/ directory for detailed guides
- **Code Examples**: See frontend/src/ for usage examples

---

**Last Updated**: January 16, 2026  
**API Version**: 1.0.0  
**Document Version**: 1.0.0
