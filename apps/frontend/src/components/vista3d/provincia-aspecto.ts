import { DALTONICO, esDaltonico } from '../tema/tema-colores'
import { COLOR_CLASE, type Clase, type Departamento } from './exposicion-datos'

export type Modo = 'exposicion' | 'pluvial' | 'hidrica'

export interface PinEstacion {
  id: number
  nombre: string
  lon: number
  lat: number
  clase: Clase | null
  descartada: boolean
}

export const ALTURA_SIN_DATO = 4
const ESCALA: Record<Clase, number> = { baja: 16, media: 38, alta: 66 }
export const COLOR_HIDRICA: Record<Clase, string> = {
  get baja() {
    return esDaltonico() ? DALTONICO.hidrica.baja : '#c6dbef'
  },
  get media() {
    return esDaltonico() ? DALTONICO.hidrica.media : '#6baed6'
  },
  get alta() {
    return esDaltonico() ? DALTONICO.hidrica.alta : '#2171b5'
  },
}

/** Alto y color de un departamento según lo que se esté mirando. null = sin dato (rayado). */
export function aspectoDepartamento(
  d: Departamento,
  modo: Modo,
  maxDensidad: number,
): { alto: number; color: string | null } {
  if (modo === 'hidrica') {
    if (!d.hidrica) return { alto: ALTURA_SIN_DATO, color: null }
    const t = maxDensidad > 0 ? d.hidrica.densidad / maxDensidad : 0
    return { alto: 8 + t * 58, color: COLOR_HIDRICA[d.hidrica.clase] }
  }
  const clase = modo === 'pluvial' ? d.pluvial : d.exposicion
  if (!clase) return { alto: ALTURA_SIN_DATO, color: null }
  return { alto: ESCALA[clase], color: COLOR_CLASE[clase] }
}
