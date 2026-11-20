import { describe, expect, it } from 'vitest'
import { mesesDelPeriodo, siguiente } from './timeline-datos'

const CORTE = '2026-10-31'

describe('meses del período', () => {
  it('El Niño 2015/16 son 10 meses, de septiembre a junio, con el cambio de año', () => {
    const m = mesesDelPeriodo('2015-09-01', '2016-06-30', CORTE)
    expect(m).toHaveLength(10)
    expect(m[0]).toEqual({ clave: '2015-09', desde: '2015-09-01', hasta: '2015-09-30' })
    expect(m[4].clave).toBe('2016-01')
    expect(m[9]).toEqual({ clave: '2016-06', desde: '2016-06-01', hasta: '2016-06-30' })
  })

  it('los extremos son parciales y nunca se sale del período', () => {
    const m = mesesDelPeriodo('2015-09-20', '2016-06-26', CORTE)
    expect(m[0].desde).toBe('2015-09-20')
    expect(m.at(-1)?.hasta).toBe('2016-06-26')
  })

  it('febrero de un año bisiesto termina el 29', () => {
    expect(mesesDelPeriodo('2016-02-01', '2016-02-29', CORTE)[0].hasta).toBe('2016-02-29')
  })

  it('no pasa de la fecha de corte', () => {
    const m = mesesDelPeriodo('2026-09-01', '2027-03-01', CORTE)
    expect(m.map((x) => x.clave)).toEqual(['2026-09', '2026-10'])
    expect(m.at(-1)?.hasta).toBe(CORTE)
  })

  it('un período dentro de un solo mes da un solo paso', () => {
    expect(mesesDelPeriodo('2026-10-25', '2026-10-31', CORTE)).toHaveLength(1)
  })

  it('entradas inválidas o invertidas no dan meses', () => {
    expect(mesesDelPeriodo('2016-06-30', '2015-09-01', CORTE)).toEqual([])
    expect(mesesDelPeriodo('ayer', '2016-06-30', CORTE)).toEqual([])
    expect(mesesDelPeriodo('2027-01-01', '2027-02-01', CORTE)).toEqual([])
  })
})

describe('paso de la reproducción', () => {
  it('avanza de a un mes y termina en el último', () => {
    expect(siguiente(0, 3)).toEqual({ indice: 1, termino: false })
    expect(siguiente(1, 3)).toEqual({ indice: 2, termino: true })
    expect(siguiente(2, 3)).toEqual({ indice: 2, termino: true })
    expect(siguiente(0, 0)).toEqual({ indice: 0, termino: true })
  })
})
