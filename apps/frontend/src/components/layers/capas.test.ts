import { describe, expect, it } from 'vitest'
import { alternar, CAPAS, categoriasActivas, totalesPorCapa, type CapaId } from './capas'

describe('capas del mapa', () => {
  it('son solo de lluvia y de la red: nada de ríos, caudales ni riesgo', () => {
    const texto = JSON.stringify(CAPAS).toLowerCase()
    for (const prohibida of [/caudal/, /riesgo/, /\brío/, /\bríos\b/, /altura/]) {
      expect(texto).not.toMatch(prohibida)
    }
    expect(CAPAS.map((c) => c.id)).toEqual([
      'observado',
      'referencia',
      'estimado',
      'reportes',
      'silencio',
    ])
  })

  it('cada capa dice su fuente; las de lluvia llevan su categoría', () => {
    for (const capa of CAPAS) expect(capa.fuente.length).toBeGreaterThan(0)
    expect(CAPAS.filter((c) => c.categoria).map((c) => c.categoria)).toEqual([
      'observado',
      'referencia',
      'estimado',
    ])
  })

  it('prende y apaga una capa', () => {
    const una = alternar(['observado'], 'referencia')
    expect(una).toEqual(['observado', 'referencia'])
    expect(alternar(una, 'observado')).toEqual(['referencia'])
  })

  it('una capa sin fuente cargada no se puede prender y se explica por qué', () => {
    expect(alternar(['observado'], 'reportes')).toEqual(['observado'])
    expect(CAPAS.find((c) => c.id === 'reportes')?.noDisponible).toMatch(/Pendiente/)
  })

  it('las categorías activas van en orden fijo, sin repetirse ni mezclarse', () => {
    const activas: CapaId[] = ['estimado', 'silencio', 'observado']
    expect(categoriasActivas(activas)).toEqual(['observado', 'estimado'])
  })

  it('cuenta cada capa por separado y un hueco no cuenta como dato', () => {
    const acumulados = new Map([
      [
        'observado' as const,
        [{ accumulated_mm: 10 }, { accumulated_mm: 0 }, { accumulated_mm: null }],
      ],
      ['estimado' as const, [{ accumulated_mm: 99 }]],
    ])
    expect(totalesPorCapa(acumulados, ['observado', 'estimado'])).toEqual([
      { categoria: 'observado', conDato: 2, sinDato: 1 },
      { categoria: 'estimado', conDato: 1, sinDato: 0 },
    ])
  })

  it('al apagar una capa desaparece de los totales', () => {
    const acumulados = new Map([
      ['observado' as const, [{ accumulated_mm: 10 }]],
      ['estimado' as const, [{ accumulated_mm: 99 }]],
    ])
    expect(totalesPorCapa(acumulados, ['observado'])).toEqual([
      { categoria: 'observado', conDato: 1, sinDato: 0 },
    ])
    expect(totalesPorCapa(acumulados, [])).toEqual([])
  })

  it('una capa encendida cuyos datos todavía no llegaron no inventa un total', () => {
    expect(totalesPorCapa(new Map(), ['observado'])).toEqual([])
  })
})
