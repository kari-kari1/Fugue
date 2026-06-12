import { test, expect } from './fixtures';

// 辅助函数：登录并创建工作流
async function setupFullWorkflow(page: any) {
  const ts = Date.now();
  const email = `test_${ts}@example.com`;
  const password = 'TestPass123';

  await page.goto('/register');
  await page.fill('input[name="username"]', `user_${ts}`);
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.fill('input[name="confirmPassword"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/(login|\/$)/, { timeout: 15000 });

  await page.goto('/login');
  await page.fill('input[name="email"]', email);
  await page.fill('input[name="password"]', password);
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL(/(dashboard|\/$)/, { timeout: 15000 });

  await page.click('button:has-text("新建工作流")');
  await expect(page).toHaveURL(/crew/, { timeout: 15000 });

  return { email, password };
}

test.describe('执行监控', () => {
  test('编辑器显示运行按钮', async ({ page }) => {
    await setupFullWorkflow(page);

    // 验证编辑器有运行工作流按钮
    await expect(page.getByRole('button', { name: '运行工作流' })).toBeVisible();
  });

  test('编辑器显示返回按钮', async ({ page }) => {
    await setupFullWorkflow(page);

    // 验证有返回按钮
    await expect(page.getByRole('button', { name: '返回' })).toBeVisible();
  });

  test('编辑器显示节点库', async ({ page }) => {
    await setupFullWorkflow(page);

    // 验证节点库存在
    await expect(page.getByText('节点库')).toBeVisible();
  });

  test('编辑器显示画布', async ({ page }) => {
    await setupFullWorkflow(page);

    // 验证React Flow画布存在
    await expect(page.locator('.react-flow')).toBeVisible();
  });
});
