# Whisper 模型使用指南

## 快速开始

### 推荐配置（最简单）

编辑 `config.deepseek.json`：

```json
{
  "audio": {
    "use_api_mode": false,
    "whisper_model": "tiny.en",
    "whisper_model_path": null
  }
}
```

然后运行：
```bash
python src/main.py
```

首次运行会自动下载模型（约 75MB），后续使用会从缓存加载。

---

## 关于你的 tiny.en.pt 文件

你的 `tiny.en.pt` 是 **PyTorch 格式**的模型文件。

**问题**: faster-whisper 使用的是 **CTranslate2 格式**，不能直接使用 `.pt` 文件。

**解决方案**: 使用模型名称 `"tiny.en"`，让 faster-whisper 自动下载正确格式的模型。

---

## 配置选项详解

### `whisper_model`
指定要使用的 Whisper 模型。

**可选值**:
- `"tiny"` - 最小模型，速度最快（39M 参数）
- `"tiny.en"` - 英文专用 tiny 模型（推荐用于英文）
- `"base"` - 基础模型（74M 参数）
- `"base.en"` - 英文专用 base 模型
- `"small"` - 小型模型（244M 参数）
- `"small.en"` - 英文专用 small 模型
- `"medium"` - 中型模型（769M 参数）
- `"medium.en"` - 英文专用 medium 模型
- `"large"` - 大型模型（1550M 参数）

**示例**:
```json
"whisper_model": "tiny.en"
```

### `whisper_model_path`
指定本地模型文件或目录的路径（可选）。

**可选值**:
- `null` - 使用 `whisper_model` 指定的模型名称
- `"./path/to/model"` - 本地 CTranslate2 格式模型目录

**示例**:
```json
"whisper_model_path": null
```

### `use_api_mode`
是否使用 OpenAI Whisper API。

**可选值**:
- `false` - 使用本地模型（推荐）
- `true` - 使用 OpenAI API（需要 API key 和网络连接）

---

## 模型性能对比

| 模型 | 大小 | 内存 | 速度 | 准确度 | 推荐场景 |
|------|------|------|------|--------|----------|
| tiny.en | ~75MB | ~1GB | 最快 | 较低 | 实时转录、快速测试 |
| base.en | ~150MB | ~1GB | 快 | 中等 | 日常使用 |
| small.en | ~500MB | ~2GB | 中等 | 良好 | 平衡性能和准确度 |
| medium.en | ~1.5GB | ~5GB | 慢 | 很好 | 高准确度需求 |
| large | ~3GB | ~10GB | 很慢 | 最好 | 专业转录 |

**建议**:
- 实时对话: `tiny.en` 或 `base.en`
- 一般使用: `small.en`
- 高质量转录: `medium.en`

---

## 配置示例

### 示例 1: 使用 tiny.en（最快）

```json
{
  "audio": {
    "use_api_mode": false,
    "whisper_model": "tiny.en",
    "whisper_model_path": null
  }
}
```

### 示例 2: 使用 small.en（平衡）

```json
{
  "audio": {
    "use_api_mode": false,
    "whisper_model": "small.en",
    "whisper_model_path": null
  }
}
```

### 示例 3: 使用 OpenAI API

```json
{
  "audio": {
    "use_api_mode": true,
    "whisper_model": "whisper-1",
    "whisper_model_path": null
  }
}
```

### 示例 4: 使用本地转换的模型

```json
{
  "audio": {
    "use_api_mode": false,
    "whisper_model": "./whisper-tiny.en-ct2",
    "whisper_model_path": "./whisper-tiny.en-ct2"
  }
}
```

---

## 模型下载位置

faster-whisper 会将模型下载到：

**macOS/Linux**:
```
~/.cache/huggingface/hub/
```

**Windows**:
```
C:\Users\<username>\.cache\huggingface\hub\
```

---

## 转换 PyTorch 模型（高级）

如果你想使用现有的 `.pt` 文件，需要转换为 CTranslate2 格式：

### 1. 安装转换工具

```bash
pip install ctranslate2
```

### 2. 转换模型

```bash
ct2-transformers-converter \
    --model openai/whisper-tiny.en \
    --output_dir ./whisper-tiny.en-ct2 \
    --copy_files tokenizer.json preprocessor_config.json
```

### 3. 使用转换后的模型

```json
{
  "audio": {
    "whisper_model": "./whisper-tiny.en-ct2",
    "whisper_model_path": "./whisper-tiny.en-ct2"
  }
}
```

---

## 故障排除

### 问题 1: 模型下载失败

**症状**: 
```
Failed to download model...
```

**解决方法**:
1. 检查网络连接
2. 检查防火墙设置
3. 手动下载模型到缓存目录

### 问题 2: 内存不足

**症状**:
```
Out of memory...
```

**解决方法**:
1. 使用更小的模型（如 `tiny.en`）
2. 关闭其他应用程序
3. 增加系统内存

### 问题 3: 转录速度慢

**症状**:
转录延迟明显

**解决方法**:
1. 使用更小的模型
2. 如果有 GPU，启用 CUDA
3. 调整 VAD 参数

### 问题 4: 转录质量差

**症状**:
转录结果不准确

**解决方法**:
1. 使用更大的模型（如 `small.en` 或 `medium.en`）
2. 确保音频输入质量良好
3. 调整 VAD 阈值参数

---

## 验证配置

运行应用后，检查日志输出：

```
Initializing comprehensive transcription system...
Using local Whisper model: tiny.en
Loading Faster Whisper model 'tiny.en' on cpu...
Faster Whisper model loaded successfully.
✓ Transcription system ready
```

如果看到这些信息，说明配置正确！

---

## 参考资料

- [faster-whisper GitHub](https://github.com/guillaumekln/faster-whisper)
- [Whisper 官方文档](https://github.com/openai/whisper)
- [CTranslate2 文档](https://github.com/OpenNMT/CTranslate2)
- [Hugging Face Models](https://huggingface.co/models?search=whisper)
