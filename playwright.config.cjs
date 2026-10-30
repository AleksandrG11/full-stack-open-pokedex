const { defineConfig } = require('@playwright/test')

module.exports = defineConfig({
  testDir: './e2e-tests',
  timeout: 30000,
  expect: { timeout: 10000 },
  use: { baseURL: 'http://127.0.0.1:5137', headless: true },
  webServer: {
    command: 'PORT=5137 npm run start-prod',
    url: 'http://127.0.0.1:5137',
    reuseExistingServer: false,
    timeout: 30000
  }
})
