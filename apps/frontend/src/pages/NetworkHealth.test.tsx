import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { NetworkHealth as Salud, StationHealth } from '../api/types'
import NetworkHealth from './NetworkHealth'
import { fechaLegible } from './network-health-datos'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getNetworkHealth: vi.fn(),
  getSensorReadings: vi.fn(),
}))
import { getNetworkHealth, getSensorReadings } from '../api/client'

beforeEach(() => {
  vi.mocked(getSensorReadings).mockResolvedValue({
    items: [],
    total: 0,
    notice: 'Lecturas simuladas.',
  })
})

function est(extra: Partial<StationHealth>): StationHealth {
  return {
    station_id: 1,
    code: '1',
    name: 'Estación',
    zone: 'norte',
    department: null,
    source: 's',
    network: 'r',
    state: 'activa',
    last_reading_date: '2026-10-31',
    last_reading_mm: 0,
    days_since_last: 0,
    ...extra,
  }
}

function salud(stations: StationHealth[]): Salud {
  return {
    category: 'observado',
    data_cutoff_date: '2026-10-31',
    silent_after_days: 30,
    active: stations.filter((s) => s.state === 'activa').length,
    silent: stations.filter((s) => s.state === 'en_silencio').length,
    no_data: stations.filter((s) => s.state === 'sin_datos').length,
    stations,
  }
}

afterEach(() => vi.clearAllMocks())

describe('Salud de la red', () => {
  it('cuenta activas, en silencio y sin datos', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue(
      salud([
        est({ station_id: 1, name: 'A' }),
        est({
          station_id: 2,
          name: 'B',
          state: 'en_silencio',
          last_reading_mm: 12,
          days_since_last: 40,
          last_reading_date: '2026-09-21',
        }),
        est({
          station_id: 3,
          name: 'C',
          state: 'sin_datos',
          last_reading_date: null,
          last_reading_mm: null,
          days_since_last: null,
        }),
      ]),
    )
    render(<NetworkHealth />)
    const resumen = await screen.findByRole('list', { name: 'Resumen de la red' })
    expect(
      within(resumen)
        .getAllByRole('listitem')
        .map((li) => li.textContent),
    ).toEqual(['1 activas', '1 en silencio', '1 sin datos'])
  })

  it('un 0 real se muestra como 0 mm y un silencio nunca como 0 mm', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue(
      salud([
        est({ station_id: 1, name: 'Cero' }),
        est({
          station_id: 2,
          name: 'Muda',
          state: 'sin_datos',
          last_reading_date: null,
          last_reading_mm: null,
          days_since_last: null,
        }),
      ]),
    )
    render(<NetworkHealth />)
    const cero = (await screen.findByRole('row', { name: /Cero/ })).textContent
    const muda = screen.getByRole('row', { name: /Muda/ }).textContent
    expect(cero).toContain('0 mm')
    expect(muda).toContain('Sin lecturas')
    expect(muda).not.toContain('0 mm')
  })

  it('muestra la fecha de la última lectura de una estación en silencio', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue(
      salud([
        est({
          name: 'Muda',
          state: 'en_silencio',
          last_reading_date: '2026-09-21',
          last_reading_mm: 12,
          days_since_last: 40,
        }),
      ]),
    )
    render(<NetworkHealth />)
    const fila = (await screen.findByRole('row', { name: /Muda/ })).textContent
    expect(fila).toContain('En silencio')
    expect(fila).toContain('21/09/2026 · 12 mm')
    expect(fila).toContain('hace 40 días')
  })

  it('sin estaciones avisa que no hay nada cargado', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue(salud([]))
    render(<NetworkHealth />)
    expect(await screen.findByText('No hay estaciones cargadas.')).toBeInTheDocument()
  })

  it('si falla, muestra el error en español y permite reintentar', async () => {
    vi.mocked(getNetworkHealth)
      .mockRejectedValueOnce(
        new ApiError(502, 'bad_gateway', 'El servicio de datos no está disponible.'),
      )
      .mockResolvedValueOnce(salud([est({})]))
    render(<NetworkHealth />)
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'El servicio de datos no está disponible.',
    )
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByRole('list', { name: 'Resumen de la red' })).toBeInTheDocument()
  })

  it('fechaLegible no corre la fecha por zona horaria', () => {
    expect(fechaLegible('2026-10-31')).toBe('31/10/2026')
  })
})
