import { describe, expect, it } from 'vitest'

import departamentos from '../../public/geo/formosa_departamentos.geojson?raw'
import intermitentes from '../../public/geo/formosa_cursos_agua_intermitentes.geojson?raw'
import perennes from '../../public/geo/formosa_cursos_agua_perennes.geojson?raw'
import provincia from '../../public/geo/formosa_provincia.geojson?raw'

interface Coleccion {
  type: string
  features: {
    properties: Record<string, unknown>
    geometry: { type: string; coordinates: unknown }
  }[]
}

// Cuadro que contiene a Formosa (lon -62.4..-57.4, lat -27.2..-22.4).
const LON = [-62.4, -57.4]
const LAT = [-27.2, -22.4]

function puntos(coordenadas: unknown): number[][] {
  if (Array.isArray(coordenadas) && typeof coordenadas[0] === 'number')
    return [coordenadas as number[]]
  return (coordenadas as unknown[]).flatMap(puntos)
}

function leer(texto: string): Coleccion {
  return JSON.parse(texto) as Coleccion
}

describe('capas geográficas del IGN', () => {
  it('provincia: una entidad Formosa con fuente IGN', () => {
    const c = leer(provincia)
    expect(c.type).toBe('FeatureCollection')
    expect(c.features).toHaveLength(1)
    expect(c.features[0].properties.nombre).toBe('Formosa')
    expect(c.features[0].properties.fuente).toBe('IGN')
  })

  it('departamentos: los 9 de la provincia, sin repetir', () => {
    const c = leer(departamentos)
    const nombres = c.features.map((f) => f.properties.nombre as string).sort()
    expect(nombres).toEqual(
      [
        'Bermejo',
        'Formosa',
        'Laishi',
        'Matacos',
        'Patiño',
        'Pilagás',
        'Pilcomayo',
        'Pirané',
        'Ramón Lista',
      ].sort(),
    )
    expect(new Set(c.features.map((f) => f.properties.id)).size).toBe(9)
  })

  // Los cursos de agua no se recortan en el límite: siguen hacia las provincias o países vecinos.
  it.each([
    ['provincia', provincia, 0],
    ['departamentos', departamentos, 0],
    ['cursos perennes', perennes, 0.5],
    ['cursos intermitentes', intermitentes, 0.5],
  ])(
    '%s: las coordenadas caen dentro de Formosa (con margen según la capa)',
    (_nombre, texto, margen) => {
      const c = leer(texto)
      expect(c.features.length).toBeGreaterThan(0)
      for (const f of c.features) {
        for (const [lon, lat] of puntos(f.geometry.coordinates)) {
          expect(lon).toBeGreaterThanOrEqual(LON[0] - margen)
          expect(lon).toBeLessThanOrEqual(LON[1] + margen)
          expect(lat).toBeGreaterThanOrEqual(LAT[0] - margen)
          expect(lat).toBeLessThanOrEqual(LAT[1] + margen)
        }
      }
    },
  )

  it('pesan poco para cargar rápido (menos de 400 KB cada una)', () => {
    for (const texto of [provincia, departamentos, perennes, intermitentes]) {
      expect(texto.length).toBeLessThan(400_000)
    }
  })

  it('entrada inválida: un archivo corrupto no se interpreta como capa', () => {
    expect(() => leer('{"type": "FeatureCollection", "features": [')).toThrow()
  })
})
