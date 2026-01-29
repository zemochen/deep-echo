# DeepEcho Development Guide

This guide provides comprehensive instructions for setting up your development environment, understanding the development workflow, and debugging common issues in the DeepEcho frontend-backend separation architecture.

## Table of Contents

1. [Development Environment Setup](#development-environment-setup)
2. [Development Workflow](#development-workflow)
3. [Debugging Tips](#debugging-tips)
4. [Common Issues and Solutions](#common-issues-and-solutions)
5. [Best Practices](#best-practices)

---

## Development Environment Setup

### Prerequisites

Before you begin, ensure you have the following installed:

#### Required Software

1. **Node.js and npm**
   - Version: Node.js 18+ and npm 9+
   - Download: https://nodejs.org/
   - Verify installation:
     ```bash
     node --version
     npm --version
     ```

2. **Rust and Cargo**
   - Version: Rust 1.70+
   - Install via rustup: https://rustup.rs/
   - Verify installation:
     ```bash
     rustc --version
     cargo --version
     ```

3. **Python**
   - Version: Python 3.8+
   - Download: https://www.python.org/downloads/
   - Verify installation:
     ```bash
     python --version
     pip --version
     ```

4. **Tauri CLI**
   - Install globally:
     ```bash
     npm install -g @tauri-apps/cli
     ```
   - Or use via npx (recommended for project-specific versions)

#### Platform-Specific Requirements

**Windows:**
- Visual Studio Build Tools 2019 or later
- WebView2 Runtime (usually pre-installed on Windows 10/11)
- Install via: https://developer.microsoft.com/en-us/microsoft-edge/webview2/

**macOS:**
- Xcode Command Line Tools
  ```bash
  xcode-select --install
  ```
- For audio capture: BlackHole virtual audio device
  ```bash
  brew install blackhole-2ch
  ```

**Linux:**
- Build essentials and development libraries
  ```bash
  sudo apt-get update
  sudo apt-get install -y libwebkit2gtk-4.0-dev \
    build-essential \
    curl \
    wget \
    libssl-dev \
    libgtk-3-dev \
    libayatana-appindicator3-dev \
    librsvg2-dev
  ```

### Initial Setup

#### 1. Clone the Repository

```bash
git clone <repository-url>
cd deepecho
```

#### 2. Set Up Python Backend

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### 3. Set Up Frontend

```bash
cd frontend
npm install
cd ..
```

#### 4. Set Up Tauri

```bash
cd backend-tauri
cargo build
cd ..
```

#### 5. Configure API Keys

```bash
# Copy example keys file
cp keys.example.py keys.py

# Edit keys.py and add your API keys
# For OpenAI, DeepSeek, Claude, etc.
```

#### 6. Configure Application

```bash
# Copy example config
cp resources/config.example.json resources/config.json

# Edit config.json with your preferences
```

### Verify Installation

Run the verification script to ensure everything is set up correctly:

```bash
# On macOS/Linux:
./dev.sh check

# On Windows:
dev.bat check
```

---

## Development Workflow

### Project Structure Overview

```
deepecho/
├── frontend/           # React/TypeScript frontend
├── src-tauri/         # Tauri middleware (Rust)
├── src/               # Python backend
├── docs/              # Documentation
├── tests/             # Test suites
└── scripts/           # Build and utility scripts
```

### Running the Application in Development Mode

#### Quick Start (Recommended)

Use the provided development scripts:

```bash
# On macOS/Linux:
./dev.sh

# On Windows:
dev.bat
```

This will:
1. Start the Python backend service
2. Build and launch the Tauri application
3. Open the frontend with hot-reload enabled

#### Manual Start (For Debugging)

**Terminal 1 - Backend Service:**
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
python backend/backend_service.py
```

**Terminal 2 - Tauri + Frontend:**
```bash
cd backend-tauri
cargo tauri dev
```

### Development Modes

#### Frontend Development

For rapid frontend iteration without backend:

```bash
cd frontend
npm run dev
```

This starts Vite dev server on `http://localhost:5173` with:
- Hot Module Replacement (HMR)
- Fast refresh
- TypeScript type checking

**Note:** Tauri commands won't work in this mode. Use for UI-only development.

#### Backend Development

For backend-only testing:

```bash
source .venv/bin/activate
python backend/backend_service.py --debug
```

Test backend endpoints using the verification script:

```bash
python verify_backend_adaptation.py
```

#### Tauri Development

For Tauri middleware development:

```bash
cd backend-tauri
cargo build
cargo test
```

### Making Changes

#### Frontend Changes

1. **Component Development:**
   - Edit files in `frontend/src/components/`
   - Changes auto-reload via HMR
   - Check browser console for errors

2. **Type Definitions:**
   - Update types in `frontend/src/types/`
   - Run type check: `npm run type-check`

3. **State Management:**
   - Modify stores in `frontend/src/store/`
   - Use React DevTools to inspect state

4. **Styling:**
   - Update theme in `frontend/src/theme/`
   - Material-UI components use theme automatically

#### Backend Changes

1. **Core Logic:**
   - Edit files in `src/audio/`, `src/ai/`, etc.
   - Restart backend service to apply changes

2. **IPC Handlers:**
   - Modify `src/ipc/message_handler.py`
   - Update event emitters in `src/ipc/event_emitter.py`

3. **Configuration:**
   - Update `src/config/config_manager.py`
   - Changes require service restart

#### Tauri Changes

1. **Commands:**
   - Edit command files in `src-tauri/src/commands/`
   - Rebuild: `cargo build`

2. **IPC Handlers:**
   - Modify handlers in `src-tauri/src/handlers/`
   - Rebuild required

3. **Configuration:**
   - Update `src-tauri/tauri.conf.json`
   - Restart dev server

### Testing Your Changes

#### Run All Tests

```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Property-based tests
pytest tests/property/

# Performance tests
pytest tests/performance/
```

#### Run Specific Test Suites

```bash
# Frontend-backend communication
pytest tests/integration/test_frontend_backend_communication.py

# Audio properties
pytest tests/property/test_audio_properties.py

# Error handling
pytest tests/unit/test_error_handling.py
```

#### Frontend Tests

```bash
cd frontend
npm run test
```

#### Tauri Tests

```bash
cd backend-tauri
cargo test
```

### Code Quality Checks

#### Python

```bash
# Linting
flake8 backend/ tests/

# Type checking
mypy backend/

# Format checking
black --check backend/ tests/
```

#### TypeScript

```bash
cd frontend

# Linting
npm run lint

# Type checking
npm run type-check

# Format checking
npm run format:check
```

#### Rust

```bash
cd backend-tauri

# Linting
cargo clippy

# Format checking
cargo fmt --check
```

### Building for Production

#### Development Build

```bash
./dev.sh build
```

#### Production Build

```bash
# Full production build
npm run tauri build

# Platform-specific builds
npm run tauri build -- --target x86_64-pc-windows-msvc  # Windows
npm run tauri build -- --target x86_64-apple-darwin     # macOS Intel
npm run tauri build -- --target aarch64-apple-darwin    # macOS Apple Silicon
```

Build artifacts are located in:
- `src-tauri/target/release/bundle/`

---

## Debugging Tips

### General Debugging Strategy

1. **Identify the Layer:** Determine if the issue is in frontend, Tauri, or backend
2. **Check Logs:** Review logs from all three layers
3. **Isolate the Problem:** Test each layer independently
4. **Use Debugging Tools:** Leverage browser DevTools, Rust debugger, Python debugger

### Frontend Debugging

#### Browser DevTools

1. **Open DevTools:**
   - In Tauri app: Right-click → Inspect Element
   - Or press `Cmd+Option+I` (macOS) / `Ctrl+Shift+I` (Windows/Linux)

2. **Console Tab:**
   - View JavaScript errors and console.log output
   - Check for Tauri command errors

3. **Network Tab:**
   - Monitor IPC communication (appears as internal requests)
   - Check for failed requests

4. **React DevTools:**
   - Install React DevTools browser extension
   - Inspect component hierarchy and state

#### Common Frontend Issues

**Issue: Tauri commands not working**
```typescript
// Check if running in Tauri context
import { invoke } from '@tauri-apps/api/tauri';

try {
  const result = await invoke('command_name', { param: value });
  console.log('Success:', result);
} catch (error) {
  console.error('Tauri command failed:', error);
}
```

**Issue: State not updating**
```typescript
// Check Zustand store
import { useAppStore } from './store/appStore';

// In component
const state = useAppStore();
console.log('Current state:', state);
```

**Issue: Events not received**
```typescript
// Verify event listener
import { listen } from '@tauri-apps/api/event';

const unlisten = await listen('event-name', (event) => {
  console.log('Event received:', event.payload);
});

// Don't forget to unlisten on cleanup
return () => unlisten();
```

### Backend Debugging

#### Python Debugger

1. **Using pdb:**
   ```python
   import pdb; pdb.set_trace()
   ```

2. **Using VS Code:**
   - Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Python: Backend Service",
         "type": "python",
         "request": "launch",
         "program": "${workspaceFolder}/backend/backend_service.py",
         "console": "integratedTerminal"
       }
     ]
   }
   ```

#### Logging

Enable debug logging:

```python
# In backend/backend_service.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check log files:
```bash
tail -f logs/deepecho.log
tail -f logs/transcription.log
```

#### Common Backend Issues

**Issue: IPC server not starting**
```bash
# Check if port is already in use
# On macOS/Linux:
lsof -i :8765

# On Windows:
netstat -ano | findstr :8765
```

**Issue: Audio device not found**
```python
# List available devices
python -c "import speech_recognition as sr; print(sr.Microphone.list_microphone_names())"
```

**Issue: AI provider errors**
```python
# Test provider directly
python -c "from backend.ai.adapter import AIAdapter; adapter = AIAdapter(); print(adapter.get_response('test'))"
```

### Tauri Debugging

#### Rust Debugging

1. **Print Debugging:**
   ```rust
   println!("Debug: {:?}", variable);
   eprintln!("Error: {:?}", error);
   ```

2. **Using rust-lldb (macOS/Linux):**
   ```bash
   rust-lldb target/debug/deepecho
   ```

3. **Using VS Code:**
   - Install "CodeLLDB" extension
   - Create `.vscode/launch.json`:
   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "type": "lldb",
         "request": "launch",
         "name": "Debug Tauri",
         "cargo": {
           "args": ["build", "--manifest-path=backend-tauri/Cargo.toml"]
         }
       }
     ]
   }
   ```

#### Tauri Logs

Check Tauri console output:
```bash
# Run with verbose logging
RUST_LOG=debug cargo tauri dev
```

#### Common Tauri Issues

**Issue: Command not found**
```rust
// Verify command is registered in main.rs
tauri::Builder::default()
  .invoke_handler(tauri::generate_handler![
    your_command_name
  ])
```

**Issue: IPC communication failure**
```rust
// Check error handling
#[tauri::command]
async fn my_command() -> Result<String, String> {
  match some_operation() {
    Ok(result) => Ok(result),
    Err(e) => {
      eprintln!("Error: {:?}", e);
      Err(format!("Operation failed: {}", e))
    }
  }
}
```

### Cross-Layer Debugging

#### Trace Request Flow

1. **Frontend → Tauri:**
   ```typescript
   console.log('Calling command:', commandName, params);
   const result = await invoke(commandName, params);
   console.log('Command result:', result);
   ```

2. **Tauri → Backend:**
   ```rust
   println!("Forwarding to backend: {:?}", request);
   let response = forward_to_backend(request).await;
   println!("Backend response: {:?}", response);
   ```

3. **Backend Processing:**
   ```python
   logger.debug(f"Received request: {request}")
   result = process_request(request)
   logger.debug(f"Sending response: {result}")
   ```

#### Network Debugging

Monitor IPC communication:

```bash
# On macOS/Linux:
sudo tcpdump -i lo0 -A port 8765

# On Windows:
# Use Wireshark with loopback adapter
```

### Performance Debugging

#### Frontend Performance

```typescript
// Measure render time
console.time('component-render');
// ... component code
console.timeEnd('component-render');

// Profile with React DevTools Profiler
import { Profiler } from 'react';

<Profiler id="MyComponent" onRender={onRenderCallback}>
  <MyComponent />
</Profiler>
```

#### Backend Performance

```python
import time

start = time.time()
# ... operation
elapsed = time.time() - start
logger.info(f"Operation took {elapsed:.2f}s")
```

#### Memory Profiling

```bash
# Python memory profiling
pip install memory_profiler
python -m memory_profiler backend/backend_service.py
```

---

## Common Issues and Solutions

### Installation Issues

#### Issue: Rust compilation fails

**Solution:**
```bash
# Update Rust
rustup update

# Clean and rebuild
cd backend-tauri
cargo clean
cargo build
```

#### Issue: Python dependencies fail to install

**Solution:**
```bash
# Upgrade pip
pip install --upgrade pip

# Install with verbose output
pip install -r requirements.txt -v

# On Windows, install Visual C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### Issue: Node modules installation fails

**Solution:**
```bash
cd frontend

# Clear cache
npm cache clean --force

# Remove node_modules
rm -rf node_modules package-lock.json

# Reinstall
npm install
```

### Runtime Issues

#### Issue: Application won't start

**Checklist:**
1. Is Python backend running? Check `ps aux | grep backend_service`
2. Are ports available? Check `lsof -i :8765`
3. Are API keys configured? Check `keys.py`
4. Is config valid? Check `resources/config.json`

#### Issue: Audio not capturing

**Windows:**
```bash
# Check WASAPI loopback device
python -c "import pyaudiowpatch as pyaudio; p = pyaudio.PyAudio(); print([p.get_device_info_by_index(i) for i in range(p.get_device_count())])"
```

**macOS:**
```bash
# Check BlackHole installation
brew list blackhole-2ch

# Verify audio routing in System Preferences → Sound
```

#### Issue: AI responses not generating

**Solution:**

```python
# Test AI provider
python - c
"
from backend.ai.adapter import AIAdapter

adapter = AIAdapter()
adapter.switch_provider('openai')  # or your provider
response = adapter.get_response('Hello')
print(response)
"
```

### Build Issues

#### Issue: Tauri build fails

**Solution:**
```bash
# Check Tauri configuration
cat backend-tauri/tauri.conf.json

# Verify all dependencies
cargo check

# Build with verbose output
cargo build --verbose
```

#### Issue: Frontend build fails

**Solution:**
```bash
cd frontend

# Check TypeScript errors
npm run type-check

# Build with verbose output
npm run build -- --verbose
```

---

## Best Practices

### Code Organization

1. **Frontend:**
   - Keep components small and focused
   - Use custom hooks for reusable logic
   - Separate business logic from UI
   - Use TypeScript strictly (no `any` types)

2. **Backend:**
   - Follow Python PEP 8 style guide
   - Use type hints
   - Keep functions pure when possible
   - Handle errors explicitly

3. **Tauri:**
   - Keep commands simple and focused
   - Use proper error types
   - Document command parameters
   - Follow Rust conventions

### Git Workflow

1. **Branch Naming:**
   ```
   feature/add-new-component
   fix/audio-capture-bug
   refactor/improve-performance
   ```

2. **Commit Messages:**
   ```
   feat: Add audio visualization component
   fix: Resolve IPC timeout issue
   refactor: Simplify state management
   docs: Update development guide
   ```

3. **Before Committing:**
   ```bash
   # Run tests
   pytest tests/
   
   # Check code quality
   npm run lint
   cargo clippy
   
   # Format code
   black backend/ tests/
   npm run format
   cargo fmt
   ```

### Testing Strategy

1. **Write tests first** (TDD when possible)
2. **Test at appropriate level:**
   - Unit tests for pure functions
   - Integration tests for workflows
   - Property tests for invariants
3. **Mock external dependencies**
4. **Keep tests fast and focused**

### Performance Optimization

1. **Frontend:**
   - Use React.memo for expensive components
   - Implement virtual scrolling for large lists
   - Debounce user input
   - Lazy load components

2. **Backend:**
   - Use async/await for I/O operations
   - Implement caching where appropriate
   - Profile before optimizing
   - Monitor memory usage

3. **IPC:**
   - Batch events when possible
   - Use efficient serialization
   - Implement request throttling
   - Handle backpressure

### Security Considerations

1. **API Keys:**
   - Never commit `keys.py`
   - Use environment variables in production
   - Rotate keys regularly

2. **File Access:**
   - Validate all file paths
   - Use Tauri's file system API
   - Implement proper permissions

3. **Input Validation:**
   - Validate all user input
   - Sanitize data before processing
   - Use type checking

### Documentation

1. **Code Comments:**
   - Explain "why", not "what"
   - Document complex algorithms
   - Keep comments up to date

2. **API Documentation:**
   - Document all public functions
   - Include examples
   - Specify error conditions

3. **Architecture Decisions:**
   - Document major decisions
   - Explain trade-offs
   - Update when changes occur

---

## Additional Resources

### Official Documentation

- [Tauri Documentation](https://tauri.app/v1/guides/)
- [React Documentation](https://react.dev/)
- [Material-UI Documentation](https://mui.com/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Python Documentation](https://docs.python.org/3/)

### Project Documentation

- [Architecture Overview](./architecture.md)
- [API Reference](./api.md)
- [Protocol Specification](./protocol.md)
- [Deployment Guide](./deployment.md)

### Community

- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas
- Contributing: See CONTRIBUTING.md for guidelines

---

## Getting Help

If you encounter issues not covered in this guide:

1. **Check existing documentation** in the `docs/` directory
2. **Search GitHub issues** for similar problems
3. **Run diagnostic scripts:**
   ```bash
   ./dev.sh check
   python check_system.py
   ```
4. **Enable debug logging** and review logs
5. **Create a GitHub issue** with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages and logs
   - System information (OS, versions)

---

**Last Updated:** January 2026
**Version:** 1.0.0
