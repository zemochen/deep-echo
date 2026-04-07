# 需求文档

## 简介

本功能为 DeepEcho 桌面应用（Tauri + React + Python）添加音频设备选择能力，允许用户在应用界面中选择用于录音的麦克风（输入设备）和扬声器（输出/环回设备）。当前应用自动使用系统默认设备，缺乏用户手动选择的入口。该功能将在控制面板区域提供设备选择下拉菜单，并在切换设备时正确重启录音流。

## 词汇表

- **AudioDeviceSelector**：负责渲染设备选择下拉菜单的前端 React 组件
- **DeviceList**：从后端获取的可用音频设备列表，包含麦克风和扬声器两类
- **MicDevice**：麦克风输入设备，用于捕获用户语音
- **SpeakerDevice**：扬声器环回设备，用于捕获系统播放的音频
- **MessageHandler**：Python 后端 IPC 消息处理器，负责路由前端命令
- **AudioRecorder**：Python 后端音频录制模块（DefaultMicRecorder / DefaultSpeakerRecorder）
- **TauriService**：前端封装 Tauri invoke 调用的服务层
- **useAudioRecording**：前端管理录音状态和设备操作的 React Hook

---

## 需求

### 需求 1：获取可用音频设备列表

**用户故事：** 作为用户，我希望应用能列出系统中所有可用的麦克风和扬声器设备，以便我知道有哪些设备可以选择。

#### 验收标准

1. WHEN 用户打开应用或点击刷新设备按钮，THE **AudioDeviceSelector** SHALL 向后端发送 `get_audio_devices` 命令并获取设备列表
2. WHEN **MessageHandler** 收到 `get_audio_devices` 命令，THE **MessageHandler** SHALL 返回包含所有可用麦克风设备和扬声器设备的列表，每个设备包含 `id`、`name` 和 `deviceType` 字段
3. WHEN 系统中没有可用的麦克风设备，THE **MessageHandler** SHALL 返回空的麦克风列表并附带警告信息
4. IF 枚举设备过程中发生异常，THEN THE **MessageHandler** SHALL 返回错误信息并提供空的设备列表，而不是抛出未处理异常
5. THE **AudioDeviceSelector** SHALL 在设备列表加载期间显示加载状态指示

### 需求 2：选择麦克风设备

**用户故事：** 作为用户，我希望能从下拉菜单中选择指定的麦克风设备，以便使用我偏好的输入设备进行录音。

#### 验收标准

1. WHEN 用户从麦克风下拉菜单中选择一个设备，THE **AudioDeviceSelector** SHALL 调用 `set_audio_device` 命令，传入 `device_type: "microphone"` 和所选设备的 `device_id`
2. WHEN **MessageHandler** 收到 `set_audio_device` 命令且 `device_type` 为 `"microphone"`，THE **MessageHandler** SHALL 停止当前录音（如有），重置麦克风录制器，并返回成功状态
3. WHEN 麦克风设备切换成功，THE **useAudioRecording** SHALL 使用新选中的设备重新启动录音
4. IF 指定的 `device_id` 对应的设备不存在或不可用，THEN THE **MessageHandler** SHALL 返回包含错误描述的错误响应
5. THE **AudioDeviceSelector** SHALL 在界面上高亮显示当前选中的麦克风设备

### 需求 3：选择扬声器（环回）设备

**用户故事：** 作为用户，我希望能选择用于捕获系统音频的扬声器环回设备，以便转录正在播放的音频内容。

#### 验收标准

1. WHEN 用户从扬声器下拉菜单中选择一个设备，THE **AudioDeviceSelector** SHALL 调用 `set_audio_device` 命令，传入 `device_type: "speaker"` 和所选设备的 `device_id`
2. WHEN **MessageHandler** 收到 `set_audio_device` 命令且 `device_type` 为 `"speaker"`，THE **MessageHandler** SHALL 停止当前录音（如有），重置扬声器录制器，并返回成功状态
3. WHEN 扬声器设备切换成功，THE **useAudioRecording** SHALL 使用新选中的设备重新启动录音
4. IF 系统不支持音频环回捕获（如 macOS 未安装虚拟音频驱动），THEN THE **MessageHandler** SHALL 返回包含说明的错误响应
5. THE **AudioDeviceSelector** SHALL 在界面上高亮显示当前选中的扬声器设备

### 需求 4：设备选择 UI 集成

**用户故事：** 作为用户，我希望设备选择控件集成在应用主界面的控制面板中，以便在不离开主界面的情况下切换设备。

#### 验收标准

1. THE **AudioDeviceSelector** SHALL 在应用的控制面板（Controls）区域渲染麦克风选择下拉菜单和扬声器选择下拉菜单
2. WHEN 应用启动，THE **AudioDeviceSelector** SHALL 自动加载设备列表并将当前使用的设备标记为选中状态
3. WHEN 录音正在进行时用户切换设备，THE **AudioDeviceSelector** SHALL 先停止当前录音，完成设备切换后再自动重新开始录音
4. IF 设备切换失败，THEN THE **AudioDeviceSelector** SHALL 在界面上显示错误提示，并恢复到切换前的设备选中状态
5. WHERE 设备列表为空，THE **AudioDeviceSelector** SHALL 显示"无可用设备"的提示文本，而不是空白下拉菜单

### 需求 5：设备选择状态持久化

**用户故事：** 作为用户，我希望我选择的设备在应用会话期间保持不变，以便不必每次重启应用都重新选择设备。

#### 验收标准

1. WHEN 用户成功选择一个设备，THE **useAudioRecording** SHALL 将所选设备的 `device_id` 和 `device_type` 保存到应用状态（Zustand store）中
2. WHILE 应用运行期间，THE **AudioDeviceSelector** SHALL 始终从应用状态中读取当前选中的设备并保持 UI 同步
3. WHEN 设备列表刷新后，IF 之前选中的设备仍在列表中，THEN THE **AudioDeviceSelector** SHALL 保持该设备的选中状态
