import { defineConfig } from '@playwright/test'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

// Pruebas de extremo a extremo (SCRUM-73): navegador real contra la API y la interfaz
// levantadas con la base de demo (3 estaciones del SIGA/INTA, sin internet).
// Puertos distintos de los de desarrollo para no pisar lo que ya corre.
const API = 'http://127.0.0.1:8100'
const WEB = 'http://127.0.0.1:5273'
const DB = join(tmpdir(), 'pluvifor-e2e.db')
const python = process.env.E2E_PYTHON ?? 'python'
const executablePath = process.env.E2E_CHROME_PATH // opcional: un Chrome ya instalado
const args = process.env.E2E_NO_SANDBOX ? ['--no-sandbox'] : []

export default defineConfig({
  testDir: './e2e',
  timeout: 30_000,
  retries: process.env.CI ? 1 : 0,
  reporter: [['list']],
  use: { baseURL: WEB, locale: 'es-AR', launchOptions: { executablePath, args } },
  projects: [
    { name: 'escritorio', use: { viewport: { width: 1280, height: 800 } } },
    { name: 'tableta', use: { viewport: { width: 768, height: 1024 }, hasTouch: true } },
    { name: 'celular', use: { viewport: { width: 360, height: 740 }, hasTouch: true } },
  ],
  webServer: [
    {
      command: `${python} -m app.cli reset-demo --yes && ${python} -m uvicorn app.main:app --port 8100`,
      cwd: '../backend',
      url: `${API}/api/stations`,
      env: { DATABASE_URL: `sqlite:///${DB}`, CORS_ORIGINS: WEB },
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: 'npx vite --host 127.0.0.1 --port 5273 --strictPort',
      url: WEB,
      env: { VITE_API_URL: API },
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
})
