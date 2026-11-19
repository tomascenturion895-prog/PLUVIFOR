import type { AccumulatedStation, NetworkState, Station } from '../../api/types'
import { textoMmMapa } from '../../pages/map-helpers'

export function normalizar(nombre: string): string {
  return nombre.normalize('NFD').replace(/[̀-ͯ]/g, '').trim().toLowerCase()
}

export interface ResumenDepto {
  /** Mayor acumulado individual entre sus estaciones con dato; null si ninguna tiene dato. */
  maximoMm: number | null
  estaciones: number
  conDato: number
}

/**
 * Por departamento: el máximo individual de sus estaciones con dato. No es un total ni un
 * promedio departamental (los acumulados de estaciones distintas no se suman).
 */
export function resumenPorDepartamento(
  estaciones: Station[],
  acumulados: Map<number, AccumulatedStation>,
): Map<string, ResumenDepto> {
  const resumen = new Map<string, ResumenDepto>()
  for (const s of estaciones) {
    if (!s.department) continue
    const clave = normalizar(s.department)
    const actual = resumen.get(clave) ?? { maximoMm: null, estaciones: 0, conDato: 0 }
    const mm = acumulados.get(s.id)?.accumulated_mm ?? null
    actual.estaciones += 1
    if (mm !== null) {
      actual.conDato += 1
      if (actual.maximoMm === null || mm > actual.maximoMm) actual.maximoMm = mm
    }
    resumen.set(clave, actual)
  }
  return resumen
}

export type EstadoPieza = 'con_dato' | 'sin_dato' | 'en_silencio'

/** Cómo se dibuja una estación: en silencio o sin dato nunca toma el color de 0 mm. */
export function estadoDePieza(
  acumulado: AccumulatedStation | undefined,
  salud: NetworkState | undefined,
): EstadoPieza {
  if (salud === 'en_silencio') return 'en_silencio'
  if (acumulado?.accumulated_mm == null) return 'sin_dato'
  return 'con_dato'
}

export interface Diferencia {
  stationId: number
  base: number | null
  variante: number | null
  /** variante − base; null si alguno de los dos no tiene dato (no se puede restar). */
  delta: number | null
}

/** Resta dos valores que ya calculó la API. Un hueco no es 0: sin los dos datos, no hay resta. */
export function diferencias(
  base: Map<number, AccumulatedStation>,
  variante: Map<number, AccumulatedStation>,
  ids: number[],
): Diferencia[] {
  return ids.map((id) => {
    const b = base.get(id)?.accumulated_mm ?? null
    const v = variante.get(id)?.accumulated_mm ?? null
    return { stationId: id, base: b, variante: v, delta: b !== null && v !== null ? v - b : null }
  })
}

function sumarDias(fecha: string, dias: number): string {
  const d = new Date(`${fecha}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() + dias)
  return d.toISOString().slice(0, 10)
}

export function diasEntre(desde: string, hasta: string): number {
  return Math.round((Date.parse(hasta) - Date.parse(desde)) / 86_400_000) + 1
}

/** Período inmediatamente anterior y de igual largo. */
export function periodoAnterior(desde: string, hasta: string): { desde: string; hasta: string } {
  const n = diasEntre(desde, hasta)
  return { desde: sumarDias(desde, -n), hasta: sumarDias(desde, -1) }
}

/** Los últimos `dias` días hasta `hasta`. */
export function ultimosDias(hasta: string, dias: number): { desde: string; hasta: string } {
  return { desde: sumarDias(hasta, -(dias - 1)), hasta }
}

export function textoDepartamento(nombre: string, r: ResumenDepto | undefined): string {
  if (!r || r.estaciones === 0) return `${nombre}: sin estaciones en el catálogo.`
  if (r.maximoMm === null) {
    return `${nombre}: ${r.estaciones} estaciones, ninguna con dato en el período (sin dato).`
  }
  return `${nombre}: mayor acumulado individual ${textoMmMapa(r.maximoMm)}, ${r.conDato} de ${r.estaciones} estaciones con dato.`
}
