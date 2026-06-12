import { test, expect } from './fixtures';

// 辅助函数：登录
async function login(page: any) {
  const ts = Date.now();
  const email = `test_${ts}@example.com`;
  const password = 'TestPass123';

  // 注册
  await page.goto('/register');
  await page.fill('input[name="username"]', `user_${ts}`);
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.fill('input[name="confirmPassword"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/(login|\/$)/, { timeout: 15000 });

  // 登录
  await page.goto('/login');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/(dashboard|\/$)/, { timeout: 15000 });

  return { email, password };
}

test.describe('工作流管理', () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test('创建新工作流', async ({ page }) => {
    // 点击新建工作流按钮（直接导航到编辑器）
    await page.click('button:has-text("新建工作流")');

    // 验证跳转到编辑器
    await expect(page).toHaveURL(/crew/, { timeout: 15000 });
  });

  test('查看工作流列表', async ({ page }) => {
    // 首页应该显示工作流列表区域
    await page.goto('/');

    // 验证有"新建工作流"按钮（说明Dashboard正常渲染）
    await expect(page.locator('button:has-text("新建工作流")')).toBeVisible();
  });

  test('编辑工作流', async ({ page }) => {
    // 先创建工作流
    await page.click('button:has-text("新建工作流")');
    await expect(page).toHaveURL(/crew/, { timeout: 15000 });

    // 验证编辑器页面有保存按钮
    await expect(page.locator('button:has-text("保存")')).toBeVisible();
  });
});
