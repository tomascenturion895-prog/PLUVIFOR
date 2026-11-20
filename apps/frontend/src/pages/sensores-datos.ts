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

const DIA_MS = 24 * 3600_000
/** Tope de días vacíos que se dibujan entre dos lecturas (evita un gráfico enorme por un error de fecha). */
const MAX_HUECOS_ENTRE_LECTURAS = 366

/** Día (AAAA-MM-DD) en hora de Argentina de un instante ISO. */
export function diaArgentina(iso: string): string {
  const local = new Date(new Date(iso).getTime() + ARGENTINA_UTC * 3600_000)
  return local.toISOString().slice(0, 10)
}

export interface PuntoSensor {
  etiqueta: string
  /** Lluvia medida por el dispositivo; null en un día sin lectura (nunca es 0). */
  mm: number | null
  /** Altura de la marca de «sin lectura»; null si ese punto es una lectura. */
  hueco: number | null
}

/**
 * Convierte lecturas (cualquier orden) en puntos de gráfico. Cada lectura es un punto; entre dos
 * lecturas que distan más de un día, cada día sin lectura es un hueco rayado, no un 0 mm.
 */
export function armarPuntosSensor(
  lecturas: ReadonlyArray<{ read_at: string; mm: number }>,
): PuntoSensor[] {
  const ordenadas = [...lecturas].sort((a, b) => a.read_at.localeCompare(b.read_at))
  const maximo = Math.max(1, ...ordenadas.map((l) => l.mm))
  const puntos: PuntoSensor[] = []
  let anterior: string | null = null
  for (const l of ordenadas) {
    const dia = diaArgentina(l.read_at)
    if (anterior !== null) {
      const faltan = Math.round((Date.parse(dia) - Date.parse(anterior)) / DIA_MS) - 1
      for (let i = 1; i <= Math.min(faltan, MAX_HUECOS_ENTRE_LECTURAS); i++) {
        const faltante = new Date(Date.parse(anterior) + i * DIA_MS).toISOString().slice(0, 10)
        puntos.push({ etiqueta: fechaCorta(faltante), mm: null, hueco: maximo })
      }
    }
    puntos.push({ etiqueta: fechaHoraArgentina(l.read_at), mm: l.mm, hueco: null })
    anterior = dia
  }
  return puntos
}

/** 2026-10-20 → «20/10/2026». */
export function fechaCorta(dia: string): string {
  const [anio, mes, d] = dia.split('-')
  return `${d}/${mes}/${anio}`
}
