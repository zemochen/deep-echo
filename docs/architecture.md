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
