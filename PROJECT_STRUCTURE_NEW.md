# DeepEcho Project Structure

## Overview

This document describes the directory structure of the DeepEcho project after the frontend-backend separation refactoring.

## Root Directory

```
deepecho/
├── frontend/              # React + TypeScript frontend application
├── src-tauri/             # Tauri middleware layer (Rust)
├── backend/               # Python backend service
├── docs/                  # Project documentation
├── scripts/               # Build and deployment scripts (to be created)
├── .github/               # GitHub workflows and templates
├── .kiro/                 # Kiro specs and configuration
├── tests/                 # Legacy tests (to be migrated)
├── src/                   # Legacy source code (to be migrated)
├── resources/             # Configuration templates
├── logs/                  # Application logs
├── README.md              # Main project README
├── LICENSE                # MIT License
└── .gitignore             # Git ignore rules
```

## Frontend Directory

```
frontend/
├── src/
│   ├── components/        # React UI components
│   │   ├── TranscriptDisplay.tsx
│   │   ├── ResponseDisplay.tsx
│   │   ├── ControlPanel.tsx
│   │   ├── ProviderSelector.tsx
│   │   ├── StatusIndicator.tsx
│   │   ├── AudioDeviceSelector.tsx
│   │   └── AudioVisualizer.tsx
│   ├── hooks/             # Custom React hooks
│   │   ├── useAudioRecording.ts
│   │   ├── useTranscript.ts
│   │   ├── useResponse.ts
│   │   ├── useTauriCommand.ts
│   │   └── useAudioDevices.ts
│   ├── services/          # Service layer for API calls
│   │   ├── tauriService.ts
│   │   ├── audioService.ts
│   │   └── eventService.ts
│   ├── store/             # State management (Zustand)
│   │   ├── appStore.ts
│   │   └── uiStore.ts
│   ├── types/             # TypeScript type definitions
│   │   ├── api.ts
│   │   ├── audio.ts
│   │   └── ui.ts
│   ├── theme/             # Material-UI theme configuration
│   │   ├── theme.ts
│   │   └── colors.ts
│   ├── App.tsx            # Main application component
│   └── main.tsx           # Application entry point
├── public/                # Static assets
├── package.json           # NPM dependencies
├── tsconfig.json          # TypeScript configuration
├── vite.config.ts         # Vite build configuration
├── index.html             # HTML template
└── README.md              # Frontend documentation
```

## Tauri Directory

```
src-tauri/
├── src/
│   ├── commands/          # Tauri command handlers
│   │   ├── audio.rs       # Audio-related commands
│   │   ├── transcription.rs
│   │   ├── ai.rs          # AI-related commands
│   │   ├── config.rs      # Configuration commands
│   │   └── system.rs      # System information commands
│   ├── handlers/          # Core handler implementations
│   │   ├── ipc_handler.rs # IPC communication handler
│   │   ├── event_handler.rs
│   │   └── error_handler.rs
│   ├── services/          # Service layer
│   │   ├── python_service.rs  # Python subprocess management
│   │   ├── file_service.rs
│   │   └── system_service.rs
│   ├── models/            # Data models
│   │   ├── request.rs
│   │   ├── response.rs
│   │   └── event.rs
│   ├── lib.rs             # Library exports
│   └── main.rs            # Application entry point
├── Cargo.toml             # Rust dependencies
├── tauri.conf.json        # Tauri configuration
├── build.rs               # Build script
└── README.md              # Tauri documentation
```

## Backend Directory

```
backend/
├── src/
│   ├── audio/             # Audio processing (existing)
│   │   ├── recorder.py
│   │   ├── transcriber.py
│   │   └── models.py
│   ├── audio_system/      # Platform-specific audio (existing)
│   │   ├── audio_interface.py
│   │   ├── audio_factory.py
│   │   ├── windows_audio.py
│   │   └── macos_audio.py
│   ├── ai/                # AI providers (existing)
│   │   ├── adapter.py
│   │   ├── responder.py
│   │   └── providers/
│   ├── config/            # Configuration management (existing)
│   │   ├── config_manager.py
│   │   └── settings.py
│   ├── api/               # API layer (new)
│   │   ├── __init__.py
│   │   ├── server.py
│   │   ├── handlers.py
│   │   └── models.py
│   ├── ipc/               # IPC communication (new)
│   │   ├── __init__.py
│   │   ├── ipc_server.py
│   │   └── message_handler.py
│   ├── utils/             # Utilities (existing)
│   │   ├── logger.py
│   │   ├── exceptions.py
│   │   └── event_emitter.py
│   └── backend_service.py # Service entry point (new)
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── property/          # Property-based tests
├── requirements.txt       # Python dependencies
├── setup.py               # Package setup
└── README.md              # Backend documentation
```

## Documentation Directory

```
docs/
├── architecture.md        # System architecture documentation
├── api.md                 # API reference documentation
├── development.md         # Development guide
└── deployment.md          # Deployment guide
```

## Scripts Directory (To Be Created)

```
scripts/
├── build.sh               # Production build script
├── dev.sh                 # Development setup script
├── package.sh             # Application packaging script
└── test.sh                # Test execution script
```

## Legacy Directories

These directories contain the original monolithic application code and will be gradually migrated:

- `src/` - Original Python source code
- `tests/` - Original test files

## Configuration Files

- `.gitignore` - Git ignore rules (configured for all three layers)
- `README.md` - Main project documentation
- `LICENSE` - MIT License
- `PROJECT_STRUCTURE.md` - Legacy structure documentation
- `PROJECT_STRUCTURE_NEW.md` - This file

## Key Files

### Root Level
- `README.md` - Updated with new architecture information
- `LICENSE` - MIT License
- `.gitignore` - Comprehensive ignore rules for frontend, Tauri, and backend

### Frontend
- `package.json` - NPM dependencies and scripts
- `tsconfig.json` - TypeScript compiler configuration
- `vite.config.ts` - Vite bundler configuration
- `README.md` - Frontend-specific documentation

### Tauri
- `Cargo.toml` - Rust dependencies
- `tauri.conf.json` - Tauri framework configuration
- `README.md` - Tauri-specific documentation

### Backend
- `requirements.txt` - Python dependencies
- `setup.py` - Python package configuration
- `README.md` - Backend-specific documentation

## Migration Status

### Completed
- ✅ Directory structure created
- ✅ .gitignore configured
- ✅ README files created for all components
- ✅ Documentation structure established
- ✅ Root README updated

### Pending
- ⏳ Frontend React application initialization
- ⏳ Tauri project initialization
- ⏳ Backend IPC server implementation
- ⏳ Migration of existing code to new structure
- ⏳ Build and deployment scripts
- ⏳ CI/CD pipeline setup

## Notes

1. **Separation of Concerns**: Each layer (frontend, middleware, backend) is completely independent with its own dependencies and build process.

2. **Documentation**: Each component has its own README with specific setup and development instructions.

3. **Testing**: Tests are organized by type (unit, integration, property) within each component.

4. **Configuration**: Configuration files are kept at the root level for easy access and management.

5. **Legacy Code**: Original code in `src/` and `tests/` will be gradually migrated to the new structure.

## Next Steps

1. Initialize Tauri project with `cargo tauri init`
2. Initialize React project with Vite
3. Set up backend IPC server
4. Implement basic communication between layers
5. Migrate existing functionality incrementally
6. Create build and deployment scripts
7. Set up CI/CD pipeline
