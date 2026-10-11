import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  fullyParallel: false,
  retries: 0,
  reporter: 'list',
  use: {
    baseURL: 'http://127.0.0.1:4599',
    trace: 'off'
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    }
  ],
  webServer: {
    command: 'pnpm exec vite preview --host 127.0.0.1 --port 4599 --strictPort',
    port: 4599,
    reuseExistingServer: false,
    timeout: 60_000
  }
});
