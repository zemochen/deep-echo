# Interface Specifications

## Overview

This document provides a comprehensive specification of all interfaces in the DeepEcho system, including data models, command interfaces, and event interfaces.

## Table of Contents

1. [Data Models](#data-models)
2. [Command Interfaces](#command-interfaces)
3. [Event Interfaces](#event-interfaces)
4. [Type Mappings](#type-mappings)
5. [Validation Rules](#validation-rules)

## Data Models

### TranscriptData

Represents transcribed audio data.

**Rust Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TranscriptData {
    pub id: String,
    pub timestamp: u64,
    pub source: String,
    pub text: String,
    pub confidence: f32,
}
```

**TypeScript Definition:**
```typescript
interface TranscriptData {
  id: string;
  timestamp: number;
  source: 'microphone' | 'speaker';
  text: string;
  confidence: number;
}
```

**Python Definition:**
```python
@dataclass
class TranscriptData:
    id: str
    timestamp: int
    source: str  # "microphone" or "speaker"
    text: str
    confidence: float
```

**Fields:**
- `id`: Unique identifier for the transcript (UUID format)
- `timestamp`: Unix timestamp in milliseconds
- `source`: Audio source - "microphone" or "speaker"
- `text`: Transcribed text content
- `confidence`: Confidence score (0.0 to 1.0)

**Validation:**
- `id`: Must be non-empty string
- `timestamp`: Must be positive integer
- `source`: Must be "microphone" or "speaker"
- `text`: Can be empty string
- `confidence`: Must be between 0.0 and 1.0

### ResponseData

Represents AI-generated response data.

**Rust Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResponseData {
    pub id: String,
    pub timestamp: u64,
    pub provider: String,
    pub text: String,
    pub context: String,
}
```

**TypeScript Definition:**
```typescript
interface ResponseData {
  id: string;
  timestamp: number;
  provider: string;
  text: string;
  context: string;
}
```

**Python Definition:**
```python
@dataclass
class ResponseData:
    id: str
    timestamp: int
    provider: str
    text: str
    context: str
```

**Fields:**
- `id`: Unique identifier for the response (UUID format)
- `timestamp`: Unix timestamp in milliseconds
- `provider`: AI provider name (e.g., "deepseek", "openai")
- `text`: Generated response text
- `context`: Context used for generation

**Validation:**
- `id`: Must be non-empty string
- `timestamp`: Must be positive integer
- `provider`: Must be valid provider name
- `text`: Must be non-empty string
- `context`: Can be empty string

### SystemStatus

Represents current system status.

**Rust Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemStatus {
    pub state: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
}
```

**TypeScript Definition:**
```typescript
interface SystemStatus {
  state: 'idle' | 'recording' | 'processing' | 'error';
  message: string;
  details?: Record<string, any>;
}
```

**Python Definition:**
```python
@dataclass
class SystemStatus:
    state: str  # "idle", "recording", "processing", "error"
    message: str
    details: Optional[Dict[str, Any]] = None
```

**Fields:**
- `state`: Current system state
- `message`: Human-readable status message
- `details`: Optional additional details

**Validation:**
- `state`: Must be one of: "idle", "recording", "processing", "error"
- `message`: Must be non-empty string
- `details`: Optional, can be any JSON object

### ConfigData

Represents application configuration.

**Rust Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ConfigData {
    pub audio: AudioConfig,
    pub ai: AIConfig,
    pub ui: UIConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioConfig {
    pub record_timeout: u32,
    pub energy_threshold: u32,
    pub device: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AIConfig {
    pub provider: String,
    pub model: String,
    pub api_key: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UIConfig {
    pub update_interval: u32,
    pub theme: String,
}
```

**TypeScript Definition:**
```typescript
interface ConfigData {
  audio: AudioConfig;
  ai: AIConfig;
  ui: UIConfig;
}

interface AudioConfig {
  recordTimeout: number;
  energyThreshold: number;
  device?: string;
}

interface AIConfig {
  provider: string;
  model: string;
  apiKey: string;
}

interface UIConfig {
  updateInterval: number;
  theme: 'light' | 'dark';
}
```

**Python Definition:**
```python
@dataclass
class AudioConfig:
    record_timeout: int
    energy_threshold: int
    device: Optional[str] = None

@dataclass
class AIConfig:
    provider: str
    model: str
    api_key: str

@dataclass
class UIConfig:
    update_interval: int
    theme: str  # "light" or "dark"

@dataclass
class ConfigData:
    audio: AudioConfig
    ai: AIConfig
    ui: UIConfig
```

**Fields:**
- `audio.recordTimeout`: Recording timeout in seconds (1-60)
- `audio.energyThreshold`: Energy threshold for voice detection (100-4000)
- `audio.device`: Optional device ID
- `ai.provider`: AI provider name
- `ai.model`: Model name
- `ai.apiKey`: API key (encrypted in storage)
- `ui.updateInterval`: UI update interval in seconds (1-10)
- `ui.theme`: UI theme - "light" or "dark"

**Validation:**
- `audio.recordTimeout`: 1 ≤ value ≤ 60
- `audio.energyThreshold`: 100 ≤ value ≤ 4000
- `ai.provider`: Must be valid provider name
- `ai.model`: Must be non-empty string
- `ai.apiKey`: Must be non-empty string
- `ui.updateInterval`: 1 ≤ value ≤ 10
- `ui.theme`: Must be "light" or "dark"

### AudioDevice

Represents an audio device.

**Rust Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AudioDevice {
    pub id: String,
    pub name: String,
    pub device_type: String,
}
```

**TypeScript Definition:**
```typescript
interface AudioDevice {
  id: string;
  name: string;
  deviceType: string;
}
```

**Python Definition:**
```python
@dataclass
class AudioDevice:
    id: str
    name: str
    device_type: str  # "microphone" or "speaker"
```

**Fields:**
- `id`: Device identifier
- `name`: Human-readable device name
- `deviceType`: Device type - "microphone" or "speaker"

**Validation:**
- `id`: Must be non-empty string
- `name`: Must be non-empty string
- `deviceType`: Must be "microphone" or "speaker"

### SystemInfo

Represents system information.

**Rust Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SystemInfo {
    pub platform: String,
    pub version: String,
    pub arch: String,
}
```

**TypeScript Definition:**
```typescript
interface SystemInfo {
  platform: string;
  version: string;
  arch: string;
}
```

**Python Definition:**
```python
@dataclass
class SystemInfo:
    platform: str
    version: str
    arch: str
```

**Fields:**
- `platform`: Operating system (e.g., "windows", "macos", "linux")
- `version`: OS version
- `arch`: CPU architecture (e.g., "x86_64", "arm64")

**Validation:**
- All fields must be non-empty strings

### ErrorInfo

Represents error information.

**Rust Definition:**
```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ErrorInfo {
    pub code: String,
    pub message: String,
    pub details: Option<serde_json::Value>,
}
```

**TypeScript Definition:**
```typescript
interface ErrorInfo {
  code: string;
  message: string;
  details?: any;
}
```

**Python Definition:**
```python
@dataclass
class ErrorInfo:
    code: str
    message: str
    details: Optional[Any] = None
```

**Fields:**
- `code`: Error code (e.g., "DEVICE_NOT_FOUND")
- `message`: Human-readable error message
- `details`: Optional additional error details

**Validation:**
- `code`: Must be non-empty string, uppercase with underscores
- `message`: Must be non-empty string
- `details`: Optional, can be any JSON value

## Command Interfaces

### Audio Commands

#### start_recording

**Signature:**
```rust
async fn start_recording(device_type: String) -> Result<String, String>
```

**Parameters:**
- `device_type`: "microphone" or "speaker"

**Returns:**
- Success: "Recording started"
- Error: Error message

**Errors:**
- `DEVICE_NOT_FOUND`: Device not found
- `DEVICE_BUSY`: Device is busy
- `RECORDING_FAILED`: Failed to start recording
- `DEVICE_PERMISSION_DENIED`: Permission denied

#### stop_recording

**Signature:**
```rust
async fn stop_recording() -> Result<String, String>
```

**Parameters:** None

**Returns:**
- Success: "Recording stopped"
- Error: Error message

**Errors:**
- `RECORDING_NOT_ACTIVE`: No active recording

#### get_audio_devices

**Signature:**
```rust
async fn get_audio_devices() -> Result<Vec<AudioDevice>, String>
```

**Parameters:** None

**Returns:**
- Success: Array of AudioDevice
- Error: Error message

**Errors:**
- `DEVICE_ENUMERATION_FAILED`: Failed to enumerate devices
- `PERMISSION_DENIED`: Permission denied

#### set_audio_device

**Signature:**
```rust
async fn set_audio_device(device_type: String, device_id: String) -> Result<String, String>
```

**Parameters:**
- `device_type`: "microphone" or "speaker"
- `device_id`: Device ID from get_audio_devices

**Returns:**
- Success: "Device set successfully"
- Error: Error message

**Errors:**
- `DEVICE_NOT_FOUND`: Device not found
- `INVALID_DEVICE_TYPE`: Invalid device type

### Transcription Commands

#### get_transcript

**Signature:**
```rust
async fn get_transcript() -> Result<TranscriptData, String>
```

**Parameters:** None

**Returns:**
- Success: TranscriptData
- Error: Error message

**Errors:**
- `TRANSCRIPT_NOT_AVAILABLE`: No transcript available
- `TRANSCRIPTION_FAILED`: Transcription failed

### AI Commands

#### generate_response

**Signature:**
```rust
async fn generate_response(context: String) -> Result<String, String>
```

**Parameters:**
- `context`: Context for AI response generation

**Returns:**
- Success: Generated response text
- Error: Error message

**Errors:**
- `PROVIDER_NOT_CONFIGURED`: AI provider not configured
- `API_KEY_INVALID`: Invalid API key
- `GENERATION_FAILED`: Failed to generate response
- `RATE_LIMIT_EXCEEDED`: API rate limit exceeded

#### switch_provider

**Signature:**
```rust
async fn switch_provider(provider: String) -> Result<String, String>
```

**Parameters:**
- `provider`: Provider name (e.g., "deepseek", "openai", "claude")

**Returns:**
- Success: "Provider switched to {provider}"
- Error: Error message

**Errors:**
- `PROVIDER_NOT_FOUND`: Provider not found
- `PROVIDER_NOT_CONFIGURED`: Provider not configured

### Configuration Commands

#### get_config

**Signature:**
```rust
async fn get_config() -> Result<ConfigData, String>
```

**Parameters:** None

**Returns:**
- Success: ConfigData
- Error: Error message

**Errors:**
- `CONFIG_NOT_FOUND`: Configuration file not found
- `CONFIG_INVALID`: Invalid configuration format

#### update_config

**Signature:**
```rust
async fn update_config(config: ConfigData) -> Result<String, String>
```

**Parameters:**
- `config`: New configuration data

**Returns:**
- Success: "Configuration updated"
- Error: Error message

**Errors:**
- `CONFIG_VALIDATION_FAILED`: Configuration validation failed
- `CONFIG_WRITE_FAILED`: Failed to write configuration

### System Commands

#### get_system_info

**Signature:**
```rust
async fn get_system_info() -> Result<SystemInfo, String>
```

**Parameters:** None

**Returns:**
- Success: SystemInfo
- Error: Error message

**Errors:**
- `SYSTEM_INFO_FAILED`: Failed to get system information

## Event Interfaces

### transcript-updated

**Event Name:** `transcript-updated`

**Payload:** TranscriptData

**Emitted When:** New transcript is available from audio transcription

**Frequency:** High - emitted for each transcription result

**Example:**
```typescript
listen<TranscriptData>('transcript-updated', (event) => {
  console.log('New transcript:', event.payload.text);
});
```

### response-generated

**Event Name:** `response-generated`

**Payload:** ResponseData

**Emitted When:** AI response is generated

**Frequency:** Medium - emitted when AI completes response generation

**Example:**
```typescript
listen<ResponseData>('response-generated', (event) => {
  console.log('AI response:', event.payload.text);
});
```

### status-changed

**Event Name:** `status-changed`

**Payload:** SystemStatus

**Emitted When:** System status changes

**Frequency:** Low - emitted on state transitions

**Example:**
```typescript
listen<SystemStatus>('status-changed', (event) => {
  console.log('Status:', event.payload.state);
});
```

### error-occurred

**Event Name:** `error-occurred`

**Payload:** ErrorInfo

**Emitted When:** An error occurs in the backend

**Frequency:** Low - emitted on errors

**Example:**
```typescript
listen<ErrorInfo>('error-occurred', (event) => {
  console.error('Error:', event.payload.message);
});
```

### config-updated

**Event Name:** `config-updated`

**Payload:** ConfigData

**Emitted When:** Configuration is updated

**Frequency:** Low - emitted when config changes

**Example:**
```typescript
listen<ConfigData>('config-updated', (event) => {
  console.log('Config updated:', event.payload);
});
```

## Type Mappings

### Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| Rust | snake_case | `device_type` |
| TypeScript | camelCase | `deviceType` |
| Python | snake_case | `device_type` |
| JSON | snake_case | `device_type` |

### Field Name Mappings

| Rust | TypeScript | Python | JSON |
|------|-----------|--------|------|
| `device_type` | `deviceType` | `device_type` | `device_type` |
| `record_timeout` | `recordTimeout` | `record_timeout` | `record_timeout` |
| `energy_threshold` | `energyThreshold` | `energy_threshold` | `energy_threshold` |
| `update_interval` | `updateInterval` | `update_interval` | `update_interval` |
| `api_key` | `apiKey` | `api_key` | `api_key` |

## Validation Rules

### General Rules

1. **Non-empty Strings**: All string fields marked as required must be non-empty
2. **Positive Numbers**: All numeric fields must be positive unless specified
3. **Enums**: Enum fields must match one of the specified values exactly
4. **Optional Fields**: Optional fields can be null/undefined/None

### Specific Validations

#### TranscriptData
- `confidence`: 0.0 ≤ value ≤ 1.0
- `source`: Must be "microphone" or "speaker"
- `timestamp`: Must be valid Unix timestamp

#### ConfigData
- `audio.recordTimeout`: 1 ≤ value ≤ 60
- `audio.energyThreshold`: 100 ≤ value ≤ 4000
- `ui.updateInterval`: 1 ≤ value ≤ 10
- `ui.theme`: Must be "light" or "dark"

#### ErrorInfo
- `code`: Must be uppercase with underscores (e.g., "DEVICE_NOT_FOUND")

### Validation Implementation

**TypeScript:**
```typescript
function validateTranscriptData(data: TranscriptData): boolean {
  return (
    data.id.length > 0 &&
    data.timestamp > 0 &&
    (data.source === 'microphone' || data.source === 'speaker') &&
    data.confidence >= 0.0 &&
    data.confidence <= 1.0
  );
}
```

**Rust:**
```rust
impl TranscriptData {
    pub fn validate(&self) -> Result<(), String> {
        if self.id.is_empty() {
            return Err("ID cannot be empty".to_string());
        }
        if self.confidence < 0.0 || self.confidence > 1.0 {
            return Err("Confidence must be between 0.0 and 1.0".to_string());
        }
        Ok(())
    }
}
```

**Python:**
```python
def validate_transcript_data(data: TranscriptData) -> bool:
    return (
        len(data.id) > 0 and
        data.timestamp > 0 and
        data.source in ["microphone", "speaker"] and
        0.0 <= data.confidence <= 1.0
    )
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-16 | Initial interface specification |
