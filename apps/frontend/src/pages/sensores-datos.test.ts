import { describe, expect, it } from 'vitest'
import { armarPuntosSensor, diaArgentina, fechaHoraArgentina } from './sensores-datos'

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

describe('armarPuntosSensor', () => {
  const l = (read_at: string, mm: number) => ({ read_at, mm })

  it('un día sin lectura entre dos lecturas es un hueco, no un 0', () => {
    const puntos = armarPuntosSensor([
      l('2026-10-22T10:00:00Z', 4),
      l('2026-10-20T10:00:00Z', 12.5),
    ])
    expect(puntos.map((p) => p.mm)).toEqual([12.5, null, 4])
    expect(puntos[1]).toMatchObject({ etiqueta: '21/10/2026', hueco: 12.5 })
    expect(puntos[0].hueco).toBeNull()
  })

  it('una lectura de 0 mm sigue siendo 0 y no un hueco', () => {
    const puntos = armarPuntosSensor([l('2026-10-20T10:00:00Z', 0)])
    expect(puntos).toHaveLength(1)
    expect(puntos[0].mm).toBe(0)
    expect(puntos[0].hueco).toBeNull()
  })

  it('sin lecturas no hay puntos', () => {
    expect(armarPuntosSensor([])).toEqual([])
  })

  it('la fecha de Argentina no se corre por la zona horaria', () => {
    expect(diaArgentina('2026-10-21T01:30:00Z')).toBe('2026-10-20')
  })
})
