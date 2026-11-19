import type { DataCategory } from '../../api/types'
import { FECHA_CORTE } from '../../constants'

export interface SeleccionValor {
  desde: string
  hasta: string
  category: DataCategory
  zona: string
  /** Vacío = todas las estaciones de la zona. */
  estaciones: number[]
}

export function periodoValido(v: Pick<SeleccionValor, 'desde' | 'hasta'>): boolean {
  return v.desde !== '' && v.hasta !== '' && v.desde <= v.hasta && v.hasta <= FECHA_CORTE
}
