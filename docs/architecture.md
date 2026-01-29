# DeepEcho Architecture Documentation

## Overview

DeepEcho uses a three-tier architecture with frontend-backend separation:

1. **Frontend Layer** (TypeScript/React): User interface and interaction
2. **Middleware Layer** (Tauri/Rust): IPC communication and system access
3. **Backend Layer** (Python): AI processing and core logic

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│                  (TypeScript/React/MUI)                     │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   UI         │  │   State      │  │   Services   │    │
│  │ Components   │  │ Management   │  │   Layer      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                    Tauri Commands & Events
                            │
┌─────────────────────────────────────────────────────────────┐
│                   Middleware Layer                          │
│                     (Tauri/Rust)                            │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │   Command    │  │     IPC      │  │   System     │    │
│  │   Handlers   │  │   Handler    │  │  Resources   │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
                            │
                      IPC Communication
                            │
┌─────────────────────────────────────────────────────────────┐
│                    Backend Layer                            │
│                       (Python)                              │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │    Audio     │  │      AI      │  │    Config    │    │
│  │  Processing  │  │   Providers  │  │  Management  │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend Layer

**Responsibilities:**
- Render user interface
- Handle user interactions
- Display real-time transcriptions and responses
- Manage UI state
- Invoke Tauri commands
- Listen to backend events

**Key Technologies:**
- React 18+ for component-based UI
- TypeScript for type safety
- Material-UI for component library
- Zustand for state management
- Web Audio API for audio visualization

**Communication:**
- Sends commands to Tauri layer via `invoke()`
- Receives events from Tauri layer via `listen()`

**Component Structure:**
```
frontend/src/
├── components/          # UI Components
│   ├── TranscriptDisplay.tsx    # Shows real-time transcriptions
│   ├── ResponseDisplay.tsx      # Shows AI responses
│   ├── ControlPanel.tsx         # Control buttons and settings
│   ├── ProviderSelector.tsx     # AI provider selection
│   ├── StatusIndicator.tsx      # System status display
│   └── index.ts                 # Component exports
├── hooks/              # Custom React Hooks
│   ├── useAudioRecording.ts     # Audio recording state
│   ├── useTranscript.ts         # Transcript data management
│   ├── useResponse.ts           # Response data management
│   └── useTauriCommand.ts       # Tauri command wrapper
├── services/           # Service Layer
│   ├── tauriService.ts          # Tauri API wrapper
│   ├── audioService.ts          # Web Audio API wrapper
│   ├── eventService.ts          # Event handling
│   └── systemService.ts         # System utilities
├── store/              # State Management
│   ├── appStore.ts              # Application state (Zustand)
│   └── uiStore.ts               # UI state (Zustand)
└── types/              # TypeScript Types
    ├── api.ts                   # API data models
    ├── commands.ts              # Command interfaces
    ├── events.ts                # Event interfaces
    └── index.ts                 # Type exports
```

### Middleware Layer (Tauri)

**Responsibilities:**
- Route commands from frontend to backend
- Forward events from backend to frontend
- Manage Python subprocess lifecycle
- Provide system resource access
- Handle errors and logging
- Ensure security and sandboxing

**Key Technologies:**
- Tauri framework for cross-platform support
- Rust for performance and safety
- Tokio for async runtime
- Serde for JSON serialization

**Communication:**
- Receives commands from frontend via Tauri API
- Communicates with backend via IPC (stdin/stdout)
- Emits events to frontend via Tauri event system

**Component Structure:**
```
src-tauri/src/
├── commands/           # Command Handlers
│   ├── audio.rs                 # Audio commands (start/stop recording)
│   ├── transcription.rs         # Transcription commands
│   ├── ai.rs                    # AI commands (generate/switch)
│   ├── config.rs                # Configuration commands
│   ├── system.rs                # System info commands
│   └── mod.rs                   # Command exports
├── handlers/           # Core Handlers
│   ├── ipc_handler.rs           # IPC communication handler
│   ├── event_handler.rs         # Event forwarding handler
│   └── error_handler.rs         # Error handling and logging
├── services/           # Service Layer
│   ├── python_service.rs        # Python subprocess management
│   ├── file_service.rs          # File system operations
│   └── system_service.rs        # System resource access
├── models/             # Data Models
│   ├── request.rs               # Request models
│   ├── response.rs              # Response models
│   └── event.rs                 # Event models
├── lib.rs              # Library exports
└── main.rs             # Application entry point
```

### Backend Layer

**Responsibilities:**
- Capture audio from microphone and speaker
- Transcribe audio to text
- Generate AI responses
- Manage configuration
- Emit events to middleware
- Handle errors and logging

**Key Technologies:**
- Python 3.8+ for core logic
- SpeechRecognition for transcription
- Multiple AI provider SDKs
- PyAudioWPatch (Windows) / PyAudio (macOS)

**Communication:**
- Receives commands from Tauri via IPC
- Sends responses and events to Tauri via IPC

**Component Structure:**
```
src/
├── audio/              # Audio Processing
│   ├── recorder.py              # Audio recording (mic + speaker)
│   ├── transcriber.py           # Speech-to-text transcription
│   └── models.py                # Whisper model management
├── audio_system/       # Platform-Specific Audio
│   ├── audio_interface.py       # Abstract audio interface
│   ├── audio_factory.py         # Device factory pattern
│   ├── windows_audio.py         # WASAPI loopback (Windows)
│   └── macos_audio.py           # BlackHole integration (macOS)
├── ai/                 # AI Processing
│   ├── adapter.py               # AI provider adapter
│   ├── responder.py             # Response generation
│   └── providers/               # Provider implementations
│       ├── openai_provider.py
│       ├── deepseek_provider.py
│       ├── claude_provider.py
│       └── ...
├── config/             # Configuration Management
│   ├── config_manager.py        # Configuration CRUD
│   ├── settings.py              # Settings definitions
│   └── validator.py             # Config validation
├── ipc/                # IPC Communication (NEW)
│   ├── ipc_server.py            # IPC server implementation
│   ├── message_handler.py       # Message routing
│   └── event_emitter.py         # Event emission
├── utils/              # Utilities
│   ├── logger.py                # Logging system
│   ├── exceptions.py            # Custom exceptions
│   ├── retry.py                 # Retry logic
│   └── threading.py             # Thread management
└── backend_service.py  # Service Entry Point (NEW)
```

## Data Flow

### Command Flow (Frontend → Backend)

```
User Action
    ↓
Frontend Component
    ↓
Tauri Command (invoke)
    ↓
Tauri Command Handler
    ↓
IPC Message to Backend
    ↓
Backend Message Handler
    ↓
Backend Service Execution
    ↓
IPC Response to Tauri
    ↓
Tauri Response to Frontend
    ↓
UI Update
```

**Detailed Example: Starting Audio Recording**

1. **User Action**: User clicks "Start Recording" button
   ```typescript
   // ControlPanel.tsx
   const handleStartRecording = async () => {
     try {
       await invoke('start_recording', { deviceType: 'microphone' });
     } catch (error) {
       console.error('Failed to start recording:', error);
     }
   };
   ```

2. **Frontend → Tauri**: Invoke command via Tauri API
   ```typescript
   // tauriService.ts wraps the invoke call
   export async function startRecording(deviceType: string): Promise<void> {
     await invoke('start_recording', { deviceType });
   }
   ```

3. **Tauri Command Handler**: Receives and processes command
   ```rust
   // src-tauri/src/commands/audio.rs
   #[tauri::command]
   pub async fn start_recording(
     device_type: String,
     state: State<'_, AppState>
   ) -> Result<String, String> {
     // Forward to IPC handler
     let response = state.ipc_handler
       .send_command("start_recording", json!({ "device_type": device_type }))
       .await?;
     Ok(response)
   }
   ```

4. **Tauri → Backend**: Send IPC message
   ```rust
   // src-tauri/src/handlers/ipc_handler.rs
   pub async fn send_command(&self, command: &str, params: Value) -> Result<Value> {
     let message = json!({
       "type": "command",
       "id": generate_id(),
       "command": command,
       "params": params
     });
     // Write to Python stdin
     self.write_to_python(message).await?;
     // Wait for response
     self.wait_for_response(id).await
   }
   ```

5. **Backend Message Handler**: Receives and routes command
   ```python
   # backend/ipc/message_handler.py
   def handle_message(self, message: dict):
     if message['type'] == 'command':
       command = message['command']
       params = message['params']
       result = self.route_command(command, params)
       self.send_response(message['id'], result)
   ```

6. **Backend Service**: Executes command
   ```python
   # backend/audio/recorder.py
   def start_recording(self, device_type: str):
     if device_type == 'microphone':
       self.mic_source = sr.Microphone()
     elif device_type == 'speaker':
       self.speaker_source = self.get_speaker_device()
     self.is_recording = True
     self.emit_event('status-changed', {'state': 'recording'})
     return {'message': 'Recording started'}
   ```

7. **Backend → Tauri**: Send response
   ```python
   # backend/ipc/ipc_server.py
   def send_response(self, request_id: str, data: dict):
     response = {
       'type': 'response',
       'id': request_id,
       'status': 'success',
       'data': data
     }
     print(json.dumps(response), flush=True)
   ```

8. **Tauri → Frontend**: Return result
   ```rust
   // Command handler returns result to frontend
   Ok("Recording started".to_string())
   ```

9. **UI Update**: Frontend updates state and UI
   ```typescript
   // useAudioRecording.ts
   const [isRecording, setIsRecording] = useState(false);
   
   const startRecording = async () => {
     await startRecording('microphone');
     setIsRecording(true);
   };
   ```

### Event Flow (Backend → Frontend)

```
Backend Event Trigger
    ↓
Event Emitter
    ↓
IPC Event to Tauri
    ↓
Tauri Event Handler
    ↓
Tauri Event Emission
    ↓
Frontend Event Listener
    ↓
State Update
    ↓
UI Re-render
```

**Detailed Example: Transcript Update**

1. **Backend Event Trigger**: Transcription completes
   ```python
   # backend/audio/transcriber.py
   def transcribe_audio(self, audio_data):
     text = self.recognizer.recognize_whisper(audio_data)
     transcript = TranscriptData(
       id=str(uuid.uuid4()),
       timestamp=int(time.time() * 1000),
       source='microphone',
       text=text,
       confidence=0.95
     )
     self.emit_event('transcript-updated', transcript)
   ```

2. **Event Emitter**: Sends event to IPC
   ```python
   # backend/ipc/event_emitter.py
   def emit_event(self, event_name: str, data: dict):
     event = {
       'type': 'event',
       'event': event_name,
       'data': data
     }
     print(json.dumps(event), flush=True)
   ```

3. **Tauri Event Handler**: Receives event from Python
   ```rust
   // src-tauri/src/handlers/event_handler.rs
   pub async fn handle_python_output(&self, line: String) {
     if let Ok(message) = serde_json::from_str::<Value>(&line) {
       if message["type"] == "event" {
         let event_name = message["event"].as_str().unwrap();
         let data = message["data"].clone();
         self.emit_to_frontend(event_name, data).await;
       }
     }
   }
   ```

4. **Tauri → Frontend**: Emit event
   ```rust
   // src-tauri/src/handlers/event_handler.rs
   async fn emit_to_frontend(&self, event: &str, payload: Value) {
     self.app_handle
       .emit_all(event, payload)
       .expect("Failed to emit event");
   }
   ```

5. **Frontend Event Listener**: Receives event
   ```typescript
   // eventService.ts
   export function listenToTranscriptUpdates(
     callback: (transcript: TranscriptData) => void
   ): UnlistenFn {
     return listen<TranscriptData>('transcript-updated', (event) => {
       callback(event.payload);
     });
   }
   ```

6. **State Update**: Update application state
   ```typescript
   // useTranscript.ts
   useEffect(() => {
     const unlisten = listenToTranscriptUpdates((transcript) => {
       setTranscripts(prev => [...prev, transcript]);
     });
     return () => unlisten();
   }, []);
   ```

7. **UI Re-render**: React re-renders component
   ```typescript
   // TranscriptDisplay.tsx
   export function TranscriptDisplay() {
     const transcripts = useTranscriptStore(state => state.transcripts);
     
     return (
       <div>
         {transcripts.map(t => (
           <div key={t.id}>{t.text}</div>
         ))}
       </div>
     );
   }
   ```

## Communication Protocols

### Tauri Commands

Commands are synchronous or asynchronous function calls from frontend to backend:

```typescript
// Frontend
const result = await invoke('start_recording', { 
  deviceType: 'microphone' 
});
```

```rust
// Tauri
#[tauri::command]
async fn start_recording(device_type: String) -> Result<String, String> {
  // Forward to backend via IPC
}
```

## Component Interactions

### 1. Audio Recording Flow

**Participants**: User → Frontend → Tauri → Backend → Audio System

**Sequence**:
```
User clicks "Start Recording"
    ↓
ControlPanel.tsx invokes start_recording command
    ↓
tauriService.ts wraps the invoke call
    ↓
Tauri audio.rs command handler receives request
    ↓
ipc_handler.rs sends JSON message to Python
    ↓
message_handler.py routes to AudioRecorder
    ↓
recorder.py initializes audio device
    ↓
Platform-specific audio system (WASAPI/BlackHole) starts capture
    ↓
Success response flows back through layers
    ↓
Frontend updates UI state (recording indicator)
```

**Key Components**:
- **Frontend**: `ControlPanel.tsx`, `useAudioRecording.ts`, `tauriService.ts`
- **Tauri**: `commands/audio.rs`, `handlers/ipc_handler.rs`
- **Backend**: `ipc/message_handler.py`, `audio/recorder.py`, `audio_system/`

**Data Flow**:
```typescript
// Frontend sends
{ deviceType: 'microphone' }

// Tauri forwards
{
  "type": "command",
  "id": "req-001",
  "command": "start_recording",
  "params": { "device_type": "microphone" }
}

// Backend responds
{
  "type": "response",
  "id": "req-001",
  "status": "success",
  "data": { "message": "Recording started" }
}
```

### 2. Transcription Flow

**Participants**: Audio System → Backend → Tauri → Frontend

**Sequence**:
```
Audio data captured from device
    ↓
recorder.py buffers audio chunks
    ↓
transcriber.py processes audio with Whisper
    ↓
TranscriptData object created
    ↓
event_emitter.py emits 'transcript-updated' event
    ↓
Tauri event_handler.rs receives event from Python stdout
    ↓
Tauri emits event to frontend
    ↓
eventService.ts receives event
    ↓
useTranscript.ts updates state
    ↓
TranscriptDisplay.tsx re-renders with new transcript
```

**Key Components**:
- **Backend**: `audio/recorder.py`, `audio/transcriber.py`, `ipc/event_emitter.py`
- **Tauri**: `handlers/event_handler.rs`
- **Frontend**: `services/eventService.ts`, `hooks/useTranscript.ts`, `components/TranscriptDisplay.tsx`

**Data Flow**:
```python
# Backend emits
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

# Frontend receives
event.payload: TranscriptData
```

### 3. AI Response Generation Flow

**Participants**: Frontend → Tauri → Backend → AI Provider → Backend → Tauri → Frontend

**Sequence**:
```
User triggers response generation (auto or manual)
    ↓
Frontend invokes generate_response command with context
    ↓
Tauri forwards command to Backend
    ↓
message_handler.py routes to AIAdapter
    ↓
adapter.py selects current provider
    ↓
Provider (e.g., deepseek_provider.py) calls API
    ↓
API response received and processed
    ↓
ResponseData object created
    ↓
event_emitter.py emits 'response-generated' event
    ↓
Tauri forwards event to Frontend
    ↓
useResponse.ts updates state
    ↓
ResponseDisplay.tsx shows AI response
```

**Key Components**:
- **Frontend**: `hooks/useResponse.ts`, `components/ResponseDisplay.tsx`
- **Tauri**: `commands/ai.rs`, `handlers/ipc_handler.rs`, `handlers/event_handler.rs`
- **Backend**: `ai/adapter.py`, `ai/responder.py`, `ai/providers/*`

**Data Flow**:
```typescript
// Frontend sends
{ context: "User said: Hello" }

// Backend processes and emits
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

### 4. Configuration Management Flow

**Participants**: Frontend → Tauri → Backend → File System

**Sequence**:
```
User modifies configuration in UI
    ↓
Frontend invokes update_config command
    ↓
Tauri forwards to Backend
    ↓
config_manager.py validates configuration
    ↓
validator.py checks all constraints
    ↓
Configuration saved to JSON file
    ↓
event_emitter.py emits 'config-updated' event
    ↓
Tauri forwards event to Frontend
    ↓
Frontend updates UI with new config
```

**Key Components**:
- **Frontend**: `components/ControlPanel.tsx`, `store/appStore.ts`
- **Tauri**: `commands/config.rs`, `services/file_service.rs`
- **Backend**: `config/config_manager.py`, `config/validator.py`

**Data Flow**:
```typescript
// Frontend sends
{
  config: {
    audio: { recordTimeout: 5, energyThreshold: 1000 },
    ai: { provider: "deepseek", model: "deepseek-chat" },
    ui: { updateInterval: 3, theme: "dark" }
  }
}

// Backend validates and saves, then emits
{
  "type": "event",
  "event": "config-updated",
  "data": { /* full config */ }
}
```

### 5. Error Handling Flow

**Participants**: Any Component → Error Handler → User

**Sequence**:
```
Error occurs in any layer
    ↓
Component catches error
    ↓
error_handler creates ErrorInfo object
    ↓
Error logged to file
    ↓
'error-occurred' event emitted
    ↓
Frontend receives error event
    ↓
UI displays error notification
    ↓
User sees error message
```

**Key Components**:
- **Backend**: `utils/exceptions.py`, `ipc/event_emitter.py`
- **Tauri**: `handlers/error_handler.rs`
- **Frontend**: `services/eventService.ts`, `components/StatusIndicator.tsx`

**Data Flow**:
```python
# Backend emits
{
  "type": "event",
  "event": "error-occurred",
  "data": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Audio device not found",
    "details": "Device ID 'invalid' does not exist"
  }
}

# Frontend displays error
```

### 6. System Status Updates

**Participants**: Backend → Tauri → Frontend

**Sequence**:
```
System state changes (idle → recording → processing)
    ↓
Backend component updates status
    ↓
event_emitter.py emits 'status-changed' event
    ↓
Tauri forwards to Frontend
    ↓
StatusIndicator.tsx updates display
```

**Key Components**:
- **Backend**: All service components
- **Tauri**: `handlers/event_handler.rs`
- **Frontend**: `components/StatusIndicator.tsx`, `store/appStore.ts`

**Data Flow**:
```python
# Backend emits
{
  "type": "event",
  "event": "status-changed",
  "data": {
    "state": "recording",
    "message": "Recording audio from microphone",
    "details": { "device": "Built-in Microphone" }
  }
}
```

### 7. Python Service Lifecycle

**Participants**: Tauri → Python Backend

**Sequence**:
```
Application starts
    ↓
Tauri main.rs initializes
    ↓
python_service.rs spawns Python subprocess
    ↓
backend_service.py starts IPC server
    ↓
Health check confirms backend is ready
    ↓
Application ready for user interaction
    ↓
... (normal operation) ...
    ↓
Application closes
    ↓
Tauri sends shutdown signal
    ↓
Python gracefully shuts down
    ↓
Subprocess terminated
```

**Key Components**:
- **Tauri**: `services/python_service.rs`, `main.rs`
- **Backend**: `backend_service.py`, `ipc/ipc_server.py`

### 8. State Synchronization

**Participants**: Frontend ↔ Backend

**Mechanism**: Event-driven updates with periodic polling fallback

**Synchronization Points**:
1. **Initial Load**: Frontend fetches current state on startup
2. **Event Updates**: Backend pushes state changes via events
3. **Periodic Sync**: Frontend polls for state every N seconds (fallback)
4. **User Actions**: Frontend commands update backend state

**Example - Recording State**:
```
Frontend State: isRecording = false
    ↓
User clicks "Start Recording"
    ↓
Frontend: isRecording = true (optimistic update)
    ↓
Command sent to backend
    ↓
Backend: recording_active = true
    ↓
Backend emits 'status-changed' event
    ↓
Frontend confirms: isRecording = true
```

### IPC Messages

JSON-based message format for Tauri ↔ Backend communication:

**Request:**
```json
{
  "type": "command",
  "id": "req-123",
  "command": "start_recording",
  "params": { "device_type": "microphone" }
}
```

**Response:**
```json
{
  "type": "response",
  "id": "req-123",
  "status": "success",
  "data": { "message": "Recording started" }
}
```

**Event:**
```json
{
  "type": "event",
  "event": "transcript-updated",
  "data": {
    "id": "transcript-123",
    "text": "Hello world",
    "confidence": 0.95
  }
}
```

### Tauri Events

Events are asynchronous notifications from backend to frontend:

```typescript
// Frontend
await listen('transcript-updated', (event) => {
  console.log('New transcript:', event.payload);
});
```

```rust
// Tauri
app.emit_all("transcript-updated", payload)?;
```

## State Management

### Frontend State

Managed by Zustand stores:

**appStore:**
- Transcripts
- AI responses
- Configuration
- System status

**uiStore:**
- UI frozen state
- Selected devices
- Theme preferences
- Window state

### Backend State

Managed by Python service:
- Audio recorder state
- Transcriber state
- AI adapter state
- Configuration state

### State Synchronization

Frontend and backend states are synchronized via:
1. Initial state fetch on app start
2. Event-driven updates
3. Periodic polling (fallback)

## Cross-Layer Dependencies

### Frontend Dependencies on Tauri

**Direct Dependencies**:
- `@tauri-apps/api` - Core Tauri API
- `@tauri-apps/api/tauri` - Command invocation
- `@tauri-apps/api/event` - Event listening
- `@tauri-apps/api/window` - Window management

**Usage Pattern**:
```typescript
import { invoke } from '@tauri-apps/api/tauri';
import { listen } from '@tauri-apps/api/event';

// Command invocation
await invoke('command_name', { params });

// Event listening
const unlisten = await listen('event-name', handler);
```

### Tauri Dependencies on Backend

**Communication Method**: IPC via stdin/stdout

**Message Format**: JSON

**Dependency Management**:
- Tauri spawns Python subprocess
- Monitors Python process health
- Restarts on failure
- Graceful shutdown on app close

**Python Requirements**:
```
# requirements.txt
SpeechRecognition>=3.10.0
openai>=1.0.0
anthropic>=0.7.0
pyaudio>=0.2.13
pyaudiowpatch>=0.2.12.5  # Windows only
```

### Backend Dependencies on System

**Audio System**:
- **Windows**: WASAPI loopback via PyAudioWPatch
- **macOS**: BlackHole virtual audio device
- **Both**: System microphone access

**File System**:
- Configuration files in app data directory
- Log files in logs directory
- Model cache in cache directory

**Network**:
- AI provider APIs (OpenAI, Anthropic, DeepSeek, etc.)
- Model downloads (Whisper)

## Integration Points

### 1. Frontend-Tauri Integration

**Integration Layer**: Tauri API

**Key Files**:
- Frontend: `src/services/tauriService.ts`
- Tauri: `src-tauri/src/commands/*.rs`

**Contract**: TypeScript types match Rust command signatures

**Example**:
```typescript
// Frontend type
interface StartRecordingParams {
  deviceType: 'microphone' | 'speaker';
}

// Rust signature
#[tauri::command]
async fn start_recording(device_type: String) -> Result<String, String>
```

### 2. Tauri-Backend Integration

**Integration Layer**: IPC (stdin/stdout)

**Key Files**:
- Tauri: `src-tauri/src/handlers/ipc_handler.rs`
- Backend: `src/ipc/ipc_server.py`, `src/ipc/message_handler.py`

**Contract**: JSON message format

**Message Types**:
1. Command Request (Tauri → Backend)
2. Command Response (Backend → Tauri)
3. Event (Backend → Tauri)

**Example**:
```rust
// Tauri sends
{
  "type": "command",
  "id": "req-001",
  "command": "start_recording",
  "params": { "device_type": "microphone" }
}

// Backend responds
{
  "type": "response",
  "id": "req-001",
  "status": "success",
  "data": { "message": "Recording started" }
}
```

### 3. Backend-Audio System Integration

**Integration Layer**: Platform-specific audio APIs

**Key Files**:
- Backend: `src/audio_system/audio_factory.py`
- Windows: `src/audio_system/windows_audio.py`
- macOS: `src/audio_system/macos_audio.py`

**Contract**: Abstract `AudioInterface` class

**Platform Detection**:
```python
def create_audio_system():
    if platform.system() == 'Windows':
        return WindowsAudio()
    elif platform.system() == 'Darwin':
        return MacOSAudio()
    else:
        raise UnsupportedPlatformError()
```

### 4. Backend-AI Provider Integration

**Integration Layer**: Provider adapter pattern

**Key Files**:
- Backend: `src/ai/adapter.py`
- Providers: `src/ai/providers/*.py`

**Contract**: Abstract `BaseProvider` class

**Provider Selection**:
```python
def get_provider(name: str) -> BaseProvider:
    providers = {
        'openai': OpenAIProvider,
        'deepseek': DeepSeekProvider,
        'claude': ClaudeProvider,
        # ...
    }
    return providers[name]()
```

## Data Consistency

### Type Consistency

All data models are defined consistently across layers:

**Example: TranscriptData**

```rust
// Rust (Tauri)
#[derive(Serialize, Deserialize)]
pub struct TranscriptData {
    pub id: String,
    pub timestamp: u64,
    pub source: String,
    pub text: String,
    pub confidence: f32,
}
```

```typescript
// TypeScript (Frontend)
interface TranscriptData {
  id: string;
  timestamp: number;
  source: 'microphone' | 'speaker';
  text: string;
  confidence: number;
}
```

```python
# Python (Backend)
@dataclass
class TranscriptData:
    id: str
    timestamp: int
    source: str
    text: str
    confidence: float
```

### Naming Conventions

| Layer | Convention | Example |
|-------|-----------|---------|
| Rust | snake_case | `device_type` |
| TypeScript | camelCase | `deviceType` |
| Python | snake_case | `device_type` |
| JSON | snake_case | `device_type` |

### Validation

Each layer validates data:

1. **Frontend**: TypeScript type checking + runtime validation
2. **Tauri**: Rust type system + Serde validation
3. **Backend**: Python type hints + runtime validation

## Concurrency Model

### Frontend

**Model**: Single-threaded event loop (JavaScript)

**Async Operations**: Promises and async/await

**State Updates**: React state updates are batched

### Tauri

**Model**: Multi-threaded with Tokio async runtime

**Command Handling**: Each command runs in async task

**Event Emission**: Thread-safe event emitter

### Backend

**Model**: Multi-threaded Python

**Audio Processing**: Separate thread for audio capture

**Transcription**: Separate thread for transcription

**AI Generation**: Separate thread for API calls

**IPC Server**: Main thread handles stdin/stdout

## Resource Management

### Memory Management

**Frontend**:
- React component lifecycle
- Automatic garbage collection
- Event listener cleanup on unmount

**Tauri**:
- Rust ownership system
- Automatic resource cleanup (RAII)
- Arc/Mutex for shared state

**Backend**:
- Python garbage collection
- Explicit resource cleanup in context managers
- Thread pool management

### File Handles

**Tauri**:
- File operations use Rust's File API
- Automatic close on drop
- Async file I/O

**Backend**:
- Context managers for file operations
- Explicit close in finally blocks
- Log rotation to prevent file growth

### Network Connections

**Backend**:
- Connection pooling for AI providers
- Timeout configuration
- Retry logic with exponential backoff
- Graceful degradation on failure

## Error Handling

### Error Propagation

```
Backend Error
    ↓
IPC Error Response
    ↓
Tauri Error Handler
    ↓
Frontend Error Handler
    ↓
User Notification
```

### Error Types

- **Command Errors**: Failed command execution
- **IPC Errors**: Communication failures
- **Backend Errors**: Service errors
- **System Errors**: Resource access errors

### Recovery Strategies

- Automatic retry with exponential backoff
- Graceful degradation
- User notification
- Logging and diagnostics

## Security

### Sandboxing

- Frontend runs in Tauri webview (sandboxed)
- Backend runs as subprocess (isolated)
- File access restricted to app directory

### API Key Protection

- Keys stored in secure configuration
- Never exposed to frontend
- Encrypted at rest (optional)

### Input Validation

- All commands validated in Tauri layer
- All IPC messages validated
- File paths sanitized

## Performance Optimization

### Frontend

- Virtual scrolling for large lists
- Debounced updates
- Lazy loading of components
- Memoization of expensive computations

### Middleware

- Async command handling
- Connection pooling
- Request batching
- Caching

### Backend

- Multi-threaded audio processing
- Queue-based message handling
- Resource usage monitoring
- Memory optimization

## Scalability

### Horizontal Scaling

- Backend can be deployed as separate service
- Multiple frontend instances can connect
- Load balancing support

### Vertical Scaling

- Efficient resource usage
- Configurable thread pools
- Memory limits
- CPU throttling

## Deployment

### Desktop Application

- Single executable with embedded frontend
- Python backend bundled or installed separately
- Auto-update support

### Web Application (Future)

- Frontend deployed to CDN
- Backend deployed to cloud
- WebSocket communication

## Monitoring

### Metrics

- Command execution time
- Event latency
- Memory usage
- CPU usage
- Error rates

### Logging

- Structured logging
- Multiple log levels
- Log rotation
- Remote logging (optional)

## Testing Strategy

### Unit Tests

- Frontend: Component tests, hook tests
- Middleware: Command tests, IPC tests
- Backend: Service tests, provider tests

### Integration Tests

- End-to-end command flow
- Event propagation
- Error handling
- State synchronization

### Property-Based Tests

- Communication consistency
- Event reliability
- Configuration persistence
- Error handling completeness

## Future Enhancements

### Planned Features

- Web-based deployment
- Mobile app support
- Plugin system
- Cloud synchronization
- Multi-user support

### Technical Improvements

- GraphQL API
- WebSocket communication
- Distributed tracing
- Advanced caching
- Performance profiling

## References

- [Tauri Documentation](https://tauri.app/)
- [React Documentation](https://react.dev/)
- [Rust Documentation](https://www.rust-lang.org/)
- [Python Documentation](https://www.python.org/)
