# 实现计划：音频设备选择

## 概述

按照三层架构（Python 后端 → Tauri Rust 中间层 → React 前端）逐步实现音频设备选择功能。先修复后端数据格式，再扩展前端状态管理，最后构建 UI 组件并集成到主界面。

## 任务

- [x] 1. 修复后端设备列表返回格式
  - 在 `backend/ipc/message_handler.py` 的 `_handle_get_audio_devices` 方法中，为每个麦克风设备对象添加 `"deviceType": "microphone"` 字段，为每个扬声器设备对象添加 `"deviceType": "speaker"` 字段
  - 确保返回格式与前端 `AudioDevice` 类型（`id`、`name`、`deviceType`）完全匹配
  - _需求：1.2_

  - [x]* 1.1 为 `_handle_get_audio_devices` 编写属性测试
    - **属性 1：设备列表字段完整性**
    - 使用 Hypothesis 生成随机设备枚举场景，验证返回列表中每个设备对象都包含非空的 `id`、`name`、`deviceType` 字段，且 `deviceType` 只能是 `"microphone"` 或 `"speaker"`
    - **Validates: Requirements 1.2**

  - [x]* 1.2 为 `_handle_get_audio_devices` 异常处理编写属性测试
    - **属性 2：异常安全性**
    - 使用 Hypothesis 模拟各种异常（OSError、ImportError 等），验证处理器始终返回包含 `error` 字段的响应且 `microphones`/`speakers` 为空列表，不抛出未捕获异常
    - **Validates: Requirements 1.4**

- [x] 2. 扩展 Zustand Store 以支持设备选择状态
  - 在 `frontend/src/store/appStore.ts` 中新增 `selectedMicId: string | null`、`selectedSpeakerId: string | null` 状态字段及对应的 `setSelectedMicId`、`setSelectedSpeakerId` action
  - _需求：5.1, 5.2_

- [x] 3. 扩展 `useAudioRecording` Hook 以支持设备选择持久化
  - 在 `frontend/src/hooks/useAudioRecording.ts` 中增强 `selectDevice` 方法：
    1. 若当前正在录音，先调用 `stopRecording()`
    2. 调用 `setAudioDevice(deviceType, deviceId)`
    3. 成功后更新 Zustand store 中的 `selectedMicId` 或 `selectedSpeakerId`
    4. 若之前在录音，调用 `startRecording(deviceType)` 重启录音
    5. 若 `setAudioDevice` 失败，不更新 store，向上抛出错误
  - 在 hook 返回值中暴露 `selectedMicId` 和 `selectedSpeakerId`
  - _需求：2.3, 3.3, 4.3, 5.1_

  - [x]* 3.1 为 `selectDevice` 编写属性测试
    - **属性 3：设备切换操作顺序**
    - 使用 fast-check 生成随机录音状态（录音中/未录音）和随机 deviceType/deviceId，验证：录音中时 `stopRecording` 在 `setAudioDevice` 之前调用，`setAudioDevice` 成功后 `startRecording` 被调用
    - **Validates: Requirements 2.3, 3.3, 4.3**

  - [x]* 3.2 为设备切换失败时的状态回滚编写属性测试
    - **属性 4：设备切换失败时的状态回滚**
    - 使用 fast-check mock `setAudioDevice` 失败，验证 store 中的选中设备 id 保持切换前的值不变
    - **Validates: Requirements 4.4**

  - [x]* 3.3 为 Store 与 UI 同步编写属性测试
    - **属性 5：Store 与 UI 选中状态同步**
    - 使用 fast-check 生成随机设备选择操作序列，验证每次成功选择后 store 中的 `selectedMicId`/`selectedSpeakerId` 与最后一次成功选择的 deviceId 一致
    - **Validates: Requirements 5.1, 5.2**

- [x] 4. 创建 `AudioDeviceSelector` 组件
  - 新建 `frontend/src/components/AudioDeviceSelector.tsx`，实现：
    - 麦克风下拉菜单（MUI Select）：列出所有 `deviceType === 'microphone'` 的设备，value 绑定 `selectedMicId`
    - 扬声器下拉菜单（MUI Select）：列出所有 `deviceType === 'speaker'` 的设备，value 绑定 `selectedSpeakerId`
    - 刷新按钮：调用 `loadDevices()`
    - 加载状态（CircularProgress）：`isLoadingDevices` 为 true 时显示
    - 错误提示（Alert）：设备切换失败时显示错误信息
    - 空列表占位文本："无可用设备"
    - 设备切换时调用 `selectDevice(deviceType, deviceId)`，失败时恢复选中状态并显示错误
  - 在 `frontend/src/components/index.ts` 中导出该组件
  - _需求：1.5, 2.1, 2.5, 3.1, 3.5, 4.1, 4.4, 4.5_

  - [x]* 4.1 为 `AudioDeviceSelector` 编写单元测试
    - 测试两个下拉菜单的渲染（有设备时）
    - 测试空列表时显示"无可用设备"占位文本（需求 4.5）
    - 测试加载状态显示（需求 1.5）
    - 测试组件挂载时自动调用 `loadDevices`（需求 4.2）
    - _需求：1.5, 4.1, 4.2, 4.5_

  - [x]* 4.2 为设备选择调用参数编写属性测试
    - **属性 6：设备选择命令参数正确性**
    - 使用 fast-check 生成随机 deviceType（microphone/speaker）和 deviceId，验证用户选择后 `setAudioDevice` 被调用且传入参数与选择完全一致
    - **Validates: Requirements 2.1, 3.1**

  - [x]* 4.3 为刷新后选中状态保持编写属性测试
    - **属性 7：刷新后选中状态保持**
    - 使用 fast-check 生成随机设备列表和选中 id，验证刷新后若选中 id 仍在新列表中则保持选中状态
    - **Validates: Requirements 5.3**

- [x] 5. 将 `AudioDeviceSelector` 集成到主界面
  - 在 `frontend/src/App.tsx` 中，在控制面板（Controls）区域的 `Paper` 内添加 `AudioDeviceSelector` 组件
  - 将 `useAudioRecording` hook 返回的 `selectedMicId`、`selectedSpeakerId`、`selectDevice`、`devices`、`loadDevices`、`isLoadingDevices` 传递给 `AudioDeviceSelector`
  - _需求：4.1, 4.2_

- [x] 6. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请向用户反馈。

## 备注

- 标有 `*` 的子任务为可选测试任务，可在快速 MVP 阶段跳过 
- 每个任务引用了具体的需求条款以保证可追溯性
- 检查点确保增量验证
- 属性测试验证通用正确性，单元测试验证具体示例和边界条件
- 后端属性测试使用 Hypothesis（Python），前端属性测试使用 fast-check（TypeScript/Vitest）
