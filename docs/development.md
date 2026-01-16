# DeepEcho Development Guide

## Getting Started

This guide covers setting up the development environment and working with the DeepEcho codebase.

## Prerequisites

### Required Software

- **Node.js** 18+ and npm/yarn
- **Rust** 1.70+ (install via [rustup](https://rustup.rs/))
- **Python** 3.8+
- **FFmpeg** (for audio processing)
- **Git**

### Platform-Specific Requirements

**Windows:**
- Visual Studio Build Tools
- PyAudioWPatch (auto-installed)

**macOS:**
- Xcode Command Line Tools
- PortAudio: `brew install portaudio`
- BlackHole: `brew install blackhole-2ch`

**Linux:**
- Build essentials
- ALSA development libraries

## Initial Setup

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/deepecho.git
cd deepecho
```

### 2. Install Tauri CLI

```bash
cargo install tauri-cli
```

### 3. Setup Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Setup Backend

```bash
cd backend
pip install -r requirements.txt
cd ..
```

### 5. Setup Tauri

```bash
cd src-tauri
cargo build
cd ..
```

## Development Workflow

### Running in Development Mode

#### Option 1: Full Stack Development

Run all components together:

```bash
npm run tauri dev
```

This will:
1. Start the frontend dev server (Vite)
2. Build and run the Tauri app
3. Start the Python backend service

#### Option 2: Component-by-Component

**Frontend only:**
```bash
cd frontend
npm run dev
```

**Backend only:**
```bash
cd backend
python src/backend_service.py
```

**Tauri only:**
```bash
cd src-tauri
cargo tauri dev
```

### Hot Reload

- **Frontend**: Vite provides hot module replacement (HMR)
- **Backend**: Restart required for changes
- **Tauri**: Rebuild required for Rust changes

### Development Tools

#### Frontend

```bash
cd frontend

# Type checking
npm run type-check

# Linting
npm run lint

# Formatting
npm run format

# Testing
npm run test
```

#### Backend

```bash
cd backend

# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Linting
pylint src/

# Formatting
black src/
```

#### Tauri

```bash
cd src-tauri

# Check code
cargo clippy

# Format code
cargo fmt

# Run tests
cargo test
```

## Project Structure

### Frontend Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   ├── hooks/          # Custom hooks
│   ├── services/       # Service layer
│   ├── store/          # State management
│   ├── types/          # TypeScript types
│   ├── theme/          # MUI theme
│   ├── App.tsx         # Main component
│   └── main.tsx        # Entry point
├── public/             # Static assets
└── package.json
```

### Backend Structure

```
backend/
├── src/
│   ├── audio/          # Audio processing
│   ├── ai/             # AI providers
│   ├── config/         # Configuration
│   ├── api/            # API layer
│   ├── ipc/            # IPC communication
│   └── utils/          # Utilities
├── tests/              # Test files
└── requirements.txt
```

### Tauri Structure

```
src-tauri/
├── src/
│   ├── commands/       # Command handlers
│   ├── handlers/       # Core handlers
│   ├── services/       # Service layer
│   ├── models/         # Data models
│   └── main.rs         # Entry point
└── Cargo.toml
```

## Coding Standards

### TypeScript/React

- Use functional components with hooks
- Use TypeScript strict mode
- Follow React best practices
- Use Material-UI components
- Write unit tests for components

**Example Component:**
```typescript
import React from 'react';
import { Box, Typography } from '@mui/material';

interface TranscriptDisplayProps {
  transcript: string;
  confidence: number;
}

export const TranscriptDisplay: React.FC<TranscriptDisplayProps> = ({
  transcript,
  confidence
}) => {
  return (
    <Box>
      <Typography variant="body1">{transcript}</Typography>
      <Typography variant="caption">
        Confidence: {(confidence * 100).toFixed(1)}%
      </Typography>
    </Box>
  );
};
```

### Rust

- Follow Rust naming conventions
- Use `Result` for error handling
- Write documentation comments
- Use `async/await` for async operations
- Write unit tests

**Example Command:**
```rust
#[tauri::command]
async fn start_recording(device_type: String) -> Result<String, String> {
    // Validate input
    if device_type != "microphone" && device_type != "speaker" {
        return Err("Invalid device type".to_string());
    }
    
    // Execute command
    match execute_recording(&device_type).await {
        Ok(_) => Ok("Recording started".to_string()),
        Err(e) => Err(format!("Failed to start recording: {}", e))
    }
}
```

### Python

- Follow PEP 8 style guide
- Use type hints
- Write docstrings
- Use async/await where appropriate
- Write unit tests

**Example Service:**
```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AudioRecorder:
    """Audio recording service."""
    
    def __init__(self, device_type: str):
        """Initialize audio recorder.
        
        Args:
            device_type: Type of device ('microphone' or 'speaker')
        """
        self.device_type = device_type
        self.is_recording = False
    
    async def start_recording(self) -> bool:
        """Start audio recording.
        
        Returns:
            True if recording started successfully
            
        Raises:
            AudioDeviceError: If device is not available
        """
        try:
            # Implementation
            self.is_recording = True
            logger.info(f"Started recording from {self.device_type}")
            return True
        except Exception as e:
            logger.error(f"Failed to start recording: {e}")
            raise
```

## Testing

### Frontend Tests

```bash
cd frontend

# Unit tests
npm run test

# Component tests
npm run test:components

# Integration tests
npm run test:integration

# E2E tests
npm run test:e2e
```

### Backend Tests

```bash
cd backend

# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Property-based tests
pytest tests/property/

# All tests with coverage
pytest --cov=src tests/
```

### Tauri Tests

```bash
cd src-tauri

# Unit tests
cargo test

# Integration tests
cargo test --test '*'
```

## Debugging

### Frontend Debugging

Use browser DevTools:
1. Open app in development mode
2. Right-click → Inspect Element
3. Use Console, Network, and React DevTools

### Backend Debugging

Use Python debugger:
```python
import pdb; pdb.set_trace()
```

Or use IDE debugger (VS Code, PyCharm)

### Tauri Debugging

Use Rust debugger:
```bash
# With lldb
rust-lldb target/debug/deepecho

# With gdb
rust-gdb target/debug/deepecho
```

## Common Issues

### Frontend Issues

**Issue: Module not found**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

**Issue: Type errors**
```bash
npm run type-check
```

### Backend Issues

**Issue: Import errors**
```bash
cd backend
pip install -r requirements.txt --force-reinstall
```

**Issue: Audio device not found**
- Check system audio settings
- Verify device permissions
- Install platform-specific audio libraries

### Tauri Issues

**Issue: Build fails**
```bash
cd src-tauri
cargo clean
cargo build
```

**Issue: IPC communication fails**
- Check backend service is running
- Verify IPC message format
- Check logs for errors

## Performance Profiling

### Frontend Profiling

Use React DevTools Profiler:
1. Open React DevTools
2. Go to Profiler tab
3. Start recording
4. Perform actions
5. Stop recording and analyze

### Backend Profiling

Use Python profiler:
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### Tauri Profiling

Use Rust profiler:
```bash
cargo install flamegraph
cargo flamegraph
```

## Git Workflow

### Branch Naming

- `feature/feature-name`: New features
- `fix/bug-description`: Bug fixes
- `refactor/component-name`: Refactoring
- `docs/topic`: Documentation updates

### Commit Messages

Follow conventional commits:
```
feat: add audio device selection
fix: resolve memory leak in transcriber
docs: update API documentation
refactor: simplify command handlers
test: add property tests for IPC
```

### Pull Request Process

1. Create feature branch
2. Make changes and commit
3. Write tests
4. Update documentation
5. Create pull request
6. Address review comments
7. Merge when approved

## Code Review Checklist

- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No console.log or debug statements
- [ ] Error handling is comprehensive
- [ ] Performance is acceptable
- [ ] Security considerations addressed

## Resources

- [Tauri Documentation](https://tauri.app/)
- [React Documentation](https://react.dev/)
- [Material-UI Documentation](https://mui.com/)
- [Rust Documentation](https://www.rust-lang.org/)
- [Python Documentation](https://www.python.org/)

## Getting Help

- Check existing documentation
- Search GitHub issues
- Ask in project discussions
- Contact maintainers

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for detailed contribution guidelines.
