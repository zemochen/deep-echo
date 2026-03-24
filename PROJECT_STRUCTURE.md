# DeepEcho Project Structure

This document describes the organization and structure of the DeepEcho project.

## Directory Structure

```
deepecho/
├── src/                          # Source code directory
│   ├── __init__.py
│   ├── main.py                   # Application entry point (to be created)
│   ├── config/                   # Configuration management layer
│   │   ├── __init__.py
│   │   ├── config_manager.py    # Configuration manager (to be created)
│   │   └── settings.py          # Configuration parameters (to be created)
│   ├── audio/                    # Audio processing layer
│   │   ├── __init__.py
│   │   ├── recorder.py          # Audio recorder ✓
│   │   ├── transcriber.py       # Audio transcriber (to be created)
│   │   └── models.py            # Transcription model management (to be created)
│   ├── audio_system/             # Platform-specific audio system
│   │   ├── __init__.py          ✓
│   │   ├── audio_interface.py   # Audio interface abstract ✓
│   │   ├── audio_factory.py     # Audio device factory ✓
│   │   ├── macos_audio.py       # macOS audio implementation ✓
│   │   └── windows_audio.py     # Windows audio implementation ✓
│   ├── ai/                       # AI response layer
│   │   ├── __init__.py
│   │   ├── adapter.py           # AI adapter (to be created)
│   │   ├── providers/           # AI provider implementations
│   │   │   ├── __init__.py
│   │   │   ├── base_provider.py # Provider base class (to be created)
│   │   │   ├── deepseek_provider.py (to be created)
│   │   │   ├── openai_provider.py (to be created)
│   │   │   ├── grok_provider.py (to be created)
│   │   │   ├── claude_provider.py (to be created)
│   │   │   ├── volcano_provider.py (to be created)
│   │   │   └── aliyun_provider.py (to be created)
│   │   └── responder.py         # GPT responder (to be created)
│   ├── ui/                       # User interface layer
│   │   ├── __init__.py
│   │   ├── controller.py        # UI controller (to be created)
│   │   └── components.py        # UI components (to be created)
│   └── utils/                    # Utility modules
│       ├── __init__.py
│       ├── logger.py            # Logging utility ✓
│       └── exceptions.py        # Custom exceptions ✓
├── tests/                        # Test directory
│   ├── __init__.py
│   ├── conftest.py              # pytest configuration (to be created)
│   ├── unit/                    # Unit tests
│   │   ├── __init__.py
│   │   ├── test_audio_recorder.py (to be created)
│   │   ├── test_audio_transcriber.py (to be created)
│   │   ├── test_ai_adapter.py (to be created)
│   │   └── test_ui_controller.py (to be created)
│   ├── property/                # Property-based tests
│   │   ├── __init__.py
│   │   ├── test_audio_properties.py ✓
│   │   ├── test_ai_properties.py (to be created)
│   │   └── test_ui_properties.py (to be created)
│   └── integration/             # Integration tests
│       ├── __init__.py
│       └── test_end_to_end.py (to be created)
├── custom_speech_recognition/    # Third-party library (keep as-is)
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies ✓
├── README.md
├── .gitignore
└── PROJECT_STRUCTURE.md         # This file

# Legacy files (migration status)
├── AudioRecorder.py             # → src/audio/recorder.py ✓ MIGRATED & DELETED
├── AudioTranscriber.py          # → src/audio/transcriber.py (pending)
├── GPTResponder.py              # → src/ai/responder.py (pending)
├── LlmClient.py                 # → src/ai/adapter.py (pending)
├── TranscriberModels.py         # → src/audio/models.py (pending)
├── UILayout.py                  # → src/ui/controller.py (pending)
├── main.py                      # → src/main.py (pending)
├── prompts.py                   # → src/config/prompts.py (pending)
└── keys.py                      # → src/config/keys.py (or use .env) (pending)

# Deleted directories
├── audio_system/                # → src/audio_system/ ✓ MIGRATED & DELETED
└── audio/                       # → (empty directory) ✓ DELETED
```

## Naming Conventions

### Python Source Files
- **Module files**: Use lowercase with underscores: `audio_recorder.py`, `config_manager.py`
- **Class files**: One main class per file, filename matches class name in snake_case
  - `AudioRecorder` class → `audio_recorder.py`
  - `AIAdapter` class → `ai_adapter.py`
- **Utility modules**: Descriptive names: `logger.py`, `exceptions.py`

### Test Files
- **Unit tests**: `test_<module_name>.py` (e.g., `test_audio_recorder.py`)
- **Property tests**: `test_<feature>_properties.py` (e.g., `test_audio_properties.py`)
- **Integration tests**: `test_<scenario>.py` (e.g., `test_end_to_end.py`)

### Code Naming
- **Classes**: PascalCase (`AudioRecorder`, `AIAdapter`, `DeepSeekProvider`)
- **Functions/Methods**: snake_case (`record_into_queue`, `adjust_for_noise`)
- **Constants**: UPPER_SNAKE_CASE (`RECORD_TIMEOUT`, `ENERGY_THRESHOLD`)
- **Private members**: Prefix with underscore (`_get_default_speaker`, `_stop_listening`)

## Import Guidelines

```python
# Standard library imports
import os
import logging
from datetime import datetime
from typing import Optional, Callable

# Third-party library imports
import numpy as np
import custom_speech_recognition as sr

# Local module imports
from backend.audio.recorder import AudioRecorder
from backend.ai.adapter import AIAdapter
from backend.config.settings import RECORD_TIMEOUT
```

## Architecture Layers

1. **Audio Processing Layer** (`src/audio/`)
   - Audio recording and capture
   - Speech-to-text transcription
   - Transcription model management

2. **Audio System Layer** (`src/audio_system/`)
   - Platform-specific audio device detection
   - Cross-platform audio interface abstraction

3. **AI Response Layer** (`src/ai/`)
   - AI provider abstraction and adapter
   - Multiple AI service provider implementations
   - Response generation logic

4. **User Interface Layer** (`src/ui/`)
   - UI controller and event handling
   - UI components and widgets

5. **Configuration Layer** (`src/config/`)
   - Application configuration management
   - Settings and parameters

6. **Utility Layer** (`src/utils/`)
   - Logging utilities
   - Custom exceptions
   - Helper functions

## Testing Strategy

- **Unit Tests** (`tests/unit/`): Test individual components in isolation
- **Property Tests** (`tests/property/`): Test universal properties with Hypothesis (100+ iterations)
- **Integration Tests** (`tests/integration/`): Test component interactions and end-to-end flows

## Migration Status

✓ = Completed
- ✓ Audio recorder refactored and moved to `src/audio/recorder.py`
- ✓ Audio system modules moved to `src/audio_system/`
- ✓ Property tests created for audio recorder
- ✓ Utility modules created (logger, exceptions)
- ✓ Project structure established

Pending:
- Audio transcriber migration
- AI adapter and providers implementation
- UI controller migration
- Configuration management
- Main application entry point
- Additional tests

## Next Steps

1. Continue with Task 2: Refactor audio transcriber module
2. Implement AI adapter architecture (Task 3)
3. Migrate UI components (Task 6)
4. Create configuration management (Task 7)
5. Update main.py to use new structure
6. Update all imports in legacy files
7. Remove legacy files after migration is complete
