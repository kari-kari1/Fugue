import { test as base } from '@playwright/test';

/**
 * 扩展 Playwright test，自动拦截图片/字体/媒体请求。
 * 纯文本模型不需要这些资源，跳过可加速测试。
 */
export const test = base.extend<{}>({
  page: async ({ page }, use) => {
    await page.route('**/*.{png,jpg,jpeg,gif,webp,svg,ico,bmp,avif}', (route) => route.abort());
    await page.route('**/*.{woff,woff2,ttf,otf,eot}', (route) => route.abort());
    await page.route('**/fonts.googleapis.com/**', (route) => route.abort());
    await page.route('**/fonts.gstatic.com/**', (route) => route.abort());
    await use(page);
  },
});

export { expect } from '@playwright/test';
