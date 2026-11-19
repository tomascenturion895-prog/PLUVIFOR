/**
 * Guardia de la demo sin conexión (SCRUM-92): el código de la interfaz no puede pedir nada
 * a Internet por su cuenta. Si alguien agrega un CDN, una fuente o un mapa externo, esta
 * prueba falla y obliga a decidirlo a propósito.
 */
import { describe, expect, it } from 'vitest'
import indexHtml from '../../index.html?raw'

const fuentes = import.meta.glob('/src/**/*.{ts,tsx,css}', {
  query: '?raw',
  import: 'default',
  eager: true,
}) as Record<string, string>

// Direcciones que no son pedidos de red o que se usan solo si se activa OpenStreetMap a propósito.
const PERMITIDAS = [
  /^https?:\/\/(localhost|127\.0\.0\.1)/,
  /^http:\/\/www\.w3\.org\//, // espacios de nombres XML/SVG, no son pedidos
  /^https:\/\/\{s\}\.tile\.openstreetmap\.org\//, // solo con VITE_MAPA_BASE=osm
  /^https:\/\/www\.openstreetmap\.org\/copyright/, // enlace de atribución (licencia ODbL)
]

function direccionesExternas(texto: string): string[] {
  return (texto.match(/https?:\/\/[^\s'"`)<>]+/g) ?? []).filter(
    (url) => !PERMITIDAS.some((ok) => ok.test(url)),
  )
}

describe('demo sin internet', () => {
  it('ningún archivo de src ni index.html trae direcciones externas', () => {
    const halladas = Object.entries({ ...fuentes, '/index.html': indexHtml })
      .filter(([ruta]) => !/\.test\.tsx?$/.test(ruta))
      .flatMap(([ruta, texto]) => direccionesExternas(texto).map((url) => `${ruta}: ${url}`))
    expect(halladas).toEqual([])
  })

  it('detecta un CDN o una fuente externa si alguien los agrega', () => {
    expect(direccionesExternas('<link href="https://fonts.googleapis.com/css2?family=X">')).toEqual(
      ['https://fonts.googleapis.com/css2?family=X'],
    )
    expect(direccionesExternas('@import url(https://cdn.example.com/a.css)')).toHaveLength(1)
    expect(direccionesExternas('http://localhost:8000 xmlns="http://www.w3.org/2000/svg"')).toEqual(
      [],
    )
  })

  it('el código de src se leyó de verdad', () => {
    expect(Object.keys(fuentes).length).toBeGreaterThan(10)
  })
})
