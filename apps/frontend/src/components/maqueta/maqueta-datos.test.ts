import { describe, expect, it } from 'vitest'
import type { AccumulatedStation, Station } from '../../api/types'
import {
  diferencias,
  estadoDePieza,
  normalizar,
  periodoAnterior,
  resumenPorDepartamento,
  ultimosDias,
} from './maqueta-datos'
import { caminoDe, crearProyeccion } from './proyeccion'

const est = (id: number, department: string | null): Station =>
  ({ id, department, name: `E${id}` }) as unknown as Station
const acum = (id: number, mm: number | null): AccumulatedStation => ({
  station_id: id,
  station_name: `E${id}`,
  accumulated_mm: mm,
  days_with_data: mm === null ? 0 : 5,
  days_without_data: 0,
  coverage: 1,
  warnings: [],
})

describe('resumenPorDepartamento', () => {
  it('toma el máximo individual y no suma estaciones', () => {
    const r = resumenPorDepartamento(
      [est(1, 'Pirané'), est(2, 'Pirané'), est(3, 'Bermejo')],
      new Map([
        [1, acum(1, 10)],
        [2, acum(2, 25)],
        [3, acum(3, null)],
      ]),
    )
    expect(r.get('pirane')).toEqual({ maximoMm: 25, estaciones: 2, conDato: 2 })
  })

  it('un departamento sin datos queda en null, no en 0', () => {
    const r = resumenPorDepartamento([est(3, 'Bermejo')], new Map([[3, acum(3, null)]]))
    expect(r.get('bermejo')).toEqual({ maximoMm: null, estaciones: 1, conDato: 0 })
  })

  it('un 0 mm real es dato, distinto de sin dato', () => {
    const r = resumenPorDepartamento([est(1, 'Laishi')], new Map([[1, acum(1, 0)]]))
    expect(r.get('laishi')?.maximoMm).toBe(0)
  })

  it('ignora estaciones sin departamento y normaliza acentos', () => {
    expect(resumenPorDepartamento([est(1, null)], new Map()).size).toBe(0)
    expect(normalizar(' Pirané ')).toBe('pirane')
  })
})

describe('estadoDePieza', () => {
  it('en silencio gana sobre el dato; sin dato nunca es con_dato', () => {
    expect(estadoDePieza(acum(1, 0), 'en_silencio')).toBe('en_silencio')
    expect(estadoDePieza(acum(1, null), 'activa')).toBe('sin_dato')
    expect(estadoDePieza(undefined, undefined)).toBe('sin_dato')
    expect(estadoDePieza(acum(1, 0), 'activa')).toBe('con_dato')
  })
})

describe('diferencias', () => {
  it('resta solo si los dos tienen dato', () => {
    const base = new Map([
      [1, acum(1, 10)],
      [2, acum(2, null)],
    ])
    const variante = new Map([
      [1, acum(1, 25)],
      [2, acum(2, 7)],
      [3, acum(3, 4)],
    ])
    const d = diferencias(base, variante, [1, 2, 3])
    expect(d.map((x) => x.delta)).toEqual([15, null, null])
  })
})

describe('períodos', () => {
  it('el anterior tiene el mismo largo y termina el día previo', () => {
    expect(periodoAnterior('2026-10-01', '2026-10-10')).toEqual({
      desde: '2026-09-21',
      hasta: '2026-09-30',
    })
  })
  it('últimos N días incluye el día final', () => {
    expect(ultimosDias('2026-10-31', 7)).toEqual({ desde: '2026-10-25', hasta: '2026-10-31' })
  })
})

describe('proyección isométrica', () => {
  const capa = {
    type: 'FeatureCollection',
    features: [
      {
        type: 'Feature',
        properties: { nombre: 'X' },
        geometry: {
          type: 'Polygon',
          coordinates: [
            [
              [-60, -25],
              [-59, -25],
              [-59, -26],
              [-60, -26],
              [-60, -25],
            ],
          ],
        },
      },
    ],
  } as const

  it('todo cae dentro del lienzo y el camino cierra', () => {
    const p = crearProyeccion(capa as never, 10)
    const pts = [p.proyectar(-60, -25), p.proyectar(-59, -26)]
    for (const q of pts) {
      expect(q.x).toBeGreaterThanOrEqual(0)
      expect(q.x).toBeLessThanOrEqual(p.ancho)
      expect(q.y).toBeGreaterThanOrEqual(0)
      expect(q.y).toBeLessThanOrEqual(p.alto)
    }
    expect(caminoDe(capa.features[0] as never, p)).toMatch(/^M.*Z$/)
  })

  it('una capa vacía no rompe', () => {
    expect(crearProyeccion({ type: 'FeatureCollection', features: [] } as never).ancho).toBe(1)
  })
})
