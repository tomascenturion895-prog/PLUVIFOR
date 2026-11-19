import { describe, expect, it } from 'vitest'
import type { Day } from '../api/types'
import { armarPuntos } from './serie-diaria-datos'

const dia = (state: Day['state'], mm: number | null): Day => ({
  obs_date: '2016-01-01',
  state,
  mm,
  category: 'observado',
  source: 's',
  flags: [],
})

describe('armarPuntos', () => {
  it('un hueco no tiene milímetros: la barra no se dibuja', () => {
    const [sinFila, sinValor] = armarPuntos([dia('sin_fila', null), dia('fila_sin_valor', null)])
    expect(sinFila.mm).toBeNull()
    expect(sinValor.mm).toBeNull()
    expect(sinFila.hueco).toBeGreaterThan(0)
  })

  it('un cero real se dibuja como 0 y no como hueco', () => {
    const [cero] = armarPuntos([dia('dato', 0)])
    expect(cero.mm).toBe(0)
    expect(cero.hueco).toBeNull()
  })

  it('la marca del hueco alcanza el máximo del período', () => {
    const puntos = armarPuntos([dia('dato', 40), dia('sin_fila', null)])
    expect(puntos[1].hueco).toBe(40)
  })

  it('un período solo con huecos igual tiene altura visible', () => {
    expect(armarPuntos([dia('sin_fila', null)])[0].hueco).toBe(1)
  })
})
