import type { NetworkState } from '../api/types'

export const TEXTO_ESTADO: Record<NetworkState, string> = {
  activa: 'Activa',
  en_silencio: 'En silencio',
  sin_datos: 'Sin datos',
}

/** 2026-10-31 → 31/10/2026 (sin pasar por Date: no hay corrimiento de zona horaria). */
export function fechaLegible(iso: string): string {
  const [anio, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${anio}`
}

export function formatoMm(mm: number): string {
  return `${mm.toLocaleString('es-AR', { maximumFractionDigits: 2 })} mm`
}
