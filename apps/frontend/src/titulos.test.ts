import { describe, expect, it } from 'vitest'
import { tituloDe } from './titulos'

describe('título de la pestaña', () => {
  it('nombra la pantalla', () => {
    expect(tituloDe('/')).toBe('Inicio · PLUVIFOR')
    expect(tituloDe('/mapa')).toBe('Mapa · PLUVIFOR')
    expect(tituloDe('/estacion/424')).toBe('Estación · PLUVIFOR')
  })

  it('una ruta que no existe no toma el nombre de otra', () => {
    expect(tituloDe('/no-existe')).toBe('Página no encontrada · PLUVIFOR')
    expect(tituloDe('/mapas')).toBe('Página no encontrada · PLUVIFOR')
  })
})
