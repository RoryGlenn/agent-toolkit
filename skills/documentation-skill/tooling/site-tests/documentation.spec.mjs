import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { writeFile } from 'node:fs/promises';

test('documentation page loads and has no detected accessibility violations', async ({ page }, testInfo) => {
  const target = process.env.DOC_AGENT_BASE_URL;
  if (!target) {
    throw new Error('Set DOC_AGENT_BASE_URL to the documentation preview page you intend to check.');
  }
  const readySelector = process.env.DOC_AGENT_READY_SELECTOR?.trim();
  if (!readySelector) {
    throw new Error('Set DOC_AGENT_READY_SELECTOR to a unique element visible only when documentation content is ready.');
  }
  const url = new URL(target);
  if (!['http:', 'https:'].includes(url.protocol)) {
    throw new Error('DOC_AGENT_BASE_URL must use http or https.');
  }
  const response = await page.goto(url.href, { waitUntil: 'domcontentloaded' });
  expect(response, 'The page must return an HTTP response').not.toBeNull();
  expect(response.ok(), 'The preview should return a successful HTTP status').toBeTruthy();
  await page.locator(readySelector).waitFor({ state: 'visible', timeout: 10_000 });
  const screenshotPath = testInfo.outputPath('rendered-page.png');
  await page.screenshot({ path: screenshotPath, fullPage: true });
  await testInfo.attach('rendered-page', {
    path: screenshotPath,
    contentType: 'image/png',
  });
  const results = await new AxeBuilder({ page }).analyze();
  const reportPath = testInfo.outputPath('accessibility-results.json');
  await writeFile(reportPath, JSON.stringify(results, null, 2));
  await testInfo.attach('accessibility-results', {
    path: reportPath,
    contentType: 'application/json',
  });
  expect(results.violations, JSON.stringify(results.violations, null, 2)).toEqual([]);
});
