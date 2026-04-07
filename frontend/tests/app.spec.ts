import { test, expect } from '@playwright/test';

test.describe('DeepEcho App', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('页面标题正确', async ({ page }) => {
    await expect(page).toHaveTitle('frontend-temp');
  });

  test('AppBar 显示应用名称', async ({ page }) => {
    await expect(page.getByText('DeepEcho - Real-time Voice AI Assistant')).toBeVisible();
  });

  test('非 Tauri 环境显示警告横幅', async ({ page }) => {
    await expect(page.getByText('Not Running in Tauri Environment')).toBeVisible();
  });

  test('Transcript 区域可见', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Transcript' })).toBeVisible();
  });

  test('AI Response 区域可见', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'AI Response' })).toBeVisible();
  });

  test('Status 面板可见', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Status' })).toBeVisible();
  });

  test('Controls 面板可见', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'Controls' })).toBeVisible();
  });

  test('AI Provider 面板可见', async ({ page }) => {
    await expect(page.getByRole('heading', { name: 'AI Provider' })).toBeVisible();
  });

  test('Debug Info 显示 Transcript 数量', async ({ page }) => {
    await expect(page.getByText('Transcript 数量: 0')).toBeVisible();
  });
});
