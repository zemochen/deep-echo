---
name: frontend-test
description: 使用 Playwright 为 DeepEcho 项目自动生成并运行前端 E2E 测试和组件测试。当用户提到"前端测试"、"E2E 测试"、"端到端测试"、"Playwright"、"测试前端"、"验证 UI"、"写测试"、"生成测试"、"添加测试覆盖"、"组件测试"、"页面测试"、"交互测试"时触发。可自动分析组件结构和页面布局，生成对应的测试代码。
---

# Frontend Test - DeepEcho E2E 测试 Skill

## 项目信息

### 技术栈
- **框架**: React 19 + TypeScript
- **UI 库**: Material-UI (MUI) v7
- **状态管理**: Zustand v5
- **构建工具**: Vite
- **测试框架**: Playwright (E2E) + Vitest (单元测试)
- **前端目录**: `frontend/`
- **测试目录**: `frontend/tests/`
- **开发服务器**: `http://localhost:5173`

### 项目文件结构
```
frontend/
├── src/
│   ├── components/
│   │   ├── TranscriptDisplay.tsx    # 实时转录显示
│   │   ├── ResponseDisplay.tsx       # AI 响应显示
│   │   ├── ControlPanel.tsx          # 控制面板 (冻结/更新间隔/清除)
│   │   ├── ProviderSelector.tsx      # AI 提供商和模型选择
│   │   ├── StatusIndicator.tsx       # 系统状态指示
│   │   └── AudioDeviceSelector.tsx   # 音频设备选择
│   ├── store/
│   │   └── appStore.ts               # Zustand 全局状态
│   ├── hooks/
│   │   ├── useTranscript.ts
│   │   ├── useResponse.ts
│   │   ├── useAudioRecording.ts
│   │   └── useTauriCommand.ts
│   └── types/
│       ├── api.ts                    # TranscriptData, ResponseData 等
│       ├── audio.ts                  # AudioDevice 类型
│       └── system.ts                 # SystemStatus 类型
├── tests/                            # Playwright 测试
├── playwright.config.ts              # Playwright 配置
└── vite.config.ts                    # Vite + Vitest 配置
```

## 核心原则：自动生成测试

本 skill 的核心能力是根据组件定义和页面结构**自动生成**测试代码。遵循以下流程：

1. **读取组件源码** → 分析 props 接口、渲染结构、条件分支
2. **生成测试模板** → 根据组件结构生成完整的 spec 文件
3. **运行验证** → 确保测试通过，截图比对

---

## 一、组件测试自动生成

### 通用测试模式

每个组件测试应覆盖：
- **渲染测试**: 组件在默认 props 下正确渲染
- **条件渲染测试**: 不同条件分支的渲染结果 (如 `frozen` 状态, 空数据状态)
- **交互测试**: 按钮点击、下拉选择、滑块拖动等用户操作

### 各组件测试模板

#### 1. TranscriptDisplay

```typescript
import { test, expect } from '@playwright/test';

test.describe('TranscriptDisplay', () => {
  test('无转录时显示空状态提示', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('No transcripts yet. Start recording to see transcriptions appear here.')).toBeVisible();
  });

  test('frozen 状态时显示 Freeze 标签', async ({ page }) => {
    await page.goto('/');
    // 点击 Freeze Display 按钮
    await page.getByRole('button', { name: /Freeze Display/i }).click();
    await expect(page.getByText('Display Frozen')).toBeVisible();
  });
});
```

#### 2. ResponseDisplay

**关键测试点**:
- 空状态: "No AI responses yet"
- 显示响应列表时每条有 SmartToy 图标
- frozen 状态标签

```typescript
test('无响应时显示空状态提示', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('No AI responses yet. Responses will appear here as they are generated.')).toBeVisible();
});
```

#### 3. ControlPanel

**关键测试点**:
- 三个子区域: Display Control, Update Interval Slider, Context Management
- Freeze/Unfreeze 按钮切换 (text + color)
- Slider 默认值 5s, 范围 1-30
- Clear Context 按钮

```typescript
test.describe('ControlPanel', () => {
  test('Freeze 按钮点击切换状态', async ({ page }) => {
    await page.goto('/');
    const btn = page.getByRole('button', { name: /Freeze Display/i });
    await expect(btn).toBeVisible();
    await btn.click();
    await expect(page.getByRole('button', { name: /Unfreeze Display/i })).toBeVisible();
  });

  test('Slider 调整更新间隔', async ({ page }) => {
    await page.goto('/');
    // MUI Slider 通过 role 定位
    const slider = page.getByRole('slider');
    await expect(slider).toBeVisible();
    // 验证默认显示 "Update Interval: 5s"
    await expect(page.getByText(/Update Interval: 5s/)).toBeVisible();
  });

  test('Clear Context 按钮存在', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('button', { name: /Clear Context/i })).toBeVisible();
  });
});
```

#### 4. ProviderSelector

**关键测试点**:
- 两个 Select 下拉: AI Provider 和 Model
- 默认值: DeepSeek / deepseek-chat
- 切换 Provider 自动切换 Model
- Provider 选项: OpenAI, Claude, DeepSeek, GLM, Grok

```typescript
test.describe('ProviderSelector', () => {
  test('默认选中 DeepSeek', async ({ page }) => {
    await page.goto('/');
    // MUI Select 的触发方式: 点击后出现 MenuItem
    const providerSelect = page.getByLabel('AI Provider');
    await expect(providerSelect).toHaveText('DeepSeek');
  });

  test('切换 AI Provider', async ({ page }) => {
    await page.goto('/');
    await page.getByLabel('AI Provider').click();
    await page.getByRole('option', { name: 'Claude' }).click();
    // 验证 Model 自动切换到 claude-3-opus
    await expect(page.getByLabel('Model')).toHaveText('claude-3-opus');
  });
});
```

#### 5. StatusIndicator

**关键测试点**:
- 初始状态: Ready (success 颜色)
- 状态文字根据 state 变化: idle→Ready, recording→Recording
- status.message 显示为 Alert

```typescript
test.describe('StatusIndicator', () => {
  test('初始状态显示 Ready', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('Ready')).toBeVisible();
  });

  test('状态信息 Alert 可见', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('System is ready')).toBeVisible();
  });
});
```

#### 6. AudioDeviceSelector

**关键测试点**:
- 标题 "AudioDevices"
- 刷新按钮 (Refresh Device)
- 麦克风下拉 (label: 麦克风)
- Speaker 下拉 (label: Speaker)
- 加载状态显示 CircularProgress

```typescript
test.describe('AudioDeviceSelector', () => {
  test('标题和刷新按钮存在', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByText('AudioDevices')).toBeVisible();
    await expect(page.getByLabel('Refresh Device')).toBeVisible();
  });

  test('设备选择器渲染在 Controls 面板中', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByLabel('Refresh Device')).toBeVisible();
    await expect(page.getByLabel('麦克风')).toBeVisible();
    await expect(page.getByLabel('Speaker')).toBeVisible();
  });
});
```

### MUI 组件测试最佳实践

| MUI 组件 | 定位方式 | 示例 |
|---------|---------|------|
| **Button** | `getByRole('button', { name: /text/i })` | 图标按钮用 `getByLabel` |
| **Select** | `getByLabel('label').click()` → `getByRole('option')` | 注意异步弹出 |
| **Slider** | `getByRole('slider')` | 通过 `fill` 或键盘操作 |
| **Alert** | `getByRole('alert')` 或 `getByText` | MUI Alert 有 role="alert" |
| **Chip** | `getByText('label')` | 用于状态标签 |
| **Typography** | `getByText(/regex/i)` | 注意 MUI variant 影响 DOM |
| **IconButton** | `getByLabel('aria-label')` | 必须设置 aria-label |
| **TextField** | `getByLabel('label')` 或 `getByRole('textbox')` | |
| **Paper** | 无法直接定位, 用内部文本定位 | 通过内容反推 |

### 处理 Tauri 环境检测

应用加载时会检测 Tauri 环境。在纯浏览器中运行时会显示橙色警告横幅:
```
"⚠️ Not Running in Tauri Environment"
```

测试中应包含对此警告的处理:

```typescript
test('非 Tauri 环境显示警告横幅', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Not Running in Tauri Environment')).toBeVisible();
});
```

---

## 二、E2E 页面流程测试

### 全页面测试模板

```typescript
import { test, expect } from '@playwright/test';

test.describe('DeepEcho App - 完整页面测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('页面加载所有核心区域', async ({ page }) => {
    // Header
    await expect(page.getByRole('heading', { name: /DeepEcho/i })).toBeVisible();
    
    // 核心面板
    const sections = ['Transcript', 'AI Response', 'Status', 'Controls', 'AI Provider', 'Debug Info'];
    for (const section of sections) {
      await expect(page.getByRole('heading', { name: section })).toBeVisible();
    }
  });

  test('页面标题正确', async ({ page }) => {
    await expect(page).toHaveTitle('frontend-temp');
  });

  test('完整交互流程: Freeze → Adjust Slider → Clear Context', async ({ page }) => {
    // 1. Freeze Display
    await page.getByRole('button', { name: /Freeze Display/i }).click();
    await expect(page.getByText('Display Frozen')).toHaveCount(2); // Transcript + Response

    // 2. Slider is disabled when frozen
    await expect(page.getByRole('slider')).toBeDisabled();

    // 3. Unfreeze
    await page.getByRole('button', { name: /Unfreeze Display/i }).click();
    await expect(page.getByRole('slider')).toBeEnabled();

    // 4. Clear Context
    await page.getByRole('button', { name: /Clear Context/i }).click();
    await expect(page.getByText('Transcript 数量: 0')).toBeVisible();
  });

  test('切换 AI Provider 流程', async ({ page }) => {
    // 1. 当前默认 DeepSeek
    await expect(page.getByLabel('AI Provider')).toHaveText('DeepSeek');
    await expect(page.getByLabel('Model')).toHaveText('deepseek-chat');

    // 2. 切换到 Claude → Model 自动切换
    await page.getByLabel('AI Provider').click();
    await page.getByRole('option', { name: 'Claude' }).click();
    await expect(page.getByLabel('Model')).toHaveText('claude-3-opus');

    // 3. 切换到 OpenAI → Model 自动切换
    await page.getByLabel('AI Provider').click();
    await page.getByRole('option', { name: 'OpenAI' }).click();
    await expect(page.getByLabel('Model')).toHaveText('gpt-4');
  });

  test('Debug Info 显示初始状态', async ({ page }) => {
    await expect(page.getByText('Transcript 数量: 0')).toBeVisible();
    await expect(page.getByText('Response 数量: 0')).toBeVisible();
  });
});
```

### 截图测试 (视觉回归)

```typescript
test('首页截图 - 初始状态', async ({ page }) => {
  await page.goto('/');
  await page.waitForLoadState('networkidle');
  await page.screenshot({ path: 'test-results/homepage-initial.png', fullPage: true });
});

test('Freeze 状态截图', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Freeze Display/i }).click();
  await page.waitForTimeout(500); // 等待渲染
  await page.screenshot({ path: 'test-results/homepage-frozen.png', fullPage: true });
});
```

---

## 三、自动生成测试的工作流

### 从组件生成测试

当需要为某个组件生成测试时:

1. **分析组件**: 读取组件源码 → 识别 props、条件渲染、交互元素
2. **生成基本测试文件**: 使用上面的组件模板
3. **运行验证**: `cd frontend && npx playwright test tests/<file>.spec.ts`
4. **截图验证**: 确认渲染符合预期

### 添加 data-testid 的建议

对于交互测试场景，建议在关键元素添加 `data-testid`:

| 元素 | data-testid 建议 |
|------|-----------------|
| Transcript Panel | `transcript-panel` |
| Response Panel | `response-panel` |
| Status Panel | `status-panel` |
| Controls Panel | `controls-panel` |
| Provider Panel | `provider-panel` |
| Debug Info Panel | `debug-panel` |
| Freeze Button | `freeze-btn` |
| Clear Button | `clear-btn` |
| Mic Select | `mic-select` |
| Speaker Select | `speaker-select` |

添加方式:
```tsx
<Paper data-testid="transcript-panel" elevation={2} sx={{ p: 3 }}>
```

使用方式:
```typescript
await expect(page.getByTestId('transcript-panel')).toBeVisible();
```

---

## 四、运行测试

### 常用命令

```bash
# 在 frontend 目录下操作
cd frontend

# 运行所有 Playwright 测试
npx playwright test

# 运行特定文件
npx playwright test tests/app.spec.ts

# UI 模式 (交互式)
npx playwright test --ui

# 调试模式 (带 Playwright Inspector)
npx playwright test --debug

# 代码生成器 (录制测试)
npx playwright codegen http://localhost:5173

# 显示 HTML 报告
npx playwright show-report
```

### CI 集成

在 CI 环境中，Playwright 配置会自动处理:
- `retries: 2` - 失败自动重试 2 次
- `workers: 1` - 单 worker 避免资源竞争
- `webServer` - 自动启动开发服务器

---

## 五、测试模式汇编

### 页面元素定位速查

| 元素 | 定位方式 |
|------|---------|
| AppBar 标题 | `getByText('DeepEcho - Real-time Voice AI Assistant')` |
| Tauri 警告 | `getByText('Not Running in Tauri Environment')` |
| Transcript 标题 | `getByRole('heading', { name: 'Transcript' })` |
| AI Response 标题 | `getByRole('heading', { name: 'AI Response' })` |
| Status 标题 | `getByRole('heading', { name: 'Status' })` |
| Controls 标题 | `getByRole('heading', { name: 'Controls' })` |
| AI Provider 标题 | `getByRole('heading', { name: 'AI Provider' })` |
| Debug Info 标题 | `getByRole('heading', { name: 'Debug Info' })` |
| Freeze 按钮 | `getByRole('button', { name: /Freeze Display/i })` |
| Unfreeze 按钮 | `getByRole('button', { name: /Unfreeze Display/i })` |
| Clear Context 按钮 | `getByRole('button', { name: /Clear Context/i })` |
| AI Provider Select | `getByLabel('AI Provider')` |
| Model Select | `getByLabel('Model')` |
| Update Interval Slider | `getByRole('slider')` |
| Transcript 数量 | `getByText('Transcript 数量: ')` |
| Response 数量 | `getByText('Response 数量: ')` |
| Display Frozen Chip | `getByText('Display Frozen')` |
| Ready 状态 | `getByText('Ready')` |

### 检查列表

- [ ] 每个组件测试空状态 (empty/loading)
- [ ] 每个组件测试条件渲染 (如 frozen 状态)
- [ ] 每个交互元素测试点击/选择
- [ ] 页面 E2E 测试覆盖核心用户流程
- [ ] 截图测试在关键状态保存视觉快照

## 触发条件

当用户提及以下内容时自动触发：
- "前端测试"、"E2E 测试"、"端到端测试"
- "Playwright"、"测试前端"、"写测试"、"生成测试"
- "验证 UI"、"交互测试"
- "组件测试"、"页面测试"
- "检查页面元素"、"点击按钮"、"填写表单"
- "截图对比"、"视觉回归"
- "测试覆盖"、"添加测试"
- "自动生成测试"、"测试模板"
