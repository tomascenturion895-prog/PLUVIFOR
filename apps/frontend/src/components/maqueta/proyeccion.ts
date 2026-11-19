import type { Feature, FeatureCollection, MultiPolygon, Polygon } from 'geojson'

/** Un punto sobre el plano ya proyectado en isométrico. */
export interface Punto {
  x: number
  y: number
}

export interface Proyeccion {
  /** Proyecta longitud y latitud al plano isométrico del SVG (sin elevar). */
  proyectar: (lon: number, lat: number) => Punto
  ancho: number
  alto: number
}

const COS30 = Math.cos(Math.PI / 6)
const SIN30 = 0.5
const GRADO = 100 // unidades del plano por grado, antes de rotar

type Anillo = number[][]

function anillos(feature: Feature): Anillo[] {
  const g = feature.geometry as Polygon | MultiPolygon | null
  if (!g) return []
  if (g.type === 'Polygon') return g.coordinates
  if (g.type === 'MultiPolygon') return g.coordinates.flat()
  return []
}

/**
 * Arma la proyección isométrica de una capa: la provincia se rota 45° y se aplasta a la mitad
 * (la vista clásica de maqueta) y se recorta el espacio vacío. `margen` deja lugar para la altura
 * de los bloques y las estaciones.
 */
export function crearProyeccion(capa: FeatureCollection, margen = 24): Proyeccion {
  const puntos = capa.features.flatMap(anillos).flat()
  if (puntos.length === 0) return { proyectar: () => ({ x: 0, y: 0 }), ancho: 1, alto: 1 }
  const lonMin = Math.min(...puntos.map((p) => p[0]))
  const latMax = Math.max(...puntos.map((p) => p[1]))
  const bruto = (lon: number, lat: number): Punto => {
    const x0 = (lon - lonMin) * GRADO
    const y0 = (latMax - lat) * GRADO
    return { x: (x0 - y0) * COS30, y: (x0 + y0) * SIN30 }
  }
  const proy = puntos.map((p) => bruto(p[0], p[1]))
  const xMin = Math.min(...proy.map((p) => p.x))
  const yMin = Math.min(...proy.map((p) => p.y))
  const xMax = Math.max(...proy.map((p) => p.x))
  const yMax = Math.max(...proy.map((p) => p.y))
  return {
    proyectar: (lon, lat) => {
      const p = bruto(lon, lat)
      return { x: p.x - xMin + margen, y: p.y - yMin + margen }
    },
    ancho: xMax - xMin + margen * 2,
    alto: yMax - yMin + margen * 2,
  }
}

/** Camino SVG (`d`) de un departamento proyectado. */
export function caminoDe(feature: Feature, proyeccion: Proyeccion): string {
  return anillos(feature)
    .map((anillo) => {
      const trazo = anillo.map((p, i) => {
        const { x, y } = proyeccion.proyectar(p[0], p[1])
        return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`
      })
      return `${trazo.join(' ')}Z`
    })
    .join(' ')
}

/** Centro aproximado (caja envolvente) de un departamento, ya proyectado. */
export function centroDe(feature: Feature, proyeccion: Proyeccion): Punto {
  const ps = anillos(feature)
    .flat()
    .map((p) => proyeccion.proyectar(p[0], p[1]))
  if (ps.length === 0) return { x: 0, y: 0 }
  const xs = ps.map((p) => p.x)
  const ys = ps.map((p) => p.y)
  return { x: (Math.min(...xs) + Math.max(...xs)) / 2, y: (Math.min(...ys) + Math.max(...ys)) / 2 }
}
