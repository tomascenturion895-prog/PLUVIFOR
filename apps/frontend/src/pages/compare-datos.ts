import type { SeriesCompareStation } from '../api/types'

export interface FilaComparada {
  fecha: string
  /** Una clave `s<id>` por estación. null = sin dato: la línea se corta, nunca baja a 0. */
  [clave: string]: string | number | null
}

export const claveDe = (id: number) => `s${id}`

/** Alinea por fecha las series de las estaciones elegidas, con una escala común. */
export function alinearSeries(estaciones: SeriesCompareStation[]): FilaComparada[] {
  const porFecha = new Map<string, FilaComparada>()
  for (const est of estaciones) {
    for (const d of est.days) {
      const fila = porFecha.get(d.obs_date) ?? { fecha: d.obs_date }
      fila[claveDe(est.station_id)] = d.state === 'dato' ? d.mm : null
      porFecha.set(d.obs_date, fila)
    }
  }
  const filas = [...porFecha.values()].sort((a, b) =>
    String(a.fecha).localeCompare(String(b.fecha)),
  )
  // Una estación sin fila en una fecha también es «sin dato» (null), no ausente.
  for (const fila of filas) {
    for (const est of estaciones) fila[claveDe(est.station_id)] ??= null
  }
  return filas
}

/** Diferencia de cobertura entre la mejor y la peor estación, en puntos porcentuales. */
export function diferenciaCobertura(estaciones: SeriesCompareStation[]): number {
  if (estaciones.length < 2) return 0
  const c = estaciones.map((e) => e.summary.coverage * 100)
  return Math.round(Math.max(...c) - Math.min(...c))
}
