import { afterEach, describe, expect, it } from 'vitest'
import { colorMm } from '../../pages/map-helpers'
import { COLOR_CLASE } from '../vista3d/exposicion-datos'
import { COLOR_HIDRICA } from '../vista3d/provincia-aspecto'
import { DALTONICO, esDaltonico, temaActual } from './tema-colores'

afterEach(() => delete document.documentElement.dataset.tema)

describe('colores de datos por tema', () => {
  it('sin tema o con oscuro y claro, rigen los colores de siempre', () => {
    for (const t of [undefined, 'oscuro', 'claro']) {
      if (t) document.documentElement.dataset.tema = t
      expect(esDaltonico()).toBe(false)
      expect(colorMm(0)).toBe('#ffffd9')
      expect(colorMm(150)).toBe('#0c2c84')
      expect(COLOR_CLASE.alta).toBe('#e5482a')
      expect(COLOR_HIDRICA.baja).toBe('#c6dbef')
    }
  })

  it('en daltónico cambia la escala de lluvia, la exposición y la hídrica', () => {
    document.documentElement.dataset.tema = 'daltonico'
    expect(temaActual()).toBe('daltonico')
    expect(colorMm(0)).toBe(DALTONICO.mm[0])
    expect(colorMm(5)).toBe(DALTONICO.mm[1])
    expect(colorMm(20)).toBe(DALTONICO.mm[2])
    expect(colorMm(45)).toBe(DALTONICO.mm[3])
    expect(colorMm(80)).toBe(DALTONICO.mm[4])
    expect(colorMm(150)).toBe(DALTONICO.mm[5])
    expect(COLOR_CLASE.alta).toBe(DALTONICO.clase.alta)
    expect(COLOR_HIDRICA.media).toBe(DALTONICO.hidrica.media)
  })

  it('un hueco nunca toma el color de 0 mm, en ningún tema', () => {
    for (const t of ['oscuro', 'claro', 'daltonico']) {
      document.documentElement.dataset.tema = t
      expect(colorMm(null)).toBe('#9e9e9e')
      expect(colorMm(null)).not.toBe(colorMm(0))
    }
  })

  it('un tema desconocido cuenta como oscuro', () => {
    document.documentElement.dataset.tema = 'rosa'
    expect(temaActual()).toBe('oscuro')
  })
})
