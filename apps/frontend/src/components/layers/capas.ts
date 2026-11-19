/**
 * Capas del mapa (SCRUM-101). Solo capas de lluvia y de la red de estaciones:
 * nada de ríos, caudales ni riesgo.
 *
 * Reglas: observado, referencia y estimado son capas separadas, cada una con su propio total.
 * Prenderlas juntas no las suma ni las promedia.
 */
import type { DataCategory } from '../../api/types'

export type CapaId = 'observado' | 'referencia' | 'estimado' | 'reportes' | 'silencio'

export interface Capa {
  id: CapaId
  nombre: string
  /** Categoría del dato, si la capa trae lluvia. */
  categoria: DataCategory | null
  fuente: string
  leyenda: string
  /** Si no hay de dónde sacarla, se dice por qué en lugar de mostrar una capa vacía. */
  noDisponible?: string
}

export const CAPAS: readonly Capa[] = [
  {
    id: 'observado',
    nombre: 'Lluvia observada',
    categoria: 'observado',
    fuente: 'Estaciones de las redes cargadas (SIGA/INTA, red provincial)',
    leyenda: 'Círculo lleno, con el color del acumulado. Trazo de puntos: sin dato (no es 0 mm).',
  },
  {
    id: 'referencia',
    nombre: 'Referencia (normales climáticas)',
    categoria: 'referencia',
    fuente: 'Normales climáticas 1991-2020 del SMN',
    leyenda: 'Anillo de guiones violeta. Es un valor de comparación, no una medición del período.',
  },
  {
    id: 'estimado',
    nombre: 'Estimado',
    categoria: 'estimado',
    fuente: 'Valores estimados (por ejemplo CHIRPS)',
    leyenda: 'Anillo punteado naranja. Es un cálculo, no una medición.',
  },
  {
    id: 'reportes',
    nombre: 'Reportes policiales',
    categoria: null,
    fuente: 'Sin fuente cargada',
    leyenda: '',
    noDisponible:
      'Pendiente: todavía no hay una fuente de reportes policiales. Los reportes de campo piden clave de administración y llevan datos personales, por eso no se muestran en el mapa público.',
  },
  {
    id: 'silencio',
    nombre: 'Estaciones en silencio',
    categoria: null,
    fuente: 'Salud de la red, calculada contra la fecha de corte',
    leyenda: 'Anillo rojo de línea doble: la estación no informa hace días. No es lluvia.',
  },
]

export const CAPAS_INICIALES: readonly CapaId[] = ['observado']

export function capaPorId(id: CapaId): Capa {
  const capa = CAPAS.find((c) => c.id === id)
  if (!capa) throw new Error(`Capa desconocida: ${id}`)
  return capa
}

/** Prende o apaga una capa. Una capa no disponible no se puede prender. */
export function alternar(activas: readonly CapaId[], id: CapaId): CapaId[] {
  if (capaPorId(id).noDisponible) return [...activas]
  return activas.includes(id) ? activas.filter((a) => a !== id) : [...activas, id]
}

/** Categorías de lluvia encendidas, en el orden fijo observado → referencia → estimado. */
export function categoriasActivas(activas: readonly CapaId[]): DataCategory[] {
  return CAPAS.filter((c) => c.categoria !== null && activas.includes(c.id)).map(
    (c) => c.categoria as DataCategory,
  )
}

export interface TotalCapa {
  categoria: DataCategory
  /** Estaciones con acumulado en esta capa. */
  conDato: number
  /** Estaciones sin dato en esta capa (huecos: no cuentan como 0 mm). */
  sinDato: number
}

/** Un resumen por capa. Nunca se devuelve un total general que mezcle categorías. */
export function totalesPorCapa(
  acumulados: ReadonlyMap<DataCategory, readonly { accumulated_mm: number | null }[]>,
  activas: readonly CapaId[],
): TotalCapa[] {
  return categoriasActivas(activas).flatMap((categoria) => {
    const estaciones = acumulados.get(categoria)
    if (!estaciones) return []
    const conDato = estaciones.filter((s) => s.accumulated_mm != null).length
    return [{ categoria, conDato, sinDato: estaciones.length - conDato }]
  })
}
