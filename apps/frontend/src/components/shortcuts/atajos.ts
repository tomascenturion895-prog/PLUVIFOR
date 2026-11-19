/** Atajos de la maqueta (SCRUM-99). Usan solo series reales ya cargadas. */
import { FECHA_CORTE } from '../../constants'
import { ultimosDias } from '../maqueta/maqueta-datos'

export type AtajoId = 'ultima-semana' | 'nino-2015-16' | 'caso-424-425'

export interface Atajo {
  id: AtajoId
  nombre: string
  descripcion: string
  desde: string
  hasta: string
  /** Códigos de estación (no ids: los ids dependen de la base). Vacío = todas. */
  codigos: readonly string[]
  /** Si recorre el período mes a mes. */
  reproducir: boolean
}

export const ATAJOS: readonly Atajo[] = [
  {
    id: 'ultima-semana',
    nombre: 'Última semana',
    descripcion: 'Los 7 días hasta la fecha de corte.',
    ...ultimosDias(FECHA_CORTE, 7),
    codigos: [],
    reproducir: false,
  },
  {
    id: 'nino-2015-16',
    nombre: 'El Niño 2015/16',
    descripcion: 'De septiembre de 2015 a junio de 2016, mes a mes, con los datos reales del SIGA.',
    desde: '2015-09-01',
    hasta: '2016-06-30',
    codigos: [],
    reproducir: true,
  },
  {
    id: 'caso-424-425',
    nombre: 'Caso 424 contra 425',
    descripcion:
      'La 424 marca 0 mm durante 281 días seguidos mientras la 425 registra 1.265 mm. Se advierte, no se da por bueno.',
    desde: '2015-09-20',
    hasta: '2016-06-26',
    codigos: ['424', '425'],
    reproducir: false,
  },
]

/** Pasa los códigos a ids. Si falta alguna estación, se informa cuál: no se inventa. */
export function resolverEstaciones(
  codigos: readonly string[],
  catalogo: readonly { id: number; code: string }[],
): { ids: number[]; faltan: string[] } {
  const ids: number[] = []
  const faltan: string[] = []
  for (const codigo of codigos) {
    const est = catalogo.find((e) => e.code === codigo)
    if (est) ids.push(est.id)
    else faltan.push(codigo)
  }
  return { ids, faltan }
}
