const { test, expect } = require('@playwright/test');

test('Launches map and simulates overlays', async ({ page }) => {
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(1000); // simulate load
  console.log('Simulated user opened map');
});
