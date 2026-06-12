import { test, expect } from './fixtures';

test('simple test', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await expect(page).toHaveTitle(/Fugue/);
});
