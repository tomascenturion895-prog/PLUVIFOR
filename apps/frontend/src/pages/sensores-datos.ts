const ARGENTINA_UTC = -3 // sin horario de verano

/** 2026-10-20T10:00:00Z → «20/10/2026 07:00» (hora de Argentina, sin depender de la zona del equipo). */
export function fechaHoraArgentina(iso: string): string {
  const instante = new Date(iso)
  if (Number.isNaN(instante.getTime())) return 'Sin dato'
  const local = new Date(instante.getTime() + ARGENTINA_UTC * 3600_000)
  const dos = (n: number) => String(n).padStart(2, '0')
  return (
    `${dos(local.getUTCDate())}/${dos(local.getUTCMonth() + 1)}/${local.getUTCFullYear()} ` +
    `${dos(local.getUTCHours())}:${dos(local.getUTCMinutes())}`
  )
}

export const AVISO_SIMULADAS =
  'Lecturas simuladas: no son datos de sensores reales ni se suman a las series de lluvia.'
