import { fechaHoraArgentina } from '../../pages/sensores-datos'

/** «2026-10-20T10:00:00Z» → «07:00» (hora de Argentina). */
export function horaDe(iso: string): string {
  return fechaHoraArgentina(iso).split(' ')[1] ?? ''
}
