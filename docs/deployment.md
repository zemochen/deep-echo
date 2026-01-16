# DeepEcho Deployment Guide

## Overview

This guide covers building and deploying DeepEcho for production use.

## Build Process

### Prerequisites

- All development dependencies installed
- API keys configured
- Tests passing

### Production Build

```bash
# Build for production
npm run tauri build
```

This will:
1. Build optimized frontend bundle
2. Compile Rust code in release mode
3. Bundle Python backend
4. Create platform-specific installers

### Build Output

**Windows:**
- `src-tauri/target/release/bundle/msi/DeepEcho_1.0.0_x64.msi`
- `src-tauri/target/release/bundle/nsis/DeepEcho_1.0.0_x64-setup.exe`

**macOS:**
- `src-tauri/target/release/bundle/dmg/DeepEcho_1.0.0_x64.dmg`
- `src-tauri/target/release/bundle/macos/DeepEcho.app`

**Linux:**
- `src-tauri/target/release/bundle/deb/deepecho_1.0.0_amd64.deb`
- `src-tauri/target/release/bundle/appimage/DeepEcho_1.0.0_amd64.AppImage`

## Platform-Specific Builds

### Windows Build

```bash
# Build for Windows
cargo tauri build --target x86_64-pc-windows-msvc
```

Requirements:
- Visual Studio Build Tools
- WiX Toolset (for MSI installer)


### macOS Build

```bash
# Build for macOS Intel
cargo tauri build --target x86_64-apple-darwin

# Build for macOS Apple Silicon
cargo tauri build --target aarch64-apple-darwin

# Universal binary
cargo tauri build --target universal-apple-darwin
```

Requirements:
- Xcode Command Line Tools
- Apple Developer account (for code signing)

### Linux Build

```bash
# Build for Linux
cargo tauri build --target x86_64-unknown-linux-gnu
```

Requirements:
- Build essentials
- GTK development libraries

## Code Signing

### Windows Code Signing

1. Obtain code signing certificate
2. Configure in `tauri.conf.json`:

```json
{
  "tauri": {
    "bundle": {
      "windows": {
        "certificateThumbprint": "YOUR_THUMBPRINT",
        "digestAlgorithm": "sha256",
        "timestampUrl": "http://timestamp.digicert.com"
      }
    }
  }
}
```


### macOS Code Signing

1. Obtain Apple Developer certificate
2. Configure in `tauri.conf.json`:

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
# backend/src/utils/logger.py
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
cd src-tauri
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
