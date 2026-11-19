import type {
  Feature,
  FeatureCollection,
  LineString,
  MultiLineString,
  MultiPolygon,
  Polygon,
} from 'geojson'
import type { Series, Station } from '../../api/types'
import { normalizar } from '../maqueta/maqueta-datos'

/**
 * Exposición pluvial por departamento (categoría: estimado).
 *
 * No es una predicción de inundación ni un mapa de riesgo oficial: cruza dos cosas reales y
 * descriptivas con reglas simples y publicadas en docs/decisiones/temas/vista-3d-exposicion.md.
 * - Lluvia: si en el período hubo días de 50 mm o más, o de 100 mm o más (umbrales del proyecto).
 * - Red hídrica: kilómetros de cursos de agua del IGN por cada 100 km² del departamento.
 * Los milímetros de estaciones distintas no se suman ni se promedian.
 */

export type Clase = 'baja' | 'media' | 'alta'

export const UMBRAL_EVENTO_MM = 50
export const UMBRAL_EVENTO_FUERTE_MM = 100

type Anillo = number[][]

function poligonos(feature: Feature): Anillo[][] {
  const g = feature.geometry as Polygon | MultiPolygon | null
  if (!g) return []
  if (g.type === 'Polygon') return [g.coordinates]
  if (g.type === 'MultiPolygon') return g.coordinates
  return []
}

function dentroDeAnillo(lon: number, lat: number, anillo: Anillo): boolean {
  let dentro = false
  for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
    const [xi, yi] = anillo[i]
    const [xj, yj] = anillo[j]
    if (yi > lat !== yj > lat && lon < ((xj - xi) * (lat - yi)) / (yj - yi) + xi) dentro = !dentro
  }
  return dentro
}

/** Punto dentro de un (multi)polígono, respetando los huecos interiores. */
export function puntoEnDepartamento(lon: number, lat: number, feature: Feature): boolean {
  return poligonos(feature).some(
    ([exterior, ...huecos]) =>
      exterior !== undefined &&
      dentroDeAnillo(lon, lat, exterior) &&
      !huecos.some((h) => dentroDeAnillo(lon, lat, h)),
  )
}

export function nombreDepartamento(feature: Feature): string {
  return String(feature.properties?.nombre ?? '')
}

export interface Ubicacion {
  departamento: string | null
  /** true si el catálogo no traía el departamento y se dedujo por las coordenadas verificadas. */
  deducido: boolean
}

/**
 * Departamento de una estación: el del catálogo; si falta, se deduce por la ubicación solo cuando
 * las coordenadas están verificadas. Coordenadas pendientes: queda sin departamento.
 */
export function ubicarEstacion(estacion: Station, deptos: FeatureCollection): Ubicacion {
  if (estacion.department) return { departamento: estacion.department, deducido: false }
  if (estacion.lat == null || estacion.lon == null || estacion.coords_status !== 'verificada') {
    return { departamento: null, deducido: false }
  }
  const f = deptos.features.find((d) => puntoEnDepartamento(estacion.lon!, estacion.lat!, d))
  return { departamento: f ? nombreDepartamento(f) : null, deducido: f !== undefined }
}

const RADIO_TIERRA_KM = 6371

function distanciaKm(a: number[], b: number[]): number {
  const rad = Math.PI / 180
  const dLat = (b[1] - a[1]) * rad
  const dLon = (b[0] - a[0]) * rad
  const s =
    Math.sin(dLat / 2) ** 2 + Math.cos(a[1] * rad) * Math.cos(b[1] * rad) * Math.sin(dLon / 2) ** 2
  return 2 * RADIO_TIERRA_KM * Math.asin(Math.min(1, Math.sqrt(s)))
}

/** Superficie aproximada en km² (proyección local; sirve para comparar, no para medir). */
export function areaKm2(feature: Feature): number {
  let total = 0
  for (const [exterior, ...huecos] of poligonos(feature)) {
    if (!exterior) continue
    const latMedia = exterior.reduce((s, p) => s + p[1], 0) / exterior.length
    const kx = ((Math.PI * RADIO_TIERRA_KM) / 180) * Math.cos((latMedia * Math.PI) / 180)
    const ky = (Math.PI * RADIO_TIERRA_KM) / 180
    const area = (anillo: Anillo) => {
      let s = 0
      for (let i = 0, j = anillo.length - 1; i < anillo.length; j = i++) {
        s += anillo[j][0] * kx * (anillo[i][1] * ky) - anillo[i][0] * kx * (anillo[j][1] * ky)
      }
      return Math.abs(s) / 2
    }
    total += area(exterior) - huecos.reduce((s, h) => s + area(h), 0)
  }
  return total
}

function lineas(capa: FeatureCollection | null): number[][][] {
  if (!capa) return []
  return capa.features.flatMap((f) => {
    const g = f.geometry as LineString | MultiLineString | null
    if (!g) return []
    if (g.type === 'LineString') return [g.coordinates]
    if (g.type === 'MultiLineString') return g.coordinates
    return []
  })
}

/** Kilómetros de cursos de agua dentro del departamento (por el punto medio de cada tramo). */
export function kmCursosEn(feature: Feature, ...capas: (FeatureCollection | null)[]): number {
  let km = 0
  for (const linea of capas.flatMap(lineas)) {
    for (let i = 1; i < linea.length; i++) {
      const a = linea[i - 1]
      const b = linea[i]
      if (puntoEnDepartamento((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, feature))
        km += distanciaKm(a, b)
    }
  }
  return km
}

export interface Hidrica {
  kmCursos: number
  areaKm2: number
  /** km de cursos de agua por cada 100 km². */
  densidad: number
  /** Tercio relativo entre los departamentos de la provincia. */
  clase: Clase
}

/** Densidad de cursos de agua y su tercio (baja, media, alta) entre los departamentos. */
export function redHidrica(
  deptos: FeatureCollection,
  ...capas: (FeatureCollection | null)[]
): Map<string, Hidrica> {
  const base = deptos.features.map((f) => {
    const km = kmCursosEn(f, ...capas)
    const area = areaKm2(f)
    return { nombre: nombreDepartamento(f), km, area, densidad: area > 0 ? (km / area) * 100 : 0 }
  })
  const orden = [...base].sort((a, b) => a.densidad - b.densidad)
  const n = orden.length
  return new Map(
    base.map((d) => {
      const pos = orden.indexOf(d)
      const clase: Clase = pos < n / 3 ? 'baja' : pos < (2 * n) / 3 ? 'media' : 'alta'
      return [
        normalizar(d.nombre),
        { kmCursos: d.km, areaKm2: d.area, densidad: d.densidad, clase },
      ]
    }),
  )
}

export type MotivoDescarte = 'racha_de_ceros' | 'sin_dato'

export interface LecturaEstacion {
  estacionId: number
  nombre: string
  /** Mayor lluvia diaria con dato; null si no hubo ningún día con dato (no es 0). */
  maximoDiarioMm: number | null
  diasSobre50: number
  diasSobre100: number
  diasConDato: number
  /** Si se descarta, no entra en la clase pluvial del departamento. */
  descarte: MotivoDescarte | null
}

/** Lee la serie diaria: los huecos se ignoran, nunca cuentan como 0 mm. */
export function leerSerie(serie: Series): LecturaEstacion {
  const conDato = serie.days.filter((d) => d.state === 'dato' && d.mm !== null)
  const mms = conDato.map((d) => d.mm as number)
  const rachaDeCeros = serie.warnings.some((w) => w.code === 'ceros_prolongados')
  return {
    estacionId: serie.station_id,
    nombre: serie.station_name,
    maximoDiarioMm: mms.length ? Math.max(...mms) : null,
    diasSobre50: mms.filter((mm) => mm >= UMBRAL_EVENTO_MM).length,
    diasSobre100: mms.filter((mm) => mm >= UMBRAL_EVENTO_FUERTE_MM).length,
    diasConDato: mms.length,
    descarte: rachaDeCeros ? 'racha_de_ceros' : mms.length === 0 ? 'sin_dato' : null,
  }
}

/** Clase pluvial de una estación según los umbrales del proyecto (≥ 50 y ≥ 100 mm en un día). */
export function clasePluvial(l: LecturaEstacion): Clase | null {
  if (l.descarte) return null
  if (l.diasSobre100 > 0) return 'alta'
  if (l.diasSobre50 > 0) return 'media'
  return 'baja'
}

const ORDEN: Clase[] = ['baja', 'media', 'alta']

/** La peor clase entre las estaciones usables del departamento (el máximo individual, no una suma). */
export function claseDepartamento(lecturas: LecturaEstacion[]): Clase | null {
  const clases = lecturas.map(clasePluvial).filter((c): c is Clase => c !== null)
  if (!clases.length) return null
  return ORDEN[Math.max(...clases.map((c) => ORDEN.indexOf(c)))]
}

/** Matriz lluvia × red hídrica. Sin clase pluvial no hay exposición: queda sin dato. */
const MATRIZ: Record<Clase, Record<Clase, Clase>> = {
  baja: { baja: 'baja', media: 'baja', alta: 'media' },
  media: { baja: 'baja', media: 'media', alta: 'alta' },
  alta: { baja: 'media', media: 'alta', alta: 'alta' },
}

export function exposicion(pluvial: Clase | null, hidrica: Clase | null): Clase | null {
  if (!pluvial || !hidrica) return null
  return MATRIZ[pluvial][hidrica]
}

export interface Departamento {
  nombre: string
  clave: string
  hidrica: Hidrica | null
  lecturas: LecturaEstacion[]
  estacionesSinSerie: number
  deducidas: string[]
  pluvial: Clase | null
  exposicion: Clase | null
}

export function armarDepartamentos(
  deptos: FeatureCollection,
  hidrica: Map<string, Hidrica>,
  estaciones: Station[],
  lecturas: Map<number, LecturaEstacion>,
): Departamento[] {
  return deptos.features.map((f) => {
    const nombre = nombreDepartamento(f)
    const clave = normalizar(nombre)
    const propias = estaciones
      .map((s) => ({ s, u: ubicarEstacion(s, deptos) }))
      .filter(({ u }) => u.departamento && normalizar(u.departamento) === clave)
    const leidas = propias
      .map(({ s }) => lecturas.get(s.id))
      .filter((l): l is LecturaEstacion => !!l)
    const pluvial = claseDepartamento(leidas)
    const h = hidrica.get(clave) ?? null
    return {
      nombre,
      clave,
      hidrica: h,
      lecturas: leidas,
      estacionesSinSerie: propias.length - leidas.length,
      deducidas: propias.filter(({ u }) => u.deducido).map(({ s }) => s.name),
      pluvial,
      exposicion: exposicion(pluvial, h?.clase ?? null),
    }
  })
}

export const TEXTO_CLASE: Record<Clase, string> = { baja: 'Baja', media: 'Media', alta: 'Alta' }

/** Colores accesibles (ColorBrewer YlOrRd, 3 clases) para la exposición. */
export const COLOR_CLASE: Record<Clase, string> = {
  baja: '#ffeda0',
  media: '#feb24c',
  alta: '#e5482a',
}

export const COLOR_SIN_DATO = '#9e9e9e'
