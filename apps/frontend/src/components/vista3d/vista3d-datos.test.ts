import { describe, expect, it } from 'vitest'
import type { FeatureCollection } from 'geojson'
import type { Series, Station } from '../../api/types'
import {
  areaKm2,
  armarDepartamentos,
  clasePluvial,
  exposicion,
  kmCursosEn,
  leerSerie,
  puntoEnDepartamento,
  redHidrica,
  ubicarEstacion,
} from './exposicion-datos'

const cuadro = (nombre: string, x0: number, x1: number) => ({
  type: 'Feature' as const,
  properties: { nombre },
  geometry: {
    type: 'Polygon' as const,
    coordinates: [
      [
        [x0, -26],
        [x1, -26],
        [x1, -25],
        [x0, -25],
        [x0, -26],
      ],
    ],
  },
})

const deptos: FeatureCollection = {
  type: 'FeatureCollection',
  features: [cuadro('Oeste', -61, -60), cuadro('Centro', -60, -59), cuadro('Este', -59, -58)],
}

const rios: FeatureCollection = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [
          [-58.9, -25.5],
          [-58.1, -25.5],
        ],
      },
    },
    {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [
          [-59.9, -25.5],
          [-59.5, -25.5],
        ],
      },
    },
  ],
}

function estacion(p: Partial<Station>): Station {
  return {
    id: 1,
    code: 'x',
    internal_code: null,
    name: 'Estación',
    kind: null,
    locality: null,
    department: null,
    zone: null,
    lat: null,
    lon: null,
    elevation_m: null,
    coords_status: 'pendiente',
    active_from: null,
    active_to: null,
    source: { code: 's', name: 'S', network: 'n', category: 'observado', day_cutoff_local: null },
    ...p,
  }
}

function serie(mms: (number | null)[], codigos: string[] = []): Series {
  return {
    station_id: 7,
    station_name: 'Prueba',
    days: mms.map((mm, i) => ({
      obs_date: `2016-01-${String(i + 1).padStart(2, '0')}`,
      state: mm === null ? 'sin_fila' : 'dato',
      mm,
      category: 'observado',
      source: 's',
      flags: [],
    })),
    warnings: codigos.map((code) => ({ code, message: '', severity: 'aviso' })),
  } as unknown as Series
}

describe('exposición por departamento', () => {
  it('ubica un punto y respeta los límites', () => {
    expect(puntoEnDepartamento(-59.5, -25.5, deptos.features[1])).toBe(true)
    expect(puntoEnDepartamento(-58.5, -25.5, deptos.features[1])).toBe(false)
  })

  it('deduce el departamento solo con coordenadas verificadas', () => {
    const ok = estacion({ lat: -25.5, lon: -59.5, coords_status: 'verificada' })
    expect(ubicarEstacion(ok, deptos)).toEqual({ departamento: 'Centro', deducido: true })
    const pendiente = estacion({ lat: -25.5, lon: -59.5, coords_status: 'pendiente' })
    expect(ubicarEstacion(pendiente, deptos).departamento).toBeNull()
    expect(ubicarEstacion(estacion({ department: 'Este' }), deptos)).toEqual({
      departamento: 'Este',
      deducido: false,
    })
  })

  it('mide superficie y cursos de agua de forma aproximada', () => {
    const area = areaKm2(deptos.features[0])
    expect(area).toBeGreaterThan(10_000)
    expect(area).toBeLessThan(12_000)
    expect(kmCursosEn(deptos.features[2], rios)).toBeGreaterThan(70)
    expect(kmCursosEn(deptos.features[0], rios)).toBe(0)
  })

  it('reparte la red hídrica en tercios relativos', () => {
    const h = redHidrica(deptos, rios)
    expect(h.get('este')?.clase).toBe('alta')
    expect(h.get('oeste')?.clase).toBe('baja')
  })

  it('un hueco no cuenta como 0 mm y una racha de ceros se descarta', () => {
    const conHuecos = leerSerie(serie([null, 12, null, 55]))
    expect(conHuecos.diasConDato).toBe(2)
    expect(clasePluvial(conHuecos)).toBe('media')
    const soloHuecos = leerSerie(serie([null, null]))
    expect(soloHuecos.maximoDiarioMm).toBeNull()
    expect(clasePluvial(soloHuecos)).toBeNull()
    const ceros = leerSerie(serie([0, 0, 0], ['ceros_prolongados']))
    expect(ceros.descarte).toBe('racha_de_ceros')
    expect(clasePluvial(ceros)).toBeNull()
    expect(clasePluvial(leerSerie(serie([101])))).toBe('alta')
  })

  it('sin clase pluvial no hay exposición', () => {
    expect(exposicion(null, 'alta')).toBeNull()
    expect(exposicion('alta', 'media')).toBe('alta')
    expect(exposicion('baja', 'baja')).toBe('baja')
  })

  it('arma los departamentos con la estación deducida', () => {
    const e = estacion({
      id: 7,
      name: 'Prueba',
      lat: -25.5,
      lon: -58.5,
      coords_status: 'verificada',
    })
    const d = armarDepartamentos(
      deptos,
      redHidrica(deptos, rios),
      [e],
      new Map([[7, leerSerie(serie([120]))]]),
    )
    const este = d.find((x) => x.nombre === 'Este')!
    expect(este.pluvial).toBe('alta')
    expect(este.exposicion).toBe('alta')
    expect(este.deducidas).toEqual(['Prueba'])
    expect(d.find((x) => x.nombre === 'Oeste')!.exposicion).toBeNull()
  })
})
