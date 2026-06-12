import { test, expect } from './fixtures';

test.describe('用户认证', () => {
  test('注册新用户', async ({ page }) => {
    const ts = Date.now();
    await page.goto('/register');

    await page.fill('input[name="username"]', `testuser_${ts}`);
    await page.fill('input[name="email"]', `test_${ts}@example.com`);
    await page.fill('input[name="password"]', 'TestPass123');
    await page.fill('input[name="confirmPassword"]', 'TestPass123');

    await page.click('button[type="submit"]');

    await expect(page).not.toHaveURL(/register/, { timeout: 15000 });
  });

  test('登录已有用户', async ({ page }) => {
    const ts = Date.now();
    await page.goto('/register');
    await page.fill('input[name="username"]', `testuser_${ts}`);
    await page.fill('input[name="email"]', `test_${ts}@example.com`);
    await page.fill('input[name="password"]', 'TestPass123');
    await page.fill('input[name="confirmPassword"]', 'TestPass123');
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL(/(login|\/$)/, { timeout: 15000 });

    await page.goto('/login');
    await page.fill('input[name="email"]', `test_${ts}@example.com`);
    await page.fill('input[name="password"]', 'TestPass123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/(dashboard|\/$)/, { timeout: 15000 });
    await expect(page.getByRole('button', { name: '新建工作流' }).first()).toBeVisible();
  });

  test('未登录时重定向到登录页', async ({ page }) => {
    await page.goto('/dashboard');

    await expect(page).toHaveURL(/login/, { timeout: 15000 });
  });
});
