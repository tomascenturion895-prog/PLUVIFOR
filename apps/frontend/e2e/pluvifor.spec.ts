import { expect, test, type Page } from '@playwright/test'

const LEYENDA = 'PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial'
const RUTAS = ['/', '/mapa', '/estacion', '/comparador', '/parte', '/importar', '/salud', '/ayuda']

async function sinDesborde(page: Page) {
  const { ancho, visible } = await page.evaluate(() => ({
    ancho: document.documentElement.scrollWidth,
    visible: window.innerWidth,
  }))
  expect(ancho, 'la página no debe tener scroll horizontal').toBeLessThanOrEqual(visible)
}

test.describe('Reglas visibles en toda la interfaz', () => {
  for (const ruta of RUTAS) {
    test(`la leyenda de prototipo está en ${ruta}`, async ({ page }) => {
      await page.goto(ruta)
      await expect(page.getByText(LEYENDA).first()).toBeVisible()
    })
  }

  test('una ruta que no existe muestra la página de error en español', async ({ page }) => {
    await page.goto('/no-existe')
    await expect(page.getByRole('heading', { name: 'Página no encontrada' })).toBeVisible()
  })
})

test.describe('Inicio y navegación', () => {
  test('el inicio responde la pregunta central y dice que un hueco no es 0 mm', async ({
    page,
  }) => {
    await page.goto('/')
    await expect(
      page.getByRole('heading', { name: '¿Cuánto llovió, dónde y en qué período?' }),
    ).toBeVisible()
    await expect(page.getByText('nunca como 0 mm').first()).toBeVisible()
  })

  test('se puede llegar a la ficha de estación desde el menú', async ({ page }) => {
    await page.goto('/')
    await page.getByRole('link', { name: 'Estación' }).first().click()
    await expect(page).toHaveURL(/\/estacion/)
    await expect(page.getByLabel('Elegí una estación')).toBeVisible()
  })
})

test.describe('Ficha de estación: el hueco no es 0 mm', () => {
  test('un período sin filas se muestra como «sin dato» y no como 0 mm', async ({ page }) => {
    await page.goto('/estacion/2')
    await expect(page.getByText('Acumulado del período')).toBeVisible()
    // La estación 424 no tiene filas en los últimos 90 días hasta el corte.
    await expect(page.getByText('sin dato').first()).toBeVisible()
    await expect(page.getByText('0 de 90')).toBeVisible()
    await expect(page.getByText(/Solo 0% de los días tiene dato/).first()).toBeVisible()
  })

  test('la racha de 281 ceros de la 424 se advierte y no se da por buena', async ({ page }) => {
    await page.goto('/estacion/2')
    await page.getByLabel('Desde').fill('2015-09-20')
    await page.getByLabel('Hasta').fill('2016-06-26')
    await expect(page.getByText(/racha/i).first()).toBeVisible()
    await expect(page.getByText('Observado').first()).toBeVisible()
  })

  test('la estación 425 en el mismo período muestra su acumulado con dato', async ({ page }) => {
    await page.goto('/estacion/3')
    await page.getByLabel('Desde').fill('2015-09-20')
    await page.getByLabel('Hasta').fill('2016-06-26')
    await expect(page.getByText(/1\.?265/).first()).toBeVisible()
  })
})

test.describe('Parte pluvial', () => {
  test('se genera un parte con fuente, categoría y fecha de corte', async ({ page }) => {
    await page.goto('/parte')
    await page.getByLabel(/El Colorado - EEA El Colorado \(424\)/).check()
    await page.getByLabel('Desde').fill('2016-01-01')
    await page.getByLabel('Hasta').fill('2016-01-31')
    await page.getByRole('button', { name: 'Generar parte' }).click()
    await expect(page.getByText(/2026-10-31|31\/10\/2026/).first()).toBeVisible()
    await expect(page.getByText(/SIGA/).first()).toBeVisible()
  })
})

test.describe('Importar: la escritura exige clave', () => {
  test('sin clave no se puede auditar ni confirmar', async ({ page }) => {
    await page.goto('/importar')
    await expect(
      page.getByText('Ingresá la clave de administración para auditar y confirmar cargas.'),
    ).toBeVisible()
    await expect(page.getByRole('button', { name: 'Auditar' })).toBeDisabled()
    await expect(page.getByRole('button', { name: 'Confirmar carga' })).toBeDisabled()
  })
})

test.describe('Mapa provincial', () => {
  test('dibuja el mapa y explica que el color no es un total departamental', async ({ page }) => {
    await page.goto('/mapa')
    await expect(page.locator('.leaflet-container')).toBeVisible()
    await expect(page.getByText(/no es un total departamental/)).toBeVisible()
    await expect(page.getByText(/hueco ≠ 0 mm/)).toBeVisible()
  })
})

test.describe('Se ve bien en este tamaño de pantalla', () => {
  for (const ruta of RUTAS) {
    test(`sin scroll horizontal en ${ruta}`, async ({ page }) => {
      await page.goto(ruta)
      await page.waitForLoadState('networkidle')
      await sinDesborde(page)
    })
  }

  test('en celular los botones y campos miden al menos 44 px', async ({ page }, info) => {
    test.skip(info.project.name !== 'celular', 'solo aplica a celular')
    for (const ruta of ['/estacion', '/parte', '/importar']) {
      await page.goto(ruta)
      await page.waitForLoadState('networkidle')
      const chicos = await page.evaluate(() =>
        [
          ...document.querySelectorAll(
            'button, select, input:not([type=checkbox]):not([type=radio])',
          ),
        ]
          .filter((e) => {
            const b = e.getBoundingClientRect()
            return b.width > 0 && b.height > 0 && b.height < 44
          })
          .map((e) => e.tagName.toLowerCase() + ':' + (e.textContent || '').trim().slice(0, 20)),
      )
      expect(chicos, `controles menores a 44 px en ${ruta}`).toEqual([])
    }
  })
})
