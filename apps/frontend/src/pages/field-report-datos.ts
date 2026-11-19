import type { FieldReportIn, LocationSource } from '../api/types'
import { FECHA_CORTE } from '../constants'

export interface FormularioReporte {
  fecha: string
  mm: string
  lugar: string
  quien: string
  lat: string
  lon: string
  origen: LocationSource | null
}

export const MAX_MM_REPORTE = 1000

export type Resultado =
  { ok: true; pedido: FieldReportIn; sinUbicacion: boolean } | { ok: false; errores: string[] }

/** «12,5» y «12.5» son lo mismo para quien escribe en un celular argentino. */
export function aNumero(texto: string): number | null {
  const limpio = texto.trim().replace(',', '.')
  if (limpio === '' || !/^-?\d+(\.\d+)?$/.test(limpio)) return null
  return Number(limpio)
}

/** Valida igual que la API (que decide de todos modos) para avisar antes de enviar. */
export function armarPedido(f: FormularioReporte): Resultado {
  const errores: string[] = []
  if (f.fecha === '') errores.push('Indicá la fecha de la lluvia.')
  else if (f.fecha > FECHA_CORTE) {
    errores.push('La fecha no puede ser posterior al corte de datos (31/10/2026).')
  }
  const mm = aNumero(f.mm)
  if (mm === null) errores.push('Indicá los milímetros como número (por ejemplo 12,5).')
  else if (mm < 0) errores.push('Los milímetros no pueden ser negativos.')
  else if (mm > MAX_MM_REPORTE) errores.push(`Los milímetros no pueden pasar de ${MAX_MM_REPORTE}.`)
  if (f.lugar.trim() === '') errores.push('Indicá el lugar.')
  if (f.quien.trim() === '') errores.push('Indicá quién reporta.')

  const hayLat = f.lat.trim() !== ''
  const hayLon = f.lon.trim() !== ''
  let lat: number | undefined
  let lon: number | undefined
  if (hayLat !== hayLon) errores.push('La ubicación necesita latitud y longitud juntas.')
  else if (hayLat) {
    const la = aNumero(f.lat)
    const lo = aNumero(f.lon)
    if (la === null || la < -90 || la > 90) errores.push('La latitud debe estar entre -90 y 90.')
    else lat = la
    if (lo === null || lo < -180 || lo > 180)
      errores.push('La longitud debe estar entre -180 y 180.')
    else lon = lo
  }
  if (errores.length > 0 || mm === null) return { ok: false, errores }
  const pedido: FieldReportIn = {
    obs_date: f.fecha,
    mm,
    place: f.lugar.trim(),
    reporter: f.quien.trim(),
  }
  if (lat !== undefined && lon !== undefined) {
    pedido.lat = lat
    pedido.lon = lon
    pedido.location_source = f.origen ?? 'manual'
  }
  return { ok: true, pedido, sinUbicacion: lat === undefined }
}

/** 2026-10-31 → 31/10/2026 (sin pasar por Date: no hay corrimiento de zona horaria). */
export function fechaLegible(iso: string): string {
  const [anio, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${anio}`
}
