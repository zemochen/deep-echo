# API Key Setup Guide

This guide explains how to set up API keys for different AI providers supported by DeepEcho.

## Supported AI Providers

DeepEcho supports multiple AI providers. You only need to set up one provider to get started.

### 1. DeepSeek (Recommended)

DeepSeek offers competitive pricing and good performance for conversational AI.

**Steps:**
1. Visit [https://platform.deepseek.com](https://platform.deepseek.com)
2. Create an account and verify your email
3. Navigate to API Keys section
4. Create a new API key
5. Copy the API key (starts with `sk-`)

**Configuration:**
```json
{
  "ai_provider": {
    "provider_type": "deepseek",
    "api_key": "sk-your-deepseek-key-here",
    "model": "deepseek-chat"
  }
}
```

### 2. OpenAI

OpenAI provides GPT models with excellent conversational capabilities.

**Steps:**
1. Visit [https://platform.openai.com](https://platform.openai.com)
2. Create an account and add billing information
3. Go to API Keys section
4. Create a new secret key
5. Copy the API key (starts with `sk-`)

**Configuration:**
```json
{
  "ai_provider": {
    "provider_type": "openai",
    "api_key": "sk-your-openai-key-here",
    "model": "gpt-3.5-turbo"
  }
}
```

**Available Models:**
- `gpt-3.5-turbo` (recommended for cost-effectiveness)
- `gpt-4` (higher quality, more expensive)
- `gpt-4-turbo` (faster GPT-4)
- `gpt-4o` (latest model)

### 3. Anthropic Claude

Claude offers excellent reasoning and safety features.

**Steps:**
1. Visit [https://console.anthropic.com](https://console.anthropic.com)
2. Create an account and verify
3. Navigate to API Keys
4. Generate a new API key
5. Copy the key

**Configuration:**
```json
{
  "ai_provider": {
    "provider_type": "claude",
    "api_key": "your-claude-key-here",
    "model": "claude-3-sonnet"
  }
}
```

**Available Models:**
- `claude-3-haiku` (fastest, most cost-effective)
- `claude-3-sonnet` (balanced performance)
- `claude-3-opus` (highest capability)

### 4. xAI Grok

Grok provides real-time information and unique conversational style.

**Steps:**
1. Visit [https://console.x.ai](https://console.x.ai)
2. Create an account
3. Generate API key
4. Copy the key

**Configuration:**
```json
{
  "ai_provider": {
    "provider_type": "grok",
    "api_key": "your-grok-key-here",
    "model": "grok-beta"
  }
}
```

### 5. ByteDance Volcano Engine (火山引擎)

Chinese AI provider with competitive models.

**Steps:**
1. Visit [https://console.volcengine.com](https://console.volcengine.com)
2. Create account and verify
3. Navigate to AI services
4. Generate API key
5. Copy the key

**Configuration:**
```json
{
  "ai_provider": {
    "provider_type": "volcano",
    "api_key": "your-volcano-key-here",
    "model": "doubao-pro"
  }
}
```

### 6. Alibaba Cloud (智谱)

Chinese AI provider with Qwen models.

**Steps:**
1. Visit Alibaba Cloud AI services
2. Create account and set up billing
3. Generate API credentials
4. Copy the key

**Configuration:**
```json
{
  "ai_provider": {
    "provider_type": "glm",
    "api_key": "your-glm-key-here",
    "model": "qwen-turbo"
  }
}
```

## Configuration Methods

### Method 1: Configuration File (Recommended)

1. Copy `config.example.json` to `config.json`
2. Edit the `ai_provider` section with your chosen provider
3. Replace `"your-api-key-here"` with your actual API key
4. Save the file

### Method 2: Environment Variables

Set environment variables for your chosen provider:

```bash
# For DeepSeek
export DEEPSEEK_API_KEY="sk-your-key-here"

# For OpenAI
export OPENAI_API_KEY="sk-your-key-here"

# For Claude
export ANTHROPIC_API_KEY="your-key-here"

# For Grok
export GROK_API_KEY="your-key-here"
```

### Method 3: Legacy keys.py File

Create a `keys.py` file in the project root:

```python
# Legacy support - use configuration file instead
OPENAI_API_KEY = "sk-your-openai-key-here"
VOLCENGINE_API_KEY = "your-volcano-key-here"
```

## Testing Your Setup

1. Start DeepEcho with your configuration:
   ```bash
   python main.py
   ```

2. Look for the provider confirmation message:
   ```
   Using DeepSeek provider with model: deepseek-chat
   ```

3. Test AI responses by speaking into your microphone

## Troubleshooting

### Common Issues

**"No AI provider configured"**
- Check that your API key is correctly set
- Verify the key format (should start with appropriate prefix)
- Ensure the provider type matches your key

**"AI provider error: Invalid API key"**
- Double-check your API key
- Verify you have sufficient credits/billing set up
- Check if the key has the necessary permissions

**"Connection timeout"**
- Check your internet connection
- Try increasing the timeout in configuration
- Some providers may have regional restrictions

### Getting Help

1. Check the console output for specific error messages
2. Enable verbose logging with `--verbose` flag
3. Review the configuration file for syntax errors
4. Ensure your API key has sufficient credits

## Cost Considerations

- **DeepSeek**: Most cost-effective option
- **OpenAI GPT-3.5**: Good balance of cost and quality
- **Claude Haiku**: Fast and affordable
- **OpenAI GPT-4**: Higher cost but better quality
- **Grok**: Pricing varies

Start with DeepSeek or OpenAI GPT-3.5 for the best cost-to-performance ratio.