#!/usr/bin/env python3
"""
将 PyTorch Whisper 模型转换为 CTranslate2 格式

faster-whisper 需要 CTranslate2 格式的模型，而不是原始的 .pt 文件。
这个脚本可以帮助你转换模型。
"""

import os
import sys

print("=" * 70)
print("Whisper 模型转换工具")
print("=" * 70)

print("\n重要说明:")
print("你的 tiny.en.pt 文件是 PyTorch 格式的模型。")
print("faster-whisper 需要 CTranslate2 格式的模型。")

print("\n有两种解决方案:")
print()
print("方案 1: 使用模型名称（推荐，最简单）")
print("-" * 70)
print("直接使用模型名称，faster-whisper 会自动下载 CTranslate2 格式:")
print()
print('  配置文件设置:')
print('    "whisper_model": "tiny.en"')
print('    "whisper_model_path": null')
print()
print("  支持的模型名称:")
print("    - tiny, base, small, medium, large")
print("    - tiny.en, base.en, small.en, medium.en (英文专用)")
print()
print("  首次运行时会自动下载模型到:")
print("    ~/.cache/huggingface/hub/")
print()

print("\n方案 2: 转换现有的 .pt 文件")
print("-" * 70)
print("如果你想使用现有的 tiny.en.pt 文件，需要先转换:")
print()
print("1. 安装转换工具:")
print("   pip install ctranslate2")
print()
print("2. 转换模型:")
print("   ct2-transformers-converter --model openai/whisper-tiny.en \\")
print("       --output_dir ./whisper-tiny.en-ct2 \\")
print("       --copy_files tokenizer.json preprocessor_config.json")
print()
print("3. 配置文件设置:")
print('   "whisper_model": "./whisper-tiny.en-ct2"')
print('   "whisper_model_path": "./whisper-tiny.en-ct2"')
print()

print("\n推荐配置 (config.deepseek.json):")
print("-" * 70)
print('''{
  "audio": {
    "use_api_mode": false,
    "whisper_model": "tiny.en",
    "whisper_model_path": null,
    ...
  }
}''')

print("\n" + "=" * 70)
print("建议: 使用方案 1，让 faster-whisper 自动下载模型")
print("=" * 70)

# 检查是否已经有转换后的模型
if os.path.exists("./whisper-tiny.en-ct2"):
    print("\n✓ 发现已转换的模型: ./whisper-tiny.en-ct2")
    print("  你可以使用这个模型路径")
else:
    print("\n提示: 如果你想转换模型，运行:")
    print("  pip install ctranslate2")
    print("  ct2-transformers-converter --model openai/whisper-tiny.en --output_dir ./whisper-tiny.en-ct2")
