---
name: frontend-test
description: 使用 Playwright 进行前端 E2E 测试和交互式测试探索。当用户提到"前端测试"、"E2E 测试"、"端到端测试"、"Playwright"、"测试前端"、"验证 UI"、"交互测试"或需要"检查页面元素"、"点击按钮"、"填写表单"、"截图对比"时使用此技能。
---

# Frontend Test

这个 Skill 用于使用 Playwright 对项目前端进行 E2E 测试和交互式测试探索。

## 项目信息

### 技术栈
- **框架**: React 19 + TypeScript
- **UI 库**: Material-UI (MUI)
- **构建工具**: Vite
- **测试运行端口**: http://localhost:5173/
- **前端目录**: `frontend/`

### 启动开发服务器

在运行测试之前，需要先启动开发服务器：

```bash
cd frontend && npm run dev
```

## 核心功能

### 1. E2E 测试编写与运行

#### 编写测试文件
- 在 `frontend/tests/` 目录创建 Playwright 测试文件
- 测试文件命名规范: `*.e2e.ts` 或 `*.spec.ts`

#### 测试结构示例
```typescript
import { test, expect } from '@playwright/test';

test.describe('功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:5173/');
  });

  test('应该显示主界面', async ({ page }) => {
    await expect(page.locator('h1')).toBeVisible();
  });
});
```

#### 运行测试
```bash
# 运行所有测试
npx playwright test

# 运行特定文件
npx playwright test tests/example.spec.ts

# 打开 Playwright UI 模式
npx playwright test --ui
```

### 2. 交互式测试探索

使用 Playwright MCP 或直接使用 Playwright 进行页面探索和调试：

#### 常用操作
- **导航**: `page.goto(url)`
- **点击**: `page.click(selector)`
- **填写表单**: `page.fill(selector, text)`
- **等待元素**: `page.waitForSelector(selector)`
- **截图**: `page.screenshot({ path: 'screenshot.png' })`
- **获取文本**: `page.textContent(selector)`
- **获取属性**: `page.getAttribute(selector, attribute)`

#### 调试模式
```bash
# 交互式调试
npx playwright test --ui

# 只运行一个测试
npx playwright test tests/example.spec.ts --grep "测试名称"
```

### 3. 视觉回归测试（可选扩展）

#### 截图对比
```typescript
test('视觉回归测试', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await expect(page).toHaveScreenshot('homepage.png');
});
```

## 测试最佳实践

### 选择器优先级
1. **data-testid**: 最稳定 (推荐添加)
   ```tsx
   <button data-testid="submit-button">Submit</button>
   ```
2. **aria-label**: 无障碍友好
   ```tsx
   <button aria-label="Submit form">Submit</button>
   ```
3. **role**: 语义化
   ```tsx
   <button role="submit">Submit</button>
   ```
4. **文本内容**: 易读但脆弱
   ```tsx
   <button>Submit</button>
   ```

### 等待策略
- 优先使用 `expect` 的自动等待
- 避免硬编码 `sleep()`
- 使用 `waitForSelector` 处理动态内容

### 测试组织
```
frontend/
├── tests/
│   ├── e2e/           # E2E 测试
│   │   ├── example.spec.ts
│   │   └── ...
│   ├── components/    # 组件测试
│   │   └── ...
│   └── playwright.config.ts
└── ...
```

## 配置 Playwright

### 安装 Playwright
```bash
cd frontend
npm init playwright@latest
# 或
npm install -D @playwright/test
npx playwright install chromium
```

### playwright.config.ts 示例
```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

## 常用命令速查

| 操作 | 命令 |
|------|------|
| 安装 Playwright | `npm init playwright@latest` |
| 运行所有测试 | `npx playwright test` |
| UI 模式 | `npx playwright test --ui` |
| 交互式调试 | `npx playwright codegen` |
| 生成测试 | `npx playwright test --generate` |
| 查看报告 | `npx playwright show-report` |

## 触发条件

当用户提及以下内容时自动触发：
- "前端测试"、"E2E 测试"、"端到端测试"
- "Playwright"、"测试前端"
- "验证 UI"、"交互测试"
- "检查页面元素"、"点击按钮"、"填写表单"
- "截图对比"、"视觉回归"
- "测试覆盖"、"写测试"

## 注意事项

1. **先启动服务器**: 确保 `npm run dev` 已运行
2. **端口检查**: 默认 5173 端口可能被占用
3. **CI 环境**: 在 CI 中使用 `webServer` 配置自动启动
4. **清理状态**: 每个测试前确保干净的应用状态
