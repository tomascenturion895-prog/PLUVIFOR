import { describe, expect, it } from 'vitest'
import { fechaHoraArgentina } from './sensores-datos'

describe('fechaHoraArgentina', () => {
  it('pasa de UTC a la hora de Argentina', () => {
    expect(fechaHoraArgentina('2026-10-20T10:00:00Z')).toBe('20/10/2026 07:00')
  })

  it('cruza el día hacia atrás', () => {
    expect(fechaHoraArgentina('2026-11-01T01:30:00Z')).toBe('31/10/2026 22:30')
  })

  it('una fecha inválida se muestra como sin dato, no como una fecha inventada', () => {
    expect(fechaHoraArgentina('ayer')).toBe('Sin dato')
  })
})
