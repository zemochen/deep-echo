# 🎧 DeepEcho - 实时语音 AI 助手

DeepEcho 是一个全面的实时语音转录和 AI 助手系统，支持多种 AI 提供商。它同时采集麦克风和扬声器音频，提供实时转录，并使用各种 AI 模型（包括 DeepSeek、OpenAI GPT、Claude、Grok 等）生成智能回复建议。

## 🏗️ 架构

DeepEcho 采用现代化的前后端分离架构：

- **前端** (TypeScript/React/MUI)：现代化的 Web 界面
- **中间层** (Tauri/Rust)：跨平台框架和 IPC 通信层
- **后端** (Python)：AI 处理和音频处理

详细说明请参阅[架构文档](docs/architecture.md)。

## ✨ 主要功能

- **🎤 实时音频采集**：同时录制麦克风和扬声器音频
- **📝 实时转录**：支持本地和 API 模式的实时语音转文字
- **🤖 多 AI 提供商支持**：DeepSeek、OpenAI、Claude、Grok、火山引擎和 GLM
- **🎨 现代界面**：集成 AI 提供商选择的新界面
- **⚙️ 灵活配置**：基于 JSON 的配置，支持多种预设
- **🔧 跨平台**：支持 Windows 和 macOS
- **📊 系统监控**：内置诊断和资源优化
- **🛡️ 错误恢复**：全面的错误处理和重试机制

## 🚀 快速开始

### 📋 前置要求

- **Node.js** 18+ 和 npm
- **Rust** 1.70+（通过 [rustup](https://rustup.rs/) 安装）
- **Python** >=3.8.0
- **FFmpeg**（用于音频处理）
- 至少一个 AI 提供商的 API 密钥（参见 [API 设置指南](API_SETUP.md)）
- Windows / macOS 系统

### 🔧 安装

1. **克隆仓库：**
   ```bash
   git clone https://github.com/zemochen/deep_echo.git
   cd deep_echo
   ```

2. **安装 Tauri CLI：**
   ```bash
   cargo install tauri-cli
   ```

3. **安装前端依赖：**
   ```bash
   cd frontend
   npm install
   cd ..
   ```

4. **安装后端依赖：**
   ```bash
   cd backend
   pip install -r requirements.txt
   cd ..
   ```

5. **设置安全保护（推荐）：**
   ```bash
   # Linux/macOS
   chmod +x setup_security.sh
   ./setup_security.sh

   # Windows
   setup_security.bat
   ```
   这将配置 git hooks 以防止意外提交 API 密钥。

6. **设置 API 密钥**（选择一种方式）：

   **方式一：配置文件（推荐）**
   ```bash
   cp resources/config.example.json config.json
   # 编辑 config.json 并添加您的 API 密钥
   ```

   **方式二：环境变量**
   ```bash
   export DEEPSEEK_API_KEY="sk-your-key-here"
   # 或
   export OPENAI_API_KEY="sk-your-key-here"
   ```

   **方式三：传统 keys.py（安全）**
   ```bash
   # 复制模板文件
   cp keys.example.py keys.py
   # 编辑 keys.py 并添加您的实际 API 密钥
   # 注意：keys.py 在 .gitignore 中，不会被提交到 git
   ```

   ⚠️ **安全提示**：切勿将您的实际 API 密钥提交到版本控制。`keys.py` 文件会自动从 git 提交中排除。详细安全指南请参阅 [SECURITY.md](SECURITY.md)。

7. **运行 DeepEcho：**
   ```bash
   npm run tauri dev
   ```

## 📚 文档

- [架构](docs/architecture.md) - 系统架构和设计
- [API 参考](docs/api.md) - 完整的 API 文档
- [开发指南](docs/development.md) - 开发设置和工作流程
- [部署指南](docs/deployment.md) - 构建和部署

## 📁 项目结构

```
deepecho/
├── frontend/          # React + TypeScript 前端
├── src-tauri/         # Tauri 中间层
├── backend/           # Python 后端服务
├── docs/              # 文档
└── scripts/           # 构建和部署脚本
```

请参阅各组件的 README：
- [前端 README](frontend/README.md)
- [Tauri README](src-tauri/README.md)
- [后端 README](backend/README.md)

## 🎯 使用模式

### 默认模式（集成应用）
```bash
python main.py
```
- 使用新的集成架构
- 自动检测 AI 提供商
- 带提供商选择的现代界面
- 全面的错误处理

### API 转录模式
```bash
python main.py --api
```
- 使用 OpenAI Whisper API 进行转录
- 更高的准确率和多语言支持
- 需要互联网连接

### 传统模式
```bash
python main.py --legacy
```
- 使用原始应用架构
- 向后兼容模式
- 传统界面

### 详细日志模式
```bash
python main.py --verbose
```
- 详细日志用于故障排除
- 系统诊断信息

## 🤖 支持的 AI 提供商

| 提供商 | 模型 | 设置指南 |
|--------|------|----------|
| **DeepSeek** | deepseek-chat, deepseek-coder | [DeepSeek 设置](API_SETUP.md#1-deepseek-recommended) |
| **OpenAI** | gpt-3.5-turbo, gpt-4, gpt-4o | [OpenAI 设置](API_SETUP.md#2-openai) |
| **Claude** | claude-3-haiku, claude-3-sonnet, claude-3-opus | [Claude 设置](API_SETUP.md#3-anthropic-claude) |
| **Grok** | grok-beta, grok-2 | [Grok 设置](API_SETUP.md#4-xai-grok) |
| **火山引擎** | doubao-pro, doubao-lite | [火山引擎设置](API_SETUP.md#5-bytedance-volcano-engine) |
| **GLM** | qwen-turbo, qwen-plus, qwen-max | [阿里云设置](API_SETUP.md#6-alibaba-cloud) |

## ⚙️ 配置

### 配置文件

DeepEcho 支持多种配置预设：

- `resources/config.example.json` - 配置模板
- `resources/config.deepseek.json` - DeepSeek 优化设置
- `resources/config.openai.json` - OpenAI 优化设置

### 配置选项

```json
{
  "audio": {
    "use_api_mode": true,          // 使用 API 模式 vs 本地转录
    "record_timeout": 3,           // 录音超时时间（秒）
    "energy_threshold": 1000       // 音频灵敏度
  },
  "ai_provider": {
    "provider_type": "deepseek",   // 使用的 AI 提供商
    "api_key": "your-key-here",    // API 密钥
    "model": "deepseek-chat",      // 模型名称
    "response_interval": 5         // 回复更新间隔
  },
  "ui": {
    "use_new_ui": true,           // 使用新的集成界面
    "theme": "dark",              // 界面主题
    "window_width": 1200          // 窗口尺寸
  }
}
```

## 🖥️ 系统要求

### Windows
- Windows 10/11
- Python 3.8+
- PyAudioWPatch（自动安装）
- FFmpeg

### macOS
- macOS 10.14+
- Python 3.8+
- BlackHole 虚拟音频设备
- FFmpeg、PortAudio

**macOS 安装：**
```bash
brew install ffmpeg portaudio python-tk blackhole-2ch
```

## 🔧 高级功能

### 系统监控
- 实时资源使用追踪
- 线程健康监控
- 队列大小优化
- 内存使用警告

### 错误恢复
- 指数退避自动重试
- 故障时优雅降级
- 组件健康检查
- 网络故障处理

### 性能优化
- 多线程架构
- 资源使用优化
- 队列管理
- 内存泄漏防护

## 🐛 故障排除

### 常见问题

**"FFmpeg 未找到"**
```bash
# Windows（使用 Chocolatey）
choco install ffmpeg

# macOS
brew install ffmpeg
```

**"未配置 AI 提供商"**
- 检查配置中的 API 密钥
- 验证密钥格式和权限
- 参见 [API 设置指南](API_SETUP.md)

**音频设备问题**
- 确保默认音频设备设置正确
- 在 macOS 上，配置 BlackHole 用于扬声器采集
- 检查系统音频权限

**内存使用过高**
- 在配置中启用资源优化
- 减小队列大小限制
- 使用本地转录模式

### 获取帮助

1. 使用详细日志运行：`python main.py --verbose`
2. 检查系统诊断输出
3. 检查配置文件语法
4. 参考 [API 设置指南](API_SETUP.md)

## 📊 性能提示

- **最佳准确率**：使用 `--api` 模式并保持互联网连接
- **最低延迟**：使用本地模式和 tiny Whisper 模型
- **成本效率**：使用 DeepSeek 或 Claude Haiku
- **最佳质量**：使用 OpenAI GPT-4 或 Claude Opus

## 🔄 从旧版本迁移

如果从旧版本升级：

1. **备份您的 keys.py 文件**
2. **创建新的配置文件**：
   ```bash
   cp resources/config.example.json config.json
   ```
3. **以新格式更新您的 API 密钥**
4. **使用以下命令测试**：`python main.py --legacy`（备用模式）

## 📖 许可证

本项目采用 MIT 许可证 - 请参阅 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎贡献！请遵循以下指南：

1. **代码风格**：遵循 PEP 8 指南
2. **测试**：为新功能添加测试
3. **文档**：更新更改的文档
4. **提交**：使用清晰、有描述性的提交信息

### 开发环境设置
```bash
pip install -r requirements-dev.txt
pytest tests/
```

## 🙏 致谢

- OpenAI 提供 Whisper 和 GPT 模型
- Anthropic 提供 Claude 模型
- DeepSeek 提供可访问的 AI API
- 所有 DeepEcho 的贡献者和用户