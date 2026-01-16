#!/bin/bash

# Script to check if Tauri development environment is properly set up

echo "==================================="
echo "Tauri Development Environment Check"
echo "==================================="
echo ""

# Check Rust
echo "Checking Rust installation..."
if command -v rustc &> /dev/null; then
    RUST_VERSION=$(rustc --version)
    echo "✓ Rust is installed: $RUST_VERSION"
else
    echo "✗ Rust is NOT installed"
    echo "  Please install from: https://rustup.rs/"
    exit 1
fi

# Check Cargo
echo ""
echo "Checking Cargo installation..."
if command -v cargo &> /dev/null; then
    CARGO_VERSION=$(cargo --version)
    echo "✓ Cargo is installed: $CARGO_VERSION"
else
    echo "✗ Cargo is NOT installed"
    echo "  Cargo should be installed with Rust"
    exit 1
fi

# Check platform-specific requirements
echo ""
echo "Checking platform-specific requirements..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Platform: macOS"
    if xcode-select -p &> /dev/null; then
        echo "✓ Xcode Command Line Tools are installed"
    else
        echo "✗ Xcode Command Line Tools are NOT installed"
        echo "  Run: xcode-select --install"
        exit 1
    fi
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "Platform: Windows"
    echo "⚠ Please ensure Microsoft C++ Build Tools and WebView2 are installed"
else
    echo "Platform: $OSTYPE"
    echo "⚠ Platform support may vary"
fi

# Check if Tauri CLI is installed
echo ""
echo "Checking Tauri CLI..."
if cargo tauri --version &> /dev/null; then
    TAURI_VERSION=$(cargo tauri --version)
    echo "✓ Tauri CLI is installed: $TAURI_VERSION"
else
    echo "✗ Tauri CLI is NOT installed"
    echo "  Install with: cargo install tauri-cli"
    echo "  (This may take several minutes)"
fi

echo ""
echo "==================================="
echo "Setup check complete!"
echo "==================================="
echo ""
echo "If all checks passed, you can proceed with:"
echo "  cd src-tauri"
echo "  cargo build"
