import { test, expect } from './fixtures';

// 辅助函数：登录并创建工作流
async function setupWorkflow(page: any) {
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
}

test.describe('画布编辑器', () => {
  test.beforeEach(async ({ page }) => {
    await setupWorkflow(page);
  });

  test('显示画布节点库', async ({ page }) => {
    // 验证节点库面板存在
    await expect(page.getByText('节点库')).toBeVisible();
    await expect(page.getByText('Agent', { exact: true })).toBeVisible();
    await expect(page.getByText('Task', { exact: true })).toBeVisible();
  });

  test('添加Agent节点', async ({ page }) => {
    // 拖拽Agent节点到画布
    await page.dragAndDrop('text=Agent >> nth=0', '.react-flow');

    // 验证画布中有节点
    await expect(page.locator('.react-flow__node').first()).toBeVisible({ timeout: 10000 });
  });

  test('添加Task节点', async ({ page }) => {
    // 拖拽Task节点到画布
    await page.dragAndDrop('text=Task >> nth=0', '.react-flow');

    // 验证画布中有节点
    await expect(page.locator('.react-flow__node').first()).toBeVisible({ timeout: 10000 });
  });

  test('选择节点显示属性面板', async ({ page }) => {
    // 拖拽Agent节点到画布
    await page.dragAndDrop('text=Agent >> nth=0', '.react-flow');
    await expect(page.locator('.react-flow__node').first()).toBeVisible({ timeout: 10000 });

    // 点击节点
    await page.locator('.react-flow__node').first().click();

    // 验证属性面板显示（编辑器右侧）
    await expect(page.getByText('属性', { exact: false })).toBeVisible();
  });

  test('画布保存按钮存在', async ({ page }) => {
    // 验证保存按钮存在
    await expect(page.getByRole('button', { name: '保存' })).toBeVisible();
  });
});
