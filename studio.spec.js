const { test, expect } = require('@playwright/test');

test('Studio page loads without runtime errors', async ({ page }) => {
  const errors = [];
  page.on('pageerror', err => errors.push(`pageerror:${err.message}`));
  page.on('console', msg => {
    if (msg.type() === 'error') errors.push(`console:${msg.text()}`);
  });
  page.on('requestfailed', req => errors.push(`requestfailed:${req.url()}::${req.failure()?.errorText || 'unknown'}`));

  await page.goto('http://127.0.0.1:8123/avodah_studio.html', { waitUntil: 'load', timeout: 60000 });
  await page.waitForTimeout(2000);
  await expect(page.locator('h1')).toHaveText(/AVODAH AUDIO STUDIO/i);
  await expect(page.locator('#visualStatus')).toContainText('Stage ready');
  console.log('RUNTIME_ERRORS:', JSON.stringify(errors));
  expect(errors).toEqual([]);
});
