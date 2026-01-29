# DeepEcho Deployment Guide

## Overview

This comprehensive guide covers the complete deployment process for DeepEcho, including building, configuration, distribution, and troubleshooting. Whether you're deploying for internal use or public distribution, this guide will walk you through each step.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Build Process](#build-process)
3. [Configuration Management](#configuration-management)
4. [Platform-Specific Deployment](#platform-specific-deployment)
5. [Code Signing and Notarization](#code-signing-and-notarization)
6. [Distribution Methods](#distribution-methods)
7. [Auto-Update Setup](#auto-update-setup)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Security Considerations](#security-considerations)
10. [Troubleshooting](#troubleshooting)
11. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

Before deploying DeepEcho to production, ensure all items are completed:

### Code Quality
- [ ] All tests passing (unit, integration, property-based)
- [ ] Code review completed
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks met
- [ ] Memory leaks checked and resolved

### Configuration
- [ ] API keys configured (not hardcoded)
- [ ] Production configuration file created
- [ ] Environment variables documented
- [ ] Logging levels set appropriately
- [ ] Error tracking configured

### Documentation
- [ ] User documentation updated
- [ ] API documentation current
- [ ] Changelog prepared
- [ ] Known issues documented
- [ ] Migration guide (if applicable)

### Testing
- [ ] Tested on target platforms (Windows, macOS)
- [ ] Audio capture verified on all platforms
- [ ] AI providers tested
- [ ] Performance tested under load
- [ ] Edge cases validated

### Legal and Compliance
- [ ] License files included
- [ ] Third-party licenses documented
- [ ] Privacy policy updated
- [ ] Terms of service reviewed
- [ ] GDPR compliance verified (if applicable)

---


## Build Process

### Prerequisites

Ensure all development dependencies are installed and configured:

#### Required Software

1. **Node.js and npm**
   - Version: Node.js 18+ and npm 9+
   - Verify: `node --version && npm --version`

2. **Rust and Cargo**
   - Version: Rust 1.70+
   - Verify: `rustc --version && cargo --version`

3. **Python**
   - Version: Python 3.8+
   - Verify: `python --version && pip --version`

4. **Tauri CLI**
   - Install: `npm install -g @tauri-apps/cli`
   - Verify: `cargo tauri --version`

#### Platform-Specific Requirements

**Windows:**
- Visual Studio Build Tools 2019 or later
- WebView2 Runtime (pre-installed on Windows 10/11)
- WiX Toolset v3.11+ (for MSI installer)
  - Download: https://wixtoolset.org/releases/
  - Add to PATH after installation

**macOS:**
- Xcode Command Line Tools: `xcode-select --install`
- Apple Developer account (for code signing and notarization)
- Valid Developer ID Application certificate

**Linux:**
- Build essentials and GTK development libraries
  ```bash
  sudo apt-get install -y libwebkit2gtk-4.0-dev \
    build-essential curl wget libssl-dev \
    libgtk-3-dev libayatana-appindicator3-dev \
    librsvg2-dev
  ```

### Environment Setup

1. **Clone and Navigate to Repository**
   ```bash
   git clone <repository-url>
   cd deepecho
   ```

2. **Install Dependencies**
   ```bash
   # Backend dependencies
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   
   # Frontend dependencies
   cd frontend
   npm install
   cd ..
   
   # Tauri dependencies
   cd backend-tauri
   cargo build --release
   cd ..
   ```

3. **Configure for Production**
   ```bash
   # Copy production configuration
   cp resources/config.example.json resources/config.production.json
   
   # Edit configuration (see Configuration Management section)
   # DO NOT commit API keys or secrets
   ```

### Production Build

#### Full Production Build

Build for all supported platforms:

```bash
# Build optimized production bundle
npm run tauri build
```

This command will:
1. Build optimized frontend bundle (minified, tree-shaken)
2. Compile Rust code in release mode with optimizations
3. Bundle Python backend with dependencies
4. Create platform-specific installers and packages

#### Build Output Locations

**Windows:**
- MSI Installer: `src-tauri/target/release/bundle/msi/DeepEcho_1.0.0_x64_en-US.msi`
- NSIS Installer: `src-tauri/target/release/bundle/nsis/DeepEcho_1.0.0_x64-setup.exe`
- Portable: `src-tauri/target/release/DeepEcho.exe`

**macOS:**
- DMG Image: `src-tauri/target/release/bundle/dmg/DeepEcho_1.0.0_x64.dmg`
- App Bundle: `src-tauri/target/release/bundle/macos/DeepEcho.app`
- Universal Binary: `src-tauri/target/release/bundle/macos/DeepEcho_universal.app`

**Linux:**
- Debian Package: `src-tauri/target/release/bundle/deb/deepecho_1.0.0_amd64.deb`
- AppImage: `src-tauri/target/release/bundle/appimage/DeepEcho_1.0.0_amd64.AppImage`
- RPM Package: `src-tauri/target/release/bundle/rpm/deepecho-1.0.0-1.x86_64.rpm`

### Build Optimization

#### Rust Optimization

Configure in `src-tauri/Cargo.toml`:

```toml
[profile.release]
opt-level = "z"        # Optimize for size
lto = true             # Enable Link Time Optimization
codegen-units = 1      # Better optimization, slower compile
strip = true           # Strip debug symbols
panic = "abort"        # Smaller binary size
```

#### Frontend Optimization

Configure in `frontend/vite.config.ts`:

```typescript
export default defineConfig({
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log in production
        drop_debugger: true
      }
    },
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          mui: ['@mui/material', '@mui/icons-material']
        }
      }
    }
  }
});
```

#### Python Optimization

```bash
# Compile Python files to bytecode
python -m compileall backend/

# Remove unnecessary files from distribution
find backend/ -name "*.pyc" -delete
find backend/ -name "__pycache__" -type d -delete
find backend/ -name "*.py[cod]" -delete
```

### Build Verification

After building, verify the output:

```bash
# Check file sizes
ls -lh backend-tauri/target/release/bundle/

# Test the built application
# Windows
./backend-tauri/target/release/DeepEcho.exe

# macOS
open backend-tauri/target/release/bundle/macos/DeepEcho.app

# Linux
./backend-tauri/target/release/deepecho
```

### Build Troubleshooting

**Issue: Build fails with "out of memory"**
```bash
# Increase Node.js memory limit
export NODE_OPTIONS="--max-old-space-size=4096"
npm run tauri build
```

**Issue: Rust compilation errors**
```bash
# Clean and rebuild
cd backend-tauri
cargo clean
cargo build --release
cd ..
```

**Issue: Frontend build fails**
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
cd ..
```

---


## Configuration Management

### Configuration Files

DeepEcho uses multiple configuration files for different aspects:

#### 1. Application Configuration (`resources/config.json`)

Main application settings:

```json
{
  "audio": {
    "use_api_mode": true,
    "record_timeout": 3,
    "energy_threshold": 1000,
    "phrase_threshold": 0.3,
    "dynamic_energy_threshold": true,
    "device_index": null
  },
  "ai_provider": {
    "provider_type": "deepseek",
    "model": "deepseek-chat",
    "response_interval": 5,
    "max_tokens": 2000,
    "temperature": 0.7
  },
  "ui": {
    "theme": "dark",
    "update_interval": 3,
    "show_confidence": true,
    "auto_scroll": true
  },
  "logging": {
    "level": "INFO",
    "file": "logs/deepecho.log",
    "max_size": 10485760,
    "backup_count": 5
  },
  "performance": {
    "max_queue_size": 100,
    "worker_threads": 4,
    "enable_caching": true
  }
}
```

#### 2. API Keys Configuration (`keys.py`)

**CRITICAL: Never commit this file to version control!**

```python
# keys.py - Production configuration
OPENAI_API_KEY = "sk-..."
ANTHROPIC_API_KEY = "sk-ant-..."
DEEPSEEK_API_KEY = "sk-..."
ZHIPUAI_API_KEY = "..."
GROK_API_KEY = "xai-..."
VOLCANO_API_KEY = "..."

# Optional: Use environment variables in production
import os
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', OPENAI_API_KEY)
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', ANTHROPIC_API_KEY)
# ... etc
```

#### 3. Tauri Configuration (`src-tauri/tauri.conf.json`)

Application metadata and build settings:

```json
{
  "package": {
    "productName": "DeepEcho",
    "version": "1.0.0"
  },
  "tauri": {
    "allowlist": {
      "all": false,
      "shell": {
        "all": false,
        "open": true
      },
      "fs": {
        "all": false,
        "readFile": true,
        "writeFile": true,
        "readDir": true,
        "scope": ["$APPDATA/*", "$RESOURCE/*"]
      }
    },
    "bundle": {
      "active": true,
      "identifier": "com.deepecho.app",
      "icon": [
        "icons/32x32.png",
        "icons/128x128.png",
        "icons/128x128@2x.png",
        "icons/icon.png"
      ],
      "resources": ["resources/*"],
      "externalBin": ["binaries/python-backend"],
      "copyright": "Copyright © 2026 DeepEcho",
      "category": "Productivity",
      "shortDescription": "Real-time AI voice assistant",
      "longDescription": "DeepEcho is a real-time voice AI assistant with transcription and response generation capabilities."
    },
    "security": {
      "csp": "default-backend 'self'; script-backend 'self' 'unsafe-inline'; style-backend 'self' 'unsafe-inline'"
    },
    "updater": {
      "active": false
    },
    "windows": [
      {
        "title": "DeepEcho",
        "width": 1200,
        "height": 800,
        "resizable": true,
        "fullscreen": false
      }
    ]
  }
}
```

### Environment-Specific Configuration

#### Development Configuration

```json
{
  "audio": {
    "record_timeout": 5,
    "energy_threshold": 300
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

#### Production Configuration

```json
{
  "audio": {
    "record_timeout": 3,
    "energy_threshold": 1000
  },
  "logging": {
    "level": "INFO"
  },
  "performance": {
    "enable_caching": true
  }
}
```

#### Staging Configuration

```json
{
  "audio": {
    "record_timeout": 3,
    "energy_threshold": 800
  },
  "logging": {
    "level": "DEBUG"
  }
}
```

### Environment Variables

Set these environment variables for production deployment:

```bash
# API Keys (REQUIRED)
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export DEEPSEEK_API_KEY="sk-..."

# Application Environment
export NODE_ENV="production"
export RUST_LOG="info"
export PYTHONPATH="./src"

# Optional: Custom configuration path
export DEEPECHO_CONFIG_PATH="/path/to/config.json"

# Optional: Logging configuration
export DEEPECHO_LOG_LEVEL="INFO"
export DEEPECHO_LOG_FILE="/var/log/deepecho/app.log"

# Optional: Performance tuning
export DEEPECHO_MAX_WORKERS="4"
export DEEPECHO_CACHE_SIZE="1000"
```

### Configuration Loading Priority

DeepEcho loads configuration in this order (later overrides earlier):

1. Default configuration (hardcoded)
2. Configuration file (`resources/config.json`)
3. Environment-specific file (`resources/config.production.json`)
4. Environment variables
5. Command-line arguments (if applicable)

### Secrets Management

#### For Development

Use `keys.py` file (not committed to git):

```python
# keys.py
OPENAI_API_KEY = "sk-dev-key"
```

#### For Production

**Option 1: Environment Variables (Recommended)**

```bash
# Set in deployment environment
export OPENAI_API_KEY="sk-prod-key"
```

**Option 2: Secrets Management Service**

```python
# Use AWS Secrets Manager, Azure Key Vault, etc.
import boto3

def get_secret(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

OPENAI_API_KEY = get_secret('deepecho/openai-key')
```

**Option 3: Encrypted Configuration File**

```bash
# Encrypt configuration
openssl enc -aes-256-cbc -salt -in keys.py -out keys.py.enc

# Decrypt at runtime
openssl enc -aes-256-cbc -d -in keys.py.enc -out keys.py
```

### Configuration Validation

Validate configuration before deployment:

```python
# backend/config/validator.py
def validate_config(config):
    """Validate configuration before use."""
    required_keys = ['audio', 'ai_provider', 'ui']
    
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    
    # Validate audio settings
    if config['audio']['record_timeout'] < 1:
        raise ValueError("record_timeout must be >= 1")
    
    # Validate AI provider
    valid_providers = ['openai', 'anthropic', 'deepseek']
    if config['ai_provider']['provider_type'] not in valid_providers:
        raise ValueError(f"Invalid provider: {config['ai_provider']['provider_type']}")
    
    return True
```

Run validation:

```bash
python -c "from src.config.validator import validate_config; import json; validate_config(json.load(open('resources/config.json')))"
```

### Configuration Best Practices

1. **Never commit secrets** - Use `.gitignore` for `keys.py`
2. **Use environment variables** - For production deployments
3. **Validate on startup** - Fail fast if configuration is invalid
4. **Document all options** - Keep configuration schema documented
5. **Version configuration** - Track configuration changes
6. **Separate by environment** - Different configs for dev/staging/prod
7. **Encrypt sensitive data** - Use encryption for stored secrets
8. **Rotate keys regularly** - Implement key rotation policy
9. **Audit configuration changes** - Log who changed what and when
10. **Test configuration** - Validate before deploying

---

## Platform-Specific Deployment

### Windows Deployment

#### Build for Windows

```bash
# Build for Windows x64
cargo tauri build --target x86_64-pc-windows-msvc

# Build for Windows ARM64 (if needed)
cargo tauri build --target aarch64-pc-windows-msvc
```

#### Windows-Specific Requirements

1. **Visual Studio Build Tools 2019+**
   - Download: https://visualstudio.microsoft.com/downloads/
   - Required components: C++ build tools, Windows 10 SDK

2. **WiX Toolset v3.11+** (for MSI installer)
   - Download: https://wixtoolset.org/releases/
   - Add to PATH: `C:\Program Files (x86)\WiX Toolset v3.11\bin`

3. **WebView2 Runtime**
   - Pre-installed on Windows 10/11
   - Download standalone: https://developer.microsoft.com/microsoft-edge/webview2/

#### Windows Audio Configuration

DeepEcho uses PyAudioWPatch for WASAPI loopback on Windows:

```python
# Verify WASAPI loopback device
import pyaudiowpatch as pyaudio

p = pyaudio.PyAudio()
wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])

if default_speakers["isLoopbackDevice"]:
    print("Loopback device available")
```

#### Windows Installer Options

**MSI Installer (Recommended for Enterprise)**
- Location: `src-tauri/target/release/bundle/msi/`
- Features: Silent install, Group Policy deployment
- Install command: `msiexec /i DeepEcho.msi /quiet`

**NSIS Installer (Recommended for End Users)**
- Location: `src-tauri/target/release/bundle/nsis/`
- Features: Custom UI, user-friendly
- Supports: Per-user and per-machine installation

**Portable Executable**
- Location: `src-tauri/target/release/DeepEcho.exe`
- No installation required
- Useful for testing and USB deployment

#### Windows Deployment Checklist

- [ ] Code signed with valid certificate
- [ ] Tested on Windows 10 and Windows 11
- [ ] Audio capture working (microphone and speakers)
- [ ] Installer tested (both MSI and NSIS)
- [ ] Uninstaller tested
- [ ] Windows Defender exclusions documented (if needed)
- [ ] Firewall rules documented (if needed)

### macOS Deployment

#### Build for macOS

```bash
# Build for macOS Intel (x86_64)
cargo tauri build --target x86_64-apple-darwin

# Build for macOS Apple Silicon (ARM64)
cargo tauri build --target aarch64-apple-darwin

# Build Universal Binary (recommended)
cargo tauri build --target universal-apple-darwin
```

#### macOS-Specific Requirements

1. **Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

2. **Apple Developer Account**
   - Required for code signing and notarization
   - Enroll at: https://developer.apple.com/programs/

3. **Developer ID Application Certificate**
   - Download from Apple Developer portal
   - Install in Keychain Access

4. **BlackHole Virtual Audio Device** (for speaker capture)
   ```bash
   brew install blackhole-2ch
   ```

#### macOS Audio Configuration

Configure audio routing for speaker capture:

1. Open **Audio MIDI Setup** (Applications → Utilities)
2. Click **+** → Create Multi-Output Device
3. Select: Built-in Output + BlackHole 2ch
4. Set as default output in System Preferences → Sound

Verify in DeepEcho:
```python
# Check BlackHole device
import speech_recognition as sr
devices = sr.Microphone.list_microphone_names()
blackhole = [d for d in devices if 'BlackHole' in d]
print(f"BlackHole devices: {blackhole}")
```

#### macOS Bundle Options

**DMG Image (Recommended)**
- Location: `src-tauri/target/release/bundle/dmg/`
- User-friendly drag-and-drop installation
- Can include custom background and layout

**App Bundle**
- Location: `src-tauri/target/release/bundle/macos/DeepEcho.app`
- Can be distributed directly
- Must be code signed and notarized

#### macOS Deployment Checklist

- [ ] Code signed with Developer ID certificate
- [ ] Notarized by Apple
- [ ] Tested on macOS 11+ (Big Sur and later)
- [ ] Tested on both Intel and Apple Silicon
- [ ] Audio capture working with BlackHole
- [ ] DMG tested and opens correctly
- [ ] App launches without security warnings
- [ ] Gatekeeper verification passed

### Linux Deployment

#### Build for Linux

```bash
# Build for Linux x86_64
cargo tauri build --target x86_64-unknown-linux-gnu

# Build for Linux ARM64 (Raspberry Pi, etc.)
cargo tauri build --target aarch64-unknown-linux-gnu
```

#### Linux-Specific Requirements

**Debian/Ubuntu:**
```bash
sudo apt-get update
sudo apt-get install -y \
  libwebkit2gtk-4.0-dev \
  build-essential \
  curl \
  wget \
  libssl-dev \
  libgtk-3-dev \
  libayatana-appindicator3-dev \
  librsvg2-dev \
  libasound2-dev \
  portaudio19-dev
```

**Fedora/RHEL:**
```bash
sudo dnf install \
  webkit2gtk3-devel \
  openssl-devel \
  curl \
  wget \
  libappindicator-gtk3 \
  librsvg2-devel \
  alsa-lib-devel \
  portaudio-devel
```

**Arch Linux:**
```bash
sudo pacman -S \
  webkit2gtk \
  base-devel \
  curl \
  wget \
  openssl \
  appmenu-gtk-module \
  gtk3 \
  libappindicator-gtk3 \
  librsvg \
  alsa-lib \
  portaudio
```

#### Linux Audio Configuration

DeepEcho uses PulseAudio/PipeWire for audio capture:

```bash
# Check audio devices
pactl list sources short

# Set default source
pactl set-default-source <source-name>

# Monitor speaker output
pactl load-module module-loopback
```

#### Linux Package Options

**Debian Package (.deb)**
- Location: `src-tauri/target/release/bundle/deb/`
- Install: `sudo dpkg -i deepecho_1.0.0_amd64.deb`
- For: Debian, Ubuntu, Linux Mint, Pop!_OS

**RPM Package (.rpm)**
- Location: `src-tauri/target/release/bundle/rpm/`
- Install: `sudo rpm -i deepecho-1.0.0-1.x86_64.rpm`
- For: Fedora, RHEL, CentOS, openSUSE

**AppImage**
- Location: `src-tauri/target/release/bundle/appimage/`
- Run: `chmod +x DeepEcho.AppImage && ./DeepEcho.AppImage`
- Universal format, no installation required

#### Linux Deployment Checklist

- [ ] Tested on major distributions (Ubuntu, Fedora, Arch)
- [ ] Dependencies documented
- [ ] Audio capture working with PulseAudio/PipeWire
- [ ] Desktop entry file included
- [ ] Icon properly displayed
- [ ] Permissions configured correctly
- [ ] AppImage tested on multiple distributions

### Cross-Platform Considerations

#### File Paths

Use platform-agnostic path handling:

```rust
// Rust
use std::path::PathBuf;
let config_path = tauri::api::path::app_config_dir(&config)
    .unwrap()
    .join("config.json");
```

```typescript
// TypeScript
import { appConfigDir, join } from '@tauri-apps/api/path';
const configPath = await join(await appConfigDir(), 'config.json');
```

```python
# Python
from pathlib import Path
config_path = Path.home() / '.config' / 'deepecho' / 'config.json'
```

#### Platform Detection

```typescript
// Frontend
import { platform } from '@tauri-apps/api/os';
const platformName = await platform();
// Returns: 'win32', 'darwin', or 'linux'
```

```rust
// Rust
#[cfg(target_os = "windows")]
fn platform_specific() {
    // Windows-specific code
}

#[cfg(target_os = "macos")]
fn platform_specific() {
    // macOS-specific code
}

#[cfg(target_os = "linux")]
fn platform_specific() {
    // Linux-specific code
}
```

#### Audio Device Handling

Different platforms have different audio APIs:

- **Windows**: WASAPI loopback (PyAudioWPatch)
- **macOS**: BlackHole virtual device
- **Linux**: PulseAudio monitor sources

Ensure your code handles platform differences:

```python
import platform

def get_speaker_device():
    system = platform.system()
    
    if system == "Windows":
        return get_wasapi_loopback_device()
    elif system == "Darwin":  # macOS
        return get_blackhole_device()
    elif system == "Linux":
        return get_pulseaudio_monitor()
    else:
        raise NotImplementedError(f"Platform {system} not supported")
```

---


## Code Signing and Notarization

Code signing is essential for distributing applications without security warnings. It proves the application's authenticity and hasn't been tampered with.

### Windows Code Signing

#### Obtain a Code Signing Certificate

**Options:**
1. **Commercial Certificate Authority** (Recommended)
   - DigiCert, Sectigo, GlobalSign
   - Cost: $200-$500/year
   - Trusted by Windows immediately

2. **Self-Signed Certificate** (Development only)
   - Free but shows security warnings
   - Not recommended for distribution

#### Configure Code Signing

1. **Install Certificate**
   ```powershell
   # Import certificate to Windows Certificate Store
   certutil -user -p <password> -importPFX <certificate.pfx>
   ```

2. **Find Certificate Thumbprint**
   ```powershell
   # List certificates
   Get-ChildItem -Path Cert:\CurrentUser\My
   
   # Note the Thumbprint value
   ```

3. **Configure in `tauri.conf.json`**
   ```json
   {
     "tauri": {
       "bundle": {
         "windows": {
           "certificateThumbprint": "YOUR_CERTIFICATE_THUMBPRINT",
           "digestAlgorithm": "sha256",
           "timestampUrl": "http://timestamp.digicert.com"
         }
       }
     }
   }
   ```

4. **Build with Signing**
   ```bash
   npm run tauri build
   ```

#### Verify Signature

```powershell
# Verify digital signature
Get-AuthenticodeSignature .\DeepEcho.exe

# Should show: Status = Valid
```

#### Troubleshooting Windows Code Signing

**Issue: "Certificate not found"**
- Ensure certificate is in CurrentUser\My store
- Check thumbprint matches exactly (no spaces)

**Issue: "Timestamp server unavailable"**
- Try alternative timestamp servers:
  - `http://timestamp.comodoca.com`
  - `http://timestamp.globalsign.com/scripts/timstamp.dll`
  - `http://tsa.starfieldtech.com`

**Issue: "Invalid certificate"**
- Verify certificate is valid and not expired
- Ensure certificate is for code signing (not SSL)

### macOS Code Signing and Notarization

#### Prerequisites

1. **Apple Developer Account**
   - Enroll at: https://developer.apple.com/programs/
   - Cost: $99/year

2. **Developer ID Application Certificate**
   - Log in to Apple Developer portal
   - Go to Certificates, Identifiers & Profiles
   - Create new certificate: Developer ID Application
   - Download and install in Keychain Access

3. **App-Specific Password**
   - Go to appleid.apple.com
   - Sign in → Security → App-Specific Passwords
   - Generate new password for notarization

#### Configure Code Signing

1. **Find Signing Identity**
   ```bash
   # List available identities
   security find-identity -v -p codesigning
   
   # Look for "Developer ID Application: Your Name (TEAM_ID)"
   ```

2. **Configure in `tauri.conf.json`**
   ```json
   {
     "tauri": {
       "bundle": {
         "macOS": {
           "signingIdentity": "Developer ID Application: Your Name (TEAM_ID)",
           "entitlements": "entitlements.plist",
           "exceptionDomain": "",
           "providerShortName": "TEAM_ID"
         }
       }
     }
   }
   ```

3. **Create Entitlements File** (`src-tauri/entitlements.plist`)
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>com.apple.security.cs.allow-jit</key>
     <true/>
     <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
     <true/>
     <key>com.apple.security.cs.disable-library-validation</key>
     <true/>
     <key>com.apple.security.device.audio-input</key>
     <true/>
     <key>com.apple.security.network.client</key>
     <true/>
   </dict>
   </plist>
   ```

#### Build and Sign

```bash
# Build with signing
npm run tauri build

# Verify signature
codesign -dv --verbose=4 backend-tauri/target/release/bundle/macos/DeepEcho.app
```

#### Notarize the Application

Notarization is required for macOS 10.15+ (Catalina and later).

1. **Create Notarization Profile**
   ```bash
   xcrun notarytool store-credentials "DeepEcho-Profile" \
     --apple-id "your@email.com" \
     --team-id "TEAM_ID" \
     --password "app-specific-password"
   ```

2. **Zip the Application**
   ```bash
   cd backend-tauri/target/release/bundle/macos
   ditto -c -k --keepParent DeepEcho.app DeepEcho.zip
   ```

3. **Submit for Notarization**
   ```bash
   xcrun notarytool submit DeepEcho.zip \
     --keychain-profile "DeepEcho-Profile" \
     --wait
   ```

4. **Check Notarization Status**
   ```bash
   # Get submission ID from previous command
   xcrun notarytool info <submission-id> \
     --keychain-profile "DeepEcho-Profile"
   ```

5. **Staple Notarization Ticket**
   ```bash
   xcrun stapler staple DeepEcho.app
   
   # Verify stapling
   xcrun stapler validate DeepEcho.app
   ```

6. **Create DMG and Notarize**
   ```bash
   # DMG is automatically created by Tauri
   # Notarize the DMG
   xcrun notarytool submit DeepEcho.dmg \
     --keychain-profile "DeepEcho-Profile" \
     --wait
   
   # Staple to DMG
   xcrun stapler staple DeepEcho.dmg
   ```

#### Verify Notarization

```bash
# Check if app is notarized
spctl -a -vv -t install DeepEcho.app

# Should show: "accepted" and "source=Notarized Developer ID"
```

#### Troubleshooting macOS Code Signing

**Issue: "No identity found"**
```bash
# Refresh certificates
security find-identity -v -p codesigning

# If empty, download certificate from Apple Developer portal
```

**Issue: "Notarization failed"**
```bash
# Get detailed log
xcrun notarytool log <submission-id> \
  --keychain-profile "DeepEcho-Profile" \
  developer_log.json

# Review issues in developer_log.json
```

**Issue: "Gatekeeper blocks app"**
```bash
# Remove quarantine attribute (testing only)
xattr -cr DeepEcho.app

# For distribution, must be properly notarized
```

**Common Notarization Issues:**
- **Hardened Runtime**: Ensure entitlements are correct
- **Library Validation**: May need to disable for Python dependencies
- **Unsigned Binaries**: All binaries must be signed (including Python)

### Linux Code Signing

Linux doesn't have a centralized code signing system like Windows/macOS, but you can still sign packages:

#### Sign Debian Packages

```bash
# Generate GPG key (if you don't have one)
gpg --full-generate-key

# Sign the package
dpkg-sig --sign builder deepecho_1.0.0_amd64.deb

# Verify signature
dpkg-sig --verify deepecho_1.0.0_amd64.deb
```

#### Sign RPM Packages

```bash
# Import GPG key
rpm --import /path/to/public-key.asc

# Sign the package
rpm --addsign deepecho-1.0.0-1.x86_64.rpm

# Verify signature
rpm --checksig deepecho-1.0.0-1.x86_64.rpm
```

#### Sign AppImage

```bash
# Sign with GPG
gpg --detach-sign --armor DeepEcho.AppImage

# Creates DeepEcho.AppImage.asc
# Distribute both files together
```

### Code Signing Best Practices

1. **Protect Private Keys**
   - Store certificates securely
   - Use hardware security modules (HSM) for production
   - Never commit certificates to version control

2. **Use Timestamp Servers**
   - Ensures signature remains valid after certificate expires
   - Use reliable timestamp servers

3. **Verify Before Distribution**
   - Always verify signatures after signing
   - Test on clean systems

4. **Automate Signing**
   - Integrate into CI/CD pipeline
   - Use secure credential storage

5. **Document Process**
   - Keep signing procedures documented
   - Document certificate renewal process

6. **Plan for Certificate Renewal**
   - Certificates expire (typically 1-3 years)
   - Set reminders before expiration
   - Test renewal process in advance

---

```json
{
  "tauri": {
    "bundle": {
      "macOS": {
        "signingIdentity": "Developer ID Application: Your Name (TEAM_ID)",
        "entitlements": "entitlements.plist"
      }
    }
  }
}
```

3. Sign and notarize:

```bash
# Sign
codesign --deep --force --verify --verbose --sign "Developer ID" DeepEcho.app

# Notarize
xcrun notarytool submit DeepEcho.dmg --apple-id your@email.com --password app-specific-password --team-id TEAM_ID
```

## Distribution

### GitHub Releases

1. Create release tag:
```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

2. Upload build artifacts to GitHub Releases

3. Write release notes

### Auto-Update

Configure auto-update in `tauri.conf.json`:

```json
{
  "tauri": {
    "updater": {
      "active": true,
      "endpoints": [
        "https://releases.myapp.com/{{target}}/{{current_version}}"
      ],
      "dialog": true,
      "pubkey": "YOUR_PUBLIC_KEY"
    }
  }
}
```


## Configuration Management

### Production Configuration

Create production config file:

```json
{
  "audio": {
    "use_api_mode": true,
    "record_timeout": 3,
    "energy_threshold": 1000
  },
  "ai_provider": {
    "provider_type": "deepseek",
    "model": "deepseek-chat",
    "response_interval": 5
  },
  "ui": {
    "theme": "dark",
    "update_interval": 3
  }
}
```

### Environment Variables

Set production environment variables:

```bash
# API keys (never commit these)
export DEEPSEEK_API_KEY="sk-..."
export OPENAI_API_KEY="sk-..."

# Environment
export NODE_ENV="production"
export RUST_LOG="info"
```

## Monitoring

### Logging

Configure production logging:

```python
# backend/backend/utils/logger.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/production.log'),
        logging.StreamHandler()
    ]
)
```

### Error Tracking

Integrate error tracking service (e.g., Sentry):

```typescript
// frontend/src/main.tsx
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "YOUR_SENTRY_DSN",
  environment: "production"
});
```


## Performance Optimization

### Frontend Optimization

- Enable production build optimizations
- Use code splitting
- Lazy load components
- Optimize bundle size

### Backend Optimization

- Use production-grade WSGI server
- Enable caching
- Optimize database queries
- Use connection pooling

### Tauri Optimization

- Enable LTO (Link Time Optimization)
- Strip debug symbols
- Optimize binary size

```toml
# Cargo.toml
[profile.release]
lto = true
strip = true
opt-level = "z"
```

## Security Checklist

- [ ] API keys not hardcoded
- [ ] Code signed
- [ ] HTTPS enabled
- [ ] Input validation
- [ ] Error messages sanitized
- [ ] Dependencies updated
- [ ] Security audit passed

## Troubleshooting

### Build Failures

**Issue: Frontend build fails**
```bash
cd frontend
rm -rf node_modules dist
npm install
npm run build
```

**Issue: Rust build fails**
```bash
cd backend-tauri
cargo clean
cargo build --release
```

### Runtime Issues

Check logs:
- Frontend: Browser console
- Backend: `logs/production.log`
- Tauri: System logs

## Rollback Procedure

If deployment fails:

1. Revert to previous version
2. Restore configuration
3. Restart services
4. Verify functionality
5. Investigate issue

## Support

For deployment issues:
- Check documentation
- Review logs
- Contact support team
