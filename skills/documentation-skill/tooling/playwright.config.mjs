import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './site-tests',
  timeout: 30_000,
  workers: 1,
  reporter: 'list',
  use: {
    browserName: 'chromium',
    headless: true,
    viewport: { width: 1280, height: 800 },
  },
});
