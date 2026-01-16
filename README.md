
# 🎧 DeepEcho - Real-time Voice AI Assistant

DeepEcho is a comprehensive real-time voice transcription and AI assistant system that supports multiple AI providers. It captures both microphone and speaker audio, provides live transcription, and generates intelligent response suggestions using various AI models including DeepSeek, OpenAI GPT, Claude, Grok, and more.

## 🏗️ Architecture

DeepEcho uses a modern frontend-backend separation architecture:

- **Frontend** (TypeScript/React/MUI): Modern web-based UI
- **Middleware** (Tauri/Rust): Cross-platform framework and IPC layer
- **Backend** (Python): AI processing and audio handling

See [Architecture Documentation](docs/architecture.md) for details.

## ✨ Key Features

- **🎤 Real-time Audio Capture**: Simultaneous microphone and speaker audio recording
- **📝 Live Transcription**: Real-time speech-to-text with local and API modes
- **🤖 Multi-AI Provider Support**: DeepSeek, OpenAI, Claude, Grok, Volcano Engine, and GLM
- **🎨 Modern UI**: New integrated interface with AI provider selection
- **⚙️ Flexible Configuration**: JSON-based configuration with multiple presets
- **🔧 Cross-platform**: Windows and macOS support
- **📊 System Monitoring**: Built-in diagnostics and resource optimization
- **🛡️ Error Recovery**: Comprehensive error handling and retry mechanisms

## 🚀 Quick Start

### 📋 Prerequisites

- **Node.js** 18+ and npm
- **Rust** 1.70+ (install via [rustup](https://rustup.rs/))
- **Python** >=3.8.0
- **FFmpeg** (for audio processing)
- At least one AI provider API key (see [API Setup Guide](API_SETUP.md))
- Windows OS / macOS

### 🔧 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/zemochen/deep_echo.git
   cd deep_echo
   ```

2. **Install Tauri CLI:**
   ```bash
   cargo install tauri-cli
   ```

3. **Install frontend dependencies:**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **Install backend dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

3. **Set up security (Recommended):**
   ```bash
   # Linux/macOS
   chmod +x setup_security.sh
   ./setup_security.sh
   
   # Windows
   setup_security.bat
   ```
   This will configure git hooks to prevent accidental API key commits.

4. **Set up API keys** (choose one method):

   **Method 1: Configuration File (Recommended)**
   ```bash
   cp resources/config.example.json config.json
   # Edit config.json and add your API key
   ```

   **Method 2: Environment Variable**
   ```bash
   export DEEPSEEK_API_KEY="sk-your-key-here"
   # or
   export OPENAI_API_KEY="sk-your-key-here"
   ```

   **Method 3: Legacy keys.py (Secure)**
   ```bash
   # Copy the template file
   cp keys.example.py keys.py
   # Edit keys.py and add your actual API keys
   # Note: keys.py is in .gitignore and will NOT be committed to git
   ```
   
   ⚠️ **Security Note**: Never commit your actual API keys to version control. The `keys.py` file is automatically excluded from git commits. See [SECURITY.md](SECURITY.md) for detailed security guidelines.

4. **Run DeepEcho:**
   ```bash
   npm run tauri dev
   ```

## 📚 Documentation

- [Architecture](docs/architecture.md) - System architecture and design
- [API Reference](docs/api.md) - Complete API documentation
- [Development Guide](docs/development.md) - Development setup and workflow
- [Deployment Guide](docs/deployment.md) - Building and deploying

## 📁 Project Structure

```
deepecho/
├── frontend/          # React + TypeScript frontend
├── src-tauri/         # Tauri middleware layer
├── backend/           # Python backend service
├── docs/              # Documentation
└── scripts/           # Build and deployment scripts
```

See component-specific READMEs:
- [Frontend README](frontend/README.md)
- [Tauri README](src-tauri/README.md)
- [Backend README](backend/README.md)

## 🎯 Usage Modes

### Default Mode (Integrated Application)
```bash
python main.py
```
- Uses new integrated architecture
- Automatic AI provider detection
- Modern UI with provider selection
- Comprehensive error handling

### API Transcription Mode
```bash
python main.py --api
```
- Uses OpenAI Whisper API for transcription
- Higher accuracy and multi-language support
- Requires internet connection

### Legacy Mode
```bash
python main.py --legacy
```
- Uses original application architecture
- Backward compatibility mode
- Legacy UI interface

### Verbose Logging
```bash
python main.py --verbose
```
- Detailed logging for troubleshooting
- System diagnostics information

## 🤖 Supported AI Providers

| Provider | Models | Setup Guide |
|----------|--------|-------------|
| **DeepSeek** | deepseek-chat, deepseek-coder | [DeepSeek Setup](API_SETUP.md#1-deepseek-recommended) |
| **OpenAI** | gpt-3.5-turbo, gpt-4, gpt-4o | [OpenAI Setup](API_SETUP.md#2-openai) |
| **Claude** | claude-3-haiku, claude-3-sonnet, claude-3-opus | [Claude Setup](API_SETUP.md#3-anthropic-claude) |
| **Grok** | grok-beta, grok-2 | [Grok Setup](API_SETUP.md#4-xai-grok) |
| **Volcano Engine** | doubao-pro, doubao-lite | [Volcano Setup](API_SETUP.md#5-bytedance-volcano-engine) |
| **GLM** | qwen-turbo, qwen-plus, qwen-max | [GLM Setup](API_SETUP.md#6-alibaba-cloud) |

## ⚙️ Configuration

### Configuration Files

DeepEcho supports multiple configuration presets:

- `resources/config.example.json` - Template configuration
- `resources/config.deepseek.json` - DeepSeek optimized settings
- `resources/config.openai.json` - OpenAI optimized settings

### Configuration Options

```json
{
  "audio": {
    "use_api_mode": true,          // Use API vs local transcription
    "record_timeout": 3,           // Recording timeout (seconds)
    "energy_threshold": 1000       // Audio sensitivity
  },
  "ai_provider": {
    "provider_type": "deepseek",   // AI provider to use
    "api_key": "your-key-here",    // API key
    "model": "deepseek-chat",      // Model name
    "response_interval": 5         // Response update interval
  },
  "ui": {
    "use_new_ui": true,           // Use new integrated UI
    "theme": "dark",              // UI theme
    "window_width": 1200          // Window dimensions
  }
}
```

## 🖥️ System Requirements

### Windows
- Windows 10/11
- Python 3.8+
- PyAudioWPatch (auto-installed)
- FFmpeg

### macOS
- macOS 10.14+
- Python 3.8+
- BlackHole virtual audio device
- FFmpeg, PortAudio

**macOS Setup:**
```bash
brew install ffmpeg portaudio python-tk blackhole-2ch
```

## 🔧 Advanced Features

### System Monitoring
- Real-time resource usage tracking
- Thread health monitoring
- Queue size optimization
- Memory usage alerts

### Error Recovery
- Automatic retry with exponential backoff
- Graceful degradation on failures
- Component health checks
- Network failure handling

### Performance Optimization
- Multi-threaded architecture
- Resource usage optimization
- Queue management
- Memory leak prevention

## 🐛 Troubleshooting

### Common Issues

**"FFmpeg not found"**
```bash
# Windows (with Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg
```

**"No AI provider configured"**
- Check your API key in configuration
- Verify the key format and permissions
- See [API Setup Guide](API_SETUP.md)

**Audio device issues**
- Ensure default audio devices are properly set
- On macOS, configure BlackHole for speaker capture
- Check system audio permissions

**High memory usage**
- Enable resource optimization in config
- Reduce queue size limits
- Use local transcription mode

### Getting Help

1. Run with verbose logging: `python main.py --verbose`
2. Check the system diagnostics output
3. Review configuration file syntax
4. Consult the [API Setup Guide](API_SETUP.md)

## 📊 Performance Tips

- **For best accuracy**: Use `--api` mode with internet connection
- **For lowest latency**: Use local mode with tiny Whisper model
- **For cost efficiency**: Use DeepSeek or Claude Haiku
- **For best quality**: Use OpenAI GPT-4 or Claude Opus

## 🔄 Migration from Legacy Version

If upgrading from an older version:

1. **Backup your keys.py file**
2. **Create new configuration file**:
   ```bash
   cp resources/config.example.json config.json
   ```
3. **Update your API keys in the new format**
4. **Test with**: `python main.py --legacy` (fallback mode)

## 📖 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Code Style**: Follow PEP 8 guidelines
2. **Testing**: Add tests for new features
3. **Documentation**: Update documentation for changes
4. **Commits**: Use clear, descriptive commit messages

### Development Setup
```bash
pip install -r requirements-dev.txt
pytest tests/
```

## 🙏 Acknowledgments

- OpenAI for Whisper and GPT models
- Anthropic for Claude models
- DeepSeek for accessible AI APIs
- All contributors and users of DeepEcho