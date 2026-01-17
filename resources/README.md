# DeepEcho Configuration Resources

This directory contains configuration templates and presets for DeepEcho.

## Configuration Files

### config.example.json
Template configuration file with all available options and default values.

**Usage:**
```bash
cp resources/config.example.json config.json
# Edit config.json with your settings
```

### config.deepseek.json
Optimized configuration for DeepSeek AI provider.

**Features:**
- DeepSeek API settings
- Recommended model: deepseek-chat
- Cost-effective configuration
- Optimized for Chinese language support

**Usage:**
```bash
cp resources/config.deepseek.json config.json
# Add your DeepSeek API key
```

### config.openai.json
Optimized configuration for OpenAI provider.

**Features:**
- OpenAI API settings
- Recommended model: gpt-3.5-turbo
- Whisper API for transcription
- High accuracy configuration

**Usage:**
```bash
cp resources/config.openai.json config.json
# Add your OpenAI API key
```

## Configuration Structure

All configuration files follow this structure:

```json
{
  "audio": {
    "use_api_mode": true,
    "record_timeout": 3,
    "energy_threshold": 1000,
    "whisper_model": "small"
  },
  "ai_provider": {
    "provider_type": "deepseek",
    "api_key": "your-api-key-here",
    "model": "deepseek-chat",
    "response_interval": 5
  },
  "ui": {
    "use_new_ui": true,
    "theme": "dark",
    "window_width": 1200,
    "window_height": 700
  }
}
```

## Configuration Options

### Audio Settings

- `use_api_mode`: Use API transcription (true) or local Whisper (false)
- `record_timeout`: Recording timeout in seconds
- `energy_threshold`: Audio sensitivity threshold
- `whisper_model`: Local Whisper model size (tiny, base, small, medium, large)

### AI Provider Settings

- `provider_type`: AI provider name (deepseek, openai, grok, claude, volcano, glm)
- `api_key`: Your API key for the provider
- `model`: Model name to use
- `response_interval`: Response update interval in seconds

### UI Settings

- `use_new_ui`: Use new integrated UI (true) or legacy UI (false)
- `theme`: UI theme (dark, light)
- `window_width`: Window width in pixels
- `window_height`: Window height in pixels

## Creating Custom Configurations

1. **Copy a template:**
   ```bash
   cp resources/config.example.json my-config.json
   ```

2. **Edit your configuration:**
   - Add your API key
   - Choose your preferred provider
   - Adjust audio and UI settings

3. **Use your configuration:**
   ```bash
   cp my-config.json config.json
   python main.py
   ```

## Security Notes

⚠️ **Important:**
- Never commit `config.json` with real API keys to version control
- Use `config.local.json` for local-only configurations (already in .gitignore)
- Keep your API keys secure and private

## Provider-Specific Guides

For detailed setup instructions for each provider, see:
- [API_SETUP.md](../API_SETUP.md) - Complete API setup guide
- [SECURITY.md](../SECURITY.md) - Security best practices

## Troubleshooting

### Configuration not loading
- Check JSON syntax (use a JSON validator)
- Ensure file is in the correct location
- Verify file permissions

### API key errors
- Verify your API key is correct
- Check provider-specific key format
- Ensure key has necessary permissions

### Model not available
- Check if model name is correct
- Verify your API plan supports the model
- See provider documentation for available models

## Support

For more help:
- Run: `python check_system.py` for system diagnostics
- See: [README.md](../README.md) for general documentation
- Check: [API_SETUP.md](../API_SETUP.md) for provider setup

---

**Note:** Configuration files in this directory are templates. Your actual `config.json` should be in the project root directory.
