import type { Day } from '../api/types'

export interface Punto {
  fecha: string
  /** Lluvia del día; null en un hueco (la barra no se dibuja: nunca es 0). */
  mm: number | null
  /** Altura de la marca de «sin dato»; null si el día tiene dato. */
  hueco: number | null
  estado: Day['state']
}

/** Convierte los días de la API en puntos del gráfico, marcando los huecos como huecos. */
export function armarPuntos(days: Day[]): Punto[] {
  const maximo = Math.max(1, ...days.map((d) => d.mm ?? 0))
  return days.map((d) => ({
    fecha: d.obs_date,
    mm: d.state === 'dato' ? d.mm : null,
    hueco: d.state === 'dato' ? null : maximo,
    estado: d.state,
  }))
}
