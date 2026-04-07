# 音频采集方案分析

## 当前方案分析

### 现有实现

DeepEcho当前采用的音频采集方案：

#### 1. 麦克风采集 (Microphone)
- **实现方式**: 使用 `speech_recognition` 库的 `sr.Microphone()` 类
- **工作原理**: 直接访问系统默认麦克风设备
- **支持平台**: Windows, macOS, Linux
- **特点**: 简单、可靠、跨平台

```python
source = sr.Microphone(sample_rate=16000)
```

#### 2. 扬声器采集 (Speaker Output)

**Windows 实现**:
- **技术**: WASAPI (Windows Audio Session API) Loopback
- **库**: PyAudioWPatch (PyAudio的Windows增强版)
- **工作原理**: 
  - 使用WASAPI获取系统默认输出设备
  - 查找对应的loopback设备
  - 通过loopback设备采集扬声器输出
- **优点**: 官方支持，稳定可靠
- **缺点**: 仅限Windows

```python
# Windows WASAPI loopback
with pyaudio.PyAudio() as p:
    wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
    # 查找loopback设备
    for loopback in p.get_loopback_device_info_generator():
        if default_speakers["name"] in loopback["name"]:
            speaker_device = loopback
            break
```

**macOS 实现**:
- **技术**: BlackHole 虚拟音频设备
- **工作原理**:
  - BlackHole是一个虚拟音频设备驱动
  - 需要用户手动安装 (brew install blackhole-2ch)
  - 系统音频通过BlackHole路由
  - 应用通过BlackHole采集扬声器输出
- **优点**: 功能完整，支持多通道
- **缺点**: 需要用户手动安装，配置复杂

```python
# macOS BlackHole
for i in range(p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if "BlackHole" in dev["name"] and dev["maxInputChannels"] > 0:
        speaker_device = dev
        break
```

### 音频采集流程

```
┌─────────────────────────────────────────────────────────┐
│                    系统音频源                            │
├──────────────────────┬──────────────────────────────────┤
│   麦克风输入         │      扬声器输出                   │
│   (Microphone)       │      (Speaker Output)            │
└──────────────────────┴──────────────────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────────┐  ┌──────────────────────┐
│  sr.Microphone()     │  │  WASAPI Loopback     │
│  (所有平台)          │  │  (Windows)           │
│                      │  │  或                  │
│                      │  │  BlackHole           │
│                      │  │  (macOS)             │
└──────────────────────┘  └──────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────────────────────────────────────────────┐
│              AudioRecorder (Python)                      │
│  • DefaultMicRecorder                                    │
│  • DefaultSpeakerRecorder                                │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│              音频队列 (Queue)                            │
│  • mic_queue: 麦克风音频数据                             │
│  • speaker_queue: 扬声器音频数据                         │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│              AudioTranscriber (Python)                   │
│  • 处理两个队列中的音频                                  │
│  • 区分音频源（You/Speaker）                             │
│  • 生成转录结果                                          │
└──────────────────────────────────────────────────────────┘
```

## 新方案中的音频采集

### 架构设计

在前后端分离方案中，音频采集保持不变，但通信方式改变：

```
┌─────────────────────────────────────────────────────────┐
│                    系统音频源                            │
├──────────────────────┬──────────────────────────────────┤
│   麦克风输入         │      扬声器输出                   │
│   (Microphone)       │      (Speaker Output)            │
└──────────────────────┴──────────────────────────────────┘
         │                           │
         ▼                           ▼
┌──────────────────────────────────────────────────────────┐
│              后端服务 (Python)                           │
│  • AudioRecorder (保持现有实现)                          │
│  • 麦克风采集: sr.Microphone()                           │
│  • 扬声器采集: WASAPI/BlackHole                          │
│  • 音频队列管理                                          │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│              IPC通信 (Tauri)                             │
│  • 后端通过事件推送转录结果                              │
│  • 前端通过命令控制后端                                  │
└──────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────┐
│              前端应用 (React/TypeScript)                 │
│  • 显示转录结果                                          │
│  • 显示音频可视化                                        │
│  • 提供设备选择界面                                      │
└──────────────────────────────────────────────────────────┘
```

### 关键特性

#### 1. 完整的音频采集支持

**麦克风采集**:
- ✅ 保持现有实现
- ✅ 支持Windows, macOS, Linux
- ✅ 自动检测默认麦克风
- ✅ 支持多个麦克风设备选择

**扬声器采集**:
- ✅ Windows: WASAPI Loopback (自动检测)
- ✅ macOS: BlackHole 虚拟设备 (需要用户安装)
- ✅ 支持设备选择和切换
- ✅ 自动故障恢复

#### 2. 设备管理

后端提供设备管理接口：

```python
# 获取可用设备列表
def get_audio_devices() -> Dict[str, List[AudioDevice]]:
    """
    返回系统中可用的音频设备
    
    Returns:
        {
            "microphones": [
                {"id": "default", "name": "Default Microphone", "index": 0},
                {"id": "usb_mic", "name": "USB Microphone", "index": 2}
            ],
            "speakers": [
                {"id": "default", "name": "Default Speaker (WASAPI)", "index": 1},
                {"id": "hdmi", "name": "HDMI Audio", "index": 3}
            ]
        }
    """
    pass

# 设置要使用的设备
def set_audio_device(device_type: str, device_id: str) -> bool:
    """
    设置要使用的音频设备
    
    Args:
        device_type: "microphone" 或 "speaker"
        device_id: 设备ID
    
    Returns:
        True if successful
    """
    pass
```

#### 3. 前端音频可视化

前端可以通过以下方式实现音频可视化：

**方案A: 后端推送音频数据**
- 后端通过事件推送原始音频数据
- 前端使用Web Audio API进行可视化
- 优点: 实时性好
- 缺点: 数据量大，网络开销大

**方案B: 前端采集音频**
- 前端通过Web Audio API采集麦克风音频
- 仅用于可视化显示
- 后端继续采集完整音频用于转录
- 优点: 网络开销小，实时性好
- 缺点: 无法显示扬声器音频可视化

**推荐方案**: 方案B
- 前端采集麦克风音频用于可视化
- 后端采集麦克风和扬声器音频用于转录
- 两者独立运行，互不影响

### 通信协议

#### 前端命令

```typescript
// 获取可用音频设备
invoke('get_audio_devices'): Promise<{
  microphones: AudioDevice[]
  speakers: AudioDevice[]
}>

// 设置音频设备
invoke('set_audio_device', {
  device_type: 'microphone' | 'speaker',
  device_id: string
}): Promise<string>

// 启动录制
invoke('start_recording', {
  mic_device?: string
  speaker_device?: string
}): Promise<string>

// 停止录制
invoke('stop_recording'): Promise<string>

// 获取转录结果
invoke('get_transcript'): Promise<TranscriptData>
```

#### 后端事件

```typescript
// 转录更新事件
listen('transcript-updated', (data: {
  source: 'microphone' | 'speaker'
  text: string
  timestamp: number
  confidence: number
}) => {})

// 音频设备变化事件
listen('audio-device-changed', (data: {
  device_type: 'microphone' | 'speaker'
  device_id: string
  device_name: string
}) => {})

// 音频错误事件
listen('audio-error', (data: {
  error: string
  device_type: 'microphone' | 'speaker'
  recovery_attempted: boolean
}) => {})
```

### 平台特定考虑

#### Windows

**优点**:
- WASAPI Loopback 是官方支持的方案
- 自动检测，无需用户配置
- 稳定可靠

**实现**:
```python
# 自动检测WASAPI loopback设备
def get_default_speaker_windows():
    with pyaudio.PyAudio() as p:
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
        default_speakers = p.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        
        # 查找对应的loopback设备
        for loopback in p.get_loopback_device_info_generator():
            if default_speakers["name"] in loopback["name"]:
                return loopback
        
        raise Exception("No loopback device found")
```

#### macOS

**挑战**:
- 需要用户手动安装BlackHole
- 需要系统级配置

**解决方案**:
1. 在安装指南中明确说明BlackHole安装步骤
2. 提供自动检测和错误提示
3. 提供备选方案（仅采集麦克风）

**实现**:
```python
# 检测BlackHole设备
def get_default_speaker_macos():
    p = pyaudio.PyAudio()
    try:
        for i in range(p.get_device_count()):
            dev = p.get_device_info_by_index(i)
            if "BlackHole" in dev["name"] and dev["maxInputChannels"] > 0:
                return dev
        
        # BlackHole未找到，提示用户
        raise Exception(
            "BlackHole device not found. "
            "Please install it with: brew install blackhole-2ch"
        )
    finally:
        p.terminate()
```

### 故障恢复

系统实现了自动故障恢复机制：

```python
# 设备恢复管理器
device_recovery_manager.register_device(
    "default_microphone",
    recovery_callback,
    device_config
)

# 当设备失败时自动尝试恢复
def _recover_microphone(device_id: str, error: Exception) -> bool:
    try:
        # 停止当前录制
        self.stop_recording()
        
        # 重新初始化设备
        new_source = sr.Microphone(sample_rate=16000)
        self.source = new_source
        
        # 测试新设备
        self.adjust_for_noise("Default Mic (Recovered)", "Testing...")
        
        return True
    except Exception:
        return False
```

## 总结

### 新方案的优势

1. **完整的音频采集支持**
   - 保持现有的麦克风和扬声器采集功能
   - 支持Windows和macOS平台
   - 自动设备检测和故障恢复

2. **灵活的设备管理**
   - 前端提供设备选择界面
   - 支持多个设备的切换
   - 实时设备变化通知

3. **实时数据推送**
   - 后端通过事件推送转录结果
   - 前端实时显示转录内容
   - 支持音频可视化

4. **跨平台一致性**
   - Windows和macOS提供一致的用户体验
   - 平台特定的实现细节隐藏在后端
   - 前端无需关心平台差异

### 实现建议

1. **第一阶段**: 保持现有音频采集实现不变
2. **第二阶段**: 创建IPC接口暴露音频采集功能
3. **第三阶段**: 前端通过Tauri命令调用后端接口
4. **第四阶段**: 实现设备管理和选择界面
5. **第五阶段**: 添加音频可视化功能

### 测试策略

1. **单元测试**: 测试设备检测和初始化
2. **集成测试**: 测试完整的音频采集流程
3. **属性测试**: 测试音频数据完整性和一致性
4. **跨平台测试**: 在Windows和macOS上验证功能
