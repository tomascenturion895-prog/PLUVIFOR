/** Las 6 advertencias de comparabilidad, con los códigos que devuelve la API. */
export const ADVERTENCIAS = {
  horario_corte_distinto: {
    texto: 'Horario de corte distinto',
    descripcion: 'Las redes cuentan el día de lluvia en horarios distintos (07:00 o 09:00).',
  },
  observado_vs_estimado: {
    texto: 'Observado vs. estimado',
    descripcion: 'Se están comparando datos medidos con datos estimados.',
  },
  cobertura_despareja: {
    texto: 'Cobertura despareja',
    descripcion: 'Las series no tienen la misma cantidad de días con dato.',
  },
  dato_sin_validar: {
    texto: 'Dato sin validar',
    descripcion: 'Hay valores que todavía no fueron validados.',
  },
  ceros_prolongados: {
    texto: 'Racha de ceros',
    descripcion: 'Una racha de 60 días o más en 0 mm: puede ser un problema del sensor.',
  },
  inconsistente_con_vecinas: {
    texto: 'Inconsistente con vecinas',
    descripcion: 'Estaciones vecinas registran lluvia mientras esta marca 0 mm.',
  },
} as const

export type CodigoAdvertencia = keyof typeof ADVERTENCIAS

/** Texto para mostrar los milímetros de un día: un hueco nunca se muestra como 0. */
export function textoMm(mm: number | null): string {
  return mm === null ? 'sin dato' : `${mm.toLocaleString('es-AR', { maximumFractionDigits: 1 })} mm`
}
