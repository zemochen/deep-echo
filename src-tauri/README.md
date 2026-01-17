# DeepEcho Tauri Layer

Rust-based middleware layer providing IPC communication between React frontend and Python backend.

## Overview

The Tauri layer acts as a bridge between the web-based frontend and the Python backend service. It handles:

- Command routing from frontend to backend
- Event forwarding from backend to frontend
- System resource access (files, devices)
- Python subprocess management
- Error handling and logging

## Technology Stack

- **Tauri**: Cross-platform framework
- **Rust**: Systems programming language
- **Tokio**: Async runtime
- **Serde**: Serialization/deserialization
- **Python subprocess**: Backend service management

## Project Structure

```
src-tauri/
├── src/
│   ├── commands/           # Tauri command handlers
│   │   ├── audio.rs
│   │   ├── transcription.rs
│   │   ├── ai.rs
│   │   ├── config.rs
│   │   └── system.rs
│   ├── handlers/           # Core handlers
│   │   ├── ipc_handler.rs
│   │   ├── event_handler.rs
│   │   └── error_handler.rs
│   ├── services/           # Service layer
│   │   ├── python_service.rs
│   │   ├── file_service.rs
│   │   └── system_service.rs
│   ├── models/             # Data models
│   │   ├── request.rs
│   │   ├── response.rs
│   │   └── event.rs
│   ├── lib.rs              # Library exports
│   └── main.rs             # Application entry
├── Cargo.toml              # Rust dependencies
├── tauri.conf.json         # Tauri configuration
└── build.rs                # Build script
```

## Development Setup

### Quick Start

See [GETTING_STARTED.md](./GETTING_STARTED.md) for a complete walkthrough.

### Prerequisites

- Rust 1.70+ (install via rustup)
- Tauri CLI: `cargo install tauri-cli`
- Python 3.8+ (for backend service)
- Platform-specific requirements (see [SETUP.md](./SETUP.md))

### Check Your Environment

Run the setup check script:

**macOS/Linux:**
```bash
./check_setup.sh
```

**Windows:**
```cmd
check_setup.bat
```

### Installation

```bash
cd backend-tauri
cargo build
```

**Note:** First build takes 10-15 minutes.

### Development

```bash
# Run in development mode (requires frontend setup)
cargo tauri dev

# Build for production
cargo tauri build

# Run tests
cargo test

# Check code
cargo clippy
```

## Tauri Commands

### Audio Commands

```rust
// Start audio recording
start_recording(device_type: String) -> Result<String, String>

// Stop audio recording
stop_recording() -> Result<String, String>

// Get available audio devices
get_audio_devices() -> Result<Vec<AudioDevice>, String>

// Set audio device
set_audio_device(device_type: String, device_id: String) -> Result<String, String>
```

### Transcription Commands

```rust
// Get current transcript
get_transcript() -> Result<TranscriptData, String>
```

### AI Commands

```rust
// Generate AI response
generate_response(context: String) -> Result<String, String>

// Switch AI provider
switch_provider(provider: String) -> Result<String, String>
```

### Configuration Commands

```rust
// Get configuration
get_config() -> Result<ConfigData, String>

// Update configuration
update_config(config: ConfigData) -> Result<String, String>
```

### System Commands

```rust
// Get system information
get_system_info() -> Result<SystemInfo, String>
```

## Event System

Events emitted from backend to frontend:

- `transcript-updated`: New transcription available
- `response-generated`: AI response ready
- `status-changed`: System status update
- `error-occurred`: Error notification
- `config-updated`: Configuration changed

## Python Service Management

The Tauri layer manages the Python backend service lifecycle:

1. **Startup**: Launch Python subprocess on app start
2. **Health Check**: Monitor service health
3. **Auto-restart**: Restart on failure
4. **Shutdown**: Graceful shutdown on app exit

## IPC Communication

Communication with Python backend uses:

- **Stdin/Stdout**: JSON-based message passing
- **Named Pipes**: Platform-specific IPC (optional)
- **HTTP**: Local REST API (optional)

## Error Handling

Comprehensive error handling:

- Command execution errors
- IPC communication errors
- Python service errors
- System resource errors

All errors are logged and forwarded to frontend.

## Security

- File access restricted to app directory
- API keys stored securely
- Input validation on all commands
- Sandboxed execution environment

## Platform Support

- **Windows**: Full support with WASAPI audio
- **macOS**: Full support with CoreAudio
- **Linux**: Planned support

## Building

```bash
# Development build
cargo tauri dev

# Production build
cargo tauri build

# Platform-specific builds
cargo tauri build --target x86_64-pc-windows-msvc
cargo tauri build --target x86_64-apple-darwin
cargo tauri build --target aarch64-apple-darwin
```

## Testing

```bash
# Unit tests
cargo test

# Integration tests
cargo test --test '*'

# Property-based tests
cargo test --features proptest
```

## Contributing

See the main project README for contribution guidelines.

## License

MIT License - see LICENSE file in project root.
