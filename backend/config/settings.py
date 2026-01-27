"""
Settings and constants for DeepEcho Real-time Voice AI Assistant.

This module defines default values, constants, and configuration parameters
used throughout the application.
"""

# Audio processing parameters
RECORD_TIMEOUT = 3          # Recording timeout (seconds)
PHRASE_TIMEOUT = 3.05       # Phrase timeout (seconds)
MAX_PHRASES = 10            # Maximum phrase count
ENERGY_THRESHOLD = 1000     # Energy threshold for voice detection

# Performance parameters
PROCESSING_INTERVAL = 0.1   # Processing interval (seconds)
UI_UPDATE_INTERVAL = 0.3    # UI update interval (seconds)

# AI response parameters
DEFAULT_AI_PROVIDER = "deepseek"         # Default AI provider
RESPONSE_TIMEOUT = 30                    # AI response timeout (seconds)
MAX_AI_RETRIES = 3                       # Maximum AI request retries
DEFAULT_UPDATE_INTERVAL = 5              # Default response update interval (seconds)

# Supported AI providers and their configurations
SUPPORTED_PROVIDERS = {
    "deepseek": {
        "models": ["deepseek-chat", "deepseek-coder"],
        "default_model": "deepseek-chat",
        "base_url": "https://api.deepseek.com/v1",
        "api_key_pattern": r"^sk-[a-zA-Z0-9]{48}$"
    },
    "openai": {
        "models": ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo", "gpt-4o"],
        "default_model": "gpt-3.5-turbo",
        "base_url": "https://api.openai.com/v1",
        "api_key_pattern": r"^sk-[a-zA-Z0-9]{48}$"
    },
    "grok": {
        "models": ["grok-beta", "grok-2"],
        "default_model": "grok-beta",
        "base_url": "https://api.x.ai/v1",
        "api_key_pattern": r"^xai-[a-zA-Z0-9]{48}$"
    },
    "claude": {
        "models": ["claude-3-haiku", "claude-3-sonnet", "claude-3-opus"],
        "default_model": "claude-3-sonnet",
        "base_url": "https://api.anthropic.com/v1",
        "api_key_pattern": r"^sk-ant-[a-zA-Z0-9]{48}$"
    },
    "volcano": {
        "models": ["doubao-pro", "doubao-lite"],
        "default_model": "doubao-pro",
        "base_url": None,
        "api_key_pattern": r"^[a-zA-Z0-9]{32}$"
    },
    "glm": {
        "models": ["glm-4", "glm-3-turbo"],
        "default_model": "glm-4",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "api_key_pattern": r"^[a-zA-Z0-9]{32}\.[a-zA-Z0-9]{32}$"
    }
}

# Configuration file paths
DEFAULT_CONFIG_DIR = "~/.deepecho"
CONFIG_FILE_NAME = "config.json"
LOG_FILE_NAME = "deepecho.log"

# System requirements
REQUIRED_DEPENDENCIES = [
    "ffmpeg",  # Required for audio processing
]

# Environment variable names for API keys
ENV_API_KEYS = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "grok": "GROK_API_KEY",
    "claude": "CLAUDE_API_KEY",
    "volcano": "VOLCENGINE_API_KEY",
    "glm": "GLM_API_KEY"
}

# UI configuration
UI_DEFAULTS = {
    "window_width": 1200,
    "window_height": 800,
    "min_window_width": 800,
    "min_window_height": 600,
    "update_interval": DEFAULT_UPDATE_INTERVAL,
    "processing_interval": PROCESSING_INTERVAL,
    "ui_update_interval": UI_UPDATE_INTERVAL,
    "use_new_ui": True
}

# Audio configuration defaults
AUDIO_DEFAULTS = {
    "record_timeout": RECORD_TIMEOUT,
    "phrase_timeout": PHRASE_TIMEOUT,
    "max_phrases": MAX_PHRASES,
    "energy_threshold": ENERGY_THRESHOLD,
    "use_api_mode": False
}

# Validation limits
VALIDATION_LIMITS = {
    "min_update_interval": 1,
    "max_update_interval": 60,
    "min_timeout": 5,
    "max_timeout": 120,
    "min_retries": 1,
    "max_retries": 10
}

# Error messages
ERROR_MESSAGES = {
    "ffmpeg_not_found": "ERROR: The ffmpeg library is not installed. Please install ffmpeg and try again.",
    "no_api_key": "WARNING: No valid API keys found. AI responses will not work.",
    "invalid_provider": "ERROR: Invalid AI provider specified.",
    "config_load_failed": "ERROR: Failed to load configuration file.",
    "config_save_failed": "ERROR: Failed to save configuration file.",
    "audio_device_error": "ERROR: Failed to initialize audio devices.",
    "transcription_error": "ERROR: Transcription service failed.",
    "ai_response_error": "ERROR: AI response generation failed."
}

# Success messages
SUCCESS_MESSAGES = {
    "config_loaded": "Configuration loaded successfully",
    "config_saved": "Configuration saved successfully",
    "provider_updated": "AI provider updated successfully",
    "system_ready": "READY - System initialized successfully"
}

# Logging configuration
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file_max_bytes": 10 * 1024 * 1024,  # 10MB
    "file_backup_count": 5
}