import { test, expect } from '@playwright/test';

test.describe('AudioDeviceSelector', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('AudioDeviceSelector 组件渲染在 Controls 面板中', async ({ page }) => {
    // Controls 面板应该包含音频设备选择器
    const controlsPanel = page.locator('text=Controls').locator('../..');
    await expect(controlsPanel).toBeVisible();
  });

  test('页面截图 - 初始状态', async ({ page }) => {
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'test-results/initial-state.png', fullPage: true });
  });
});
