import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { SeriesCompare, SeriesCompareStation, StationList } from '../api/types'
import Compare from './Compare'
import { alinearSeries, diferenciaCobertura } from './compare-datos'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getStations: vi.fn(),
  getCompare: vi.fn(),
}))
import { getCompare, getStations } from '../api/client'

const ESTACIONES = {
  items: [
    { id: 1, code: '424', name: 'El Colorado' },
    { id: 2, code: '425', name: 'Bartolomé de las Casas' },
    { id: 3, code: '51', name: 'Tercera' },
  ],
  total: 3,
  limit: 200,
  offset: 0,
} as unknown as StationList

const FUENTE = {
  code: 's',
  name: 'SIGA',
  network: 'INTA',
  category: 'observado',
  day_cutoff_local: '09:00',
} as const

function est(
  id: number,
  nombre: string,
  mms: (number | null)[],
  coverage = 1,
): SeriesCompareStation {
  return {
    station_id: id,
    station_name: nombre,
    source: FUENTE,
    category: 'observado',
    summary: {
      days_in_period: mms.length,
      days_with_data: mms.filter((m) => m !== null).length,
      days_sin_fila: 0,
      days_fila_sin_valor: mms.filter((m) => m === null).length,
      coverage,
      accumulated_mm: mms.every((m) => m === null)
        ? null
        : mms.reduce<number>((a, m) => a + (m ?? 0), 0),
    },
    warnings: [],
    days: mms.map((m, i) => ({
      obs_date: `2016-01-0${i + 1}`,
      state: m === null ? 'fila_sin_valor' : 'dato',
      mm: m,
      category: 'observado',
      source: 's',
      flags: [],
    })),
  }
}

function comparacion(extra: Partial<SeriesCompare> = {}): SeriesCompare {
  return {
    category: 'observado',
    date_from: '2016-01-01',
    date_to: '2016-01-03',
    data_cutoff_date: '2026-10-31',
    clipped_to_cutoff: false,
    stations: [est(1, 'El Colorado', [0, 0, 0]), est(2, 'Bartolomé', [5, null, 3], 0.66)],
    comparability_warnings: [
      {
        code: 'racha_ceros',
        message: 'Una estación marca 0 mm durante 281 días seguidos.',
        severity: 'alerta',
        start_date: null,
        end_date: null,
      },
    ],
    not_evaluated: [],
    notice: 'PROTOTIPO',
    ...extra,
  }
}

afterEach(() => vi.clearAllMocks())

async function elegir(usuario: ReturnType<typeof userEvent.setup>, ...nombres: string[]) {
  for (const n of nombres)
    await usuario.click(await screen.findByRole('checkbox', { name: new RegExp(n) }))
}

describe('alinearSeries', () => {
  it('un hueco queda null y nunca 0', () => {
    const filas = alinearSeries([est(1, 'A', [5, null]), est(2, 'B', [null, 2])])
    expect(filas).toEqual([
      { fecha: '2016-01-01', s1: 5, s2: null },
      { fecha: '2016-01-02', s1: null, s2: 2 },
    ])
  })

  it('una fecha que una estación no tiene queda null en ella', () => {
    const a = est(1, 'A', [1, 2])
    const b = { ...est(2, 'B', [9]) }
    expect(alinearSeries([a, b])[1]).toEqual({ fecha: '2016-01-02', s1: 2, s2: null })
  })

  it('calcula la diferencia de cobertura', () => {
    expect(diferenciaCobertura([est(1, 'A', [1], 1), est(2, 'B', [1], 0.4)])).toBe(60)
    expect(diferenciaCobertura([est(1, 'A', [1], 1)])).toBe(0)
  })
})

describe('Comparador', () => {
  it('no deja comparar con menos de 2 estaciones', async () => {
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424')
    expect(screen.getByRole('button', { name: 'Comparar' })).toBeDisabled()
    expect(screen.getByText(/al menos una estación más/)).toBeInTheDocument()
  })

  it('compara 424 y 425 y muestra la advertencia de racha de ceros', async () => {
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    vi.mocked(getCompare).mockResolvedValue(comparacion())
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424', '425')
    await usuario.click(screen.getByRole('button', { name: 'Comparar' }))
    const lista = await screen.findByRole('list', { name: 'Advertencias de comparabilidad' })
    expect(lista).toHaveTextContent('281 días seguidos')
    expect(getCompare).toHaveBeenCalledWith(expect.objectContaining({ stationIds: [1, 2] }))
  })

  it('muestra las advertencias de cada estación aunque no haya advertencias entre series (caso 424 vs 425)', async () => {
    const e424 = est(1, 'El Colorado', [0, 0, 0])
    e424.warnings = [
      {
        code: 'ceros_prolongados',
        message: '281 días seguidos con 0 mm: puede ser un sensor sin registrar.',
        severity: 'aviso',
        start_date: '2015-09-20',
        end_date: '2016-06-26',
      },
    ]
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    vi.mocked(getCompare).mockResolvedValue(
      comparacion({
        stations: [e424, est(2, 'Bartolomé', [5, null, 3], 0.66)],
        comparability_warnings: [],
      }),
    )
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424', '425')
    await usuario.click(screen.getByRole('button', { name: 'Comparar' }))
    const bloque = await screen.findByRole('region', {
      name: 'Advertencias de calidad por estación',
    })
    expect(bloque).toHaveTextContent('El Colorado')
    expect(bloque).toHaveTextContent('281 días seguidos')
    expect(bloque).toHaveTextContent('2015-09-20 a 2016-06-26')
    expect(
      screen.queryByText('No se detectaron advertencias de comparabilidad entre estas series.'),
    ).toBeNull()
  })

  it('sin advertencias en ningún nivel lo dice', async () => {
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    vi.mocked(getCompare).mockResolvedValue(comparacion({ comparability_warnings: [] }))
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424', '425')
    await usuario.click(screen.getByRole('button', { name: 'Comparar' }))
    expect(await screen.findByText(/No se detectaron advertencias/)).toBeInTheDocument()
    expect(
      screen.queryByRole('region', { name: 'Advertencias de calidad por estación' }),
    ).toBeNull()
  })

  it('la tabla muestra el acumulado, los días sin dato y no suma estaciones', async () => {
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    vi.mocked(getCompare).mockResolvedValue(comparacion())
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424', '425')
    await usuario.click(screen.getByRole('button', { name: 'Comparar' }))
    const fila = await screen.findByRole('row', { name: /Bartolomé/ })
    expect(fila).toHaveTextContent('2 de 3')
    expect(fila).toHaveTextContent('8 mm')
    expect(fila).toHaveTextContent('66 %')
    expect(screen.getByText(/no se suman entre estaciones/)).toBeInTheDocument()
  })

  it('una estación sin ningún dato muestra «sin dato», no 0 mm', async () => {
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    vi.mocked(getCompare).mockResolvedValue(
      comparacion({ stations: [est(1, 'Muda', [null, null, null], 0), est(2, 'Otra', [1, 1, 1])] }),
    )
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424', '425')
    await usuario.click(screen.getByRole('button', { name: 'Comparar' }))
    const fila = await screen.findByRole('row', { name: /Muda/ })
    expect(fila).toHaveTextContent('sin dato')
    expect(fila).not.toHaveTextContent('0 mm')
  })

  it('máximo 4 estaciones', async () => {
    vi.mocked(getStations).mockResolvedValue({
      ...ESTACIONES,
      items: [1, 2, 3, 4, 5].map((n) => ({
        ...ESTACIONES.items[0],
        id: n,
        code: `E${n}`,
        name: `Est ${n}`,
      })),
    })
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, 'E1', 'E2', 'E3', 'E4', 'E5')
    expect(screen.getAllByRole('checkbox', { checked: true })).toHaveLength(4)
  })

  it('muestra el error de la API en español', async () => {
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    vi.mocked(getCompare).mockRejectedValue(
      new ApiError(422, 'invalid', 'Los datos enviados no son válidos.'),
    )
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424', '425')
    await usuario.click(screen.getByRole('button', { name: 'Comparar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('no son válidos')
  })

  it('un período invertido bloquea el botón', async () => {
    vi.mocked(getStations).mockResolvedValue(ESTACIONES)
    const usuario = userEvent.setup()
    render(<Compare />)
    await elegir(usuario, '424', '425')
    await usuario.clear(screen.getByLabelText('Hasta'))
    await usuario.type(screen.getByLabelText('Hasta'), '2000-01-01')
    expect(screen.getByRole('button', { name: 'Comparar' })).toBeDisabled()
  })
})
