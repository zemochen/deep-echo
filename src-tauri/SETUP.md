# Tauri Development Environment Setup

This guide will help you set up the Rust development environment required for the Tauri layer.

## Prerequisites

- macOS 10.13 or later (for macOS development)
- Windows 10 or later (for Windows development)
- At least 2GB of free disk space

## Step 1: Install Rust

### macOS

1. Open Terminal
2. Install Rust using rustup:
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   ```
3. Follow the on-screen instructions (press Enter to proceed with default installation)
4. After installation, restart your terminal or run:
   ```bash
   source $HOME/.cargo/env
   ```
5. Verify installation:
   ```bash
   rustc --version
   cargo --version
   ```

### Windows

1. Download and run rustup-init.exe from: https://rustup.rs/
2. Follow the installation wizard
3. Restart your terminal
4. Verify installation:
   ```cmd
   rustc --version
   cargo --version
   ```

## Step 2: Install Tauri Prerequisites

### macOS

Install Xcode Command Line Tools (if not already installed):
```bash
xcode-select --install
```

### Windows

Install Microsoft C++ Build Tools:
1. Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
2. Install "Desktop development with C++" workload

Install WebView2:
- Windows 11: Already included
- Windows 10: Download from https://developer.microsoft.com/en-us/microsoft-edge/webview2/

## Step 3: Install Tauri CLI

```bash
cargo install tauri-cli
```

This may take several minutes to compile.

## Step 4: Verify Setup

Navigate to the src-tauri directory and try building:

```bash
cd src-tauri
cargo build
```

If successful, you should see output indicating the build completed.

## Step 5: Development Workflow

### Run in Development Mode

From the project root:
```bash
cargo tauri dev
```

This will:
1. Start the frontend development server
2. Build the Rust backend
3. Launch the application window

### Build for Production

```bash
cargo tauri build
```

This creates optimized binaries in `src-tauri/target/release/`.

## Troubleshooting

### "rustc not found" error
- Make sure you've restarted your terminal after installing Rust
- Run `source $HOME/.cargo/env` (macOS/Linux) or restart terminal (Windows)

### Build errors on macOS
- Ensure Xcode Command Line Tools are installed: `xcode-select --install`
- Update Rust: `rustup update`

### Build errors on Windows
- Ensure Microsoft C++ Build Tools are installed
- Ensure WebView2 is installed
- Update Rust: `rustup update`

### Slow compilation
- First compilation is always slow (10-15 minutes)
- Subsequent builds are much faster due to caching
- Consider using `cargo build --release` only when needed

## Additional Resources

- Tauri Documentation: https://tauri.app/
- Rust Book: https://doc.rust-lang.org/book/
- Cargo Book: https://doc.rust-lang.org/cargo/

## Next Steps

After completing this setup:
1. Proceed to Task 3: Initialize React frontend project
2. Review the Tauri configuration in `tauri.conf.json`
3. Familiarize yourself with the project structure in `README.md`
