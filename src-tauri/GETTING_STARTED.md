# Getting Started with Tauri Development

This guide will walk you through setting up and running the Tauri layer for DeepEcho.

## Quick Start

### 1. Check Your Environment

Run the setup check script for your platform:

**macOS/Linux:**
```bash
./backend-tauri/check_setup.sh
```

**Windows:**
```cmd
src-tauri\check_setup.bat
```

### 2. Install Missing Dependencies

If the check script reports missing dependencies, follow the instructions in [SETUP.md](./SETUP.md).

### 3. Build the Project

Once all dependencies are installed:

```bash
cd backend-tauri
cargo build
```

The first build will take 10-15 minutes as Cargo downloads and compiles all dependencies.

### 4. Run in Development Mode

After the frontend is set up (Task 3), you can run the full application:

```bash
# From project root
cargo tauri dev
```

## Project Structure

```
src-tauri/
├── src/
│   ├── main.rs              # Application entry point
│   ├── lib.rs               # Library exports
│   └── models/              # Data models
│       ├── mod.rs
│       ├── request.rs       # Request types
│       ├── response.rs      # Response types
│       └── event.rs         # Event types
├── Cargo.toml               # Rust dependencies
├── tauri.conf.json          # Tauri configuration
├── build.rs                 # Build script
├── SETUP.md                 # Detailed setup instructions
├── GETTING_STARTED.md       # This file
└── README.md                # Project overview
```

## Configuration

### tauri.conf.json

Key configuration sections:

- **build**: Frontend build commands and paths
- **package**: Application metadata
- **tauri.allowlist**: Security permissions
- **tauri.bundle**: Application bundling settings
- **tauri.windows**: Window configuration

### Cargo.toml

Rust dependencies and build settings. Key dependencies:

- `tauri`: Core framework
- `serde`: Serialization
- `tokio`: Async runtime

## Development Workflow

### Adding New Commands

1. Define the command function in `src/main.rs`:
   ```rust
   #[tauri::command]
   fn my_command(param: String) -> Result<String, String> {
       // Implementation
       Ok("Success".to_string())
   }
   ```

2. Register it in the `invoke_handler`:
   ```rust
   .invoke_handler(tauri::generate_handler![
       greet,
       my_command,  // Add here
   ])
   ```

3. Call from frontend:
   ```typescript
   import { invoke } from '@tauri-apps/api/tauri';
   const result = await invoke('my_command', { param: 'value' });
   ```

### Emitting Events

From Rust:
```rust
use tauri::Manager;

app.emit_all("event-name", payload)?;
```

From frontend:
```typescript
import { listen } from '@tauri-apps/api/event';

await listen('event-name', (event) => {
    console.log('Received:', event.payload);
});
```

## Testing

### Run Tests

```bash
cargo test
```

### Run with Logging

```bash
RUST_LOG=debug cargo tauri dev
```

## Building for Production

### Development Build

```bash
cargo build
```

### Release Build

```bash
cargo build --release
```

### Create Installer

```bash
cargo tauri build
```

Installers will be created in `src-tauri/target/release/bundle/`.

## Platform-Specific Notes

### macOS

- Requires Xcode Command Line Tools
- First run may prompt for permissions
- Code signing required for distribution

### Windows

- Requires Microsoft C++ Build Tools
- Requires WebView2 Runtime
- May need to run as administrator for first build

## Troubleshooting

### Build Fails

1. Update Rust: `rustup update`
2. Clean build: `cargo clean && cargo build`
3. Check SETUP.md for platform requirements

### Runtime Errors

1. Check console output: `RUST_LOG=debug cargo tauri dev`
2. Verify frontend is running on correct port (5173)
3. Check tauri.conf.json configuration

### Performance Issues

1. Use release builds for testing: `cargo build --release`
2. Check system resources
3. Review async operations in code

## Next Steps

1. Complete Task 3: Initialize React frontend
2. Implement Tauri commands (Task 11)
3. Set up IPC communication (Task 12)
4. Test end-to-end integration

## Resources

- [Tauri Documentation](https://tauri.app/)
- [Rust Book](https://doc.rust-lang.org/book/)
- [Tauri API Reference](https://tauri.app/v1/api/js/)
- [Project README](./README.md)

## Support

For issues specific to this project, refer to the main project documentation or create an issue in the repository.
