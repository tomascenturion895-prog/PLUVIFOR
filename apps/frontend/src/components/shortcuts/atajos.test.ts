import { describe, expect, it } from 'vitest'
import { FECHA_CORTE } from '../../constants'
import { ATAJOS, resolverEstaciones } from './atajos'

describe('atajos', () => {
  it('ninguno pasa de la fecha de corte', () => {
    for (const a of ATAJOS) expect(a.hasta <= FECHA_CORTE).toBe(true)
  })

  it('la última semana son 7 días terminando en el corte', () => {
    const a = ATAJOS.find((x) => x.id === 'ultima-semana')
    expect(a?.hasta).toBe(FECHA_CORTE)
    expect(a?.desde).toBe('2026-10-25')
    expect(a?.reproducir).toBe(false)
  })

  it('El Niño 2015/16 se reproduce mes a mes', () => {
    expect(ATAJOS.find((x) => x.id === 'nino-2015-16')?.reproducir).toBe(true)
  })

  it('el caso 424 contra 425 usa el período del cero prolongado y no se reproduce', () => {
    const a = ATAJOS.find((x) => x.id === 'caso-424-425')
    expect(a).toMatchObject({ desde: '2015-09-20', hasta: '2016-06-26', reproducir: false })
    expect(a?.codigos).toEqual(['424', '425'])
  })

  it('resuelve códigos a ids y dice cuáles faltan, sin inventarlos', () => {
    const cat = [
      { id: 7, code: '424' },
      { id: 9, code: '51' },
    ]
    expect(resolverEstaciones(['424'], cat)).toEqual({ ids: [7], faltan: [] })
    expect(resolverEstaciones(['424', '425'], cat)).toEqual({ ids: [7], faltan: ['425'] })
    expect(resolverEstaciones([], cat)).toEqual({ ids: [], faltan: [] })
  })
})
