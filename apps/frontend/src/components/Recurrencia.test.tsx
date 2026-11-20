import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { RecurrenceOut } from '../api/types'
import Recurrencia from './Recurrencia'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getRecurrence: vi.fn(),
}))
import { getRecurrence } from '../api/client'

function datos(extra: Partial<RecurrenceOut>): RecurrenceOut {
  return {
    station_id: 2,
    station_name: 'El Colorado',
    category: 'observado',
    date_from: '2013-01-01',
    date_to: '2026-10-31',
    clipped_to_cutoff: false,
    valid_days: 2412,
    observed_years: 6.6,
    excluded_zero_run_days: 0,
    gap_days: 2725,
    sufficient_history: true,
    min_observed_years: 5,
    ge50: 30,
    ge100: 1,
    ge50_per_year: 4.5,
    ge100_per_year: 0.15,
    ge50_every_years: 0.2,
    ge100_every_years: 6.6,
    by_year: [{ year: 2014, valid_days: 300, ge50: 5, ge100: 0 }],
    notice: 'Frecuencia histórica. No es una predicción ni una alerta.',
    ...extra,
  }
}

afterEach(() => vi.clearAllMocks())

describe('Recurrencia', () => {
  it('muestra el conteo y la frecuencia pasada, aclarando que no es una predicción', async () => {
    vi.mocked(getRecurrence).mockResolvedValue(datos({}))
    render(<Recurrencia stationId={2} />)
    expect(await screen.findByRole('note')).toHaveTextContent(/No es una predicción/)
    expect(screen.getByText('30')).toBeInTheDocument()
    expect(screen.getByText(/una vez cada 6,6 años/)).toBeInTheDocument()
    expect(getRecurrence).toHaveBeenCalledWith(
      { stationId: 2, from: '2013-01-01', to: '2026-10-31' },
      expect.anything(),
    )
  })

  it('con poca historia informa el conteo pero no calcula ninguna frecuencia', async () => {
    vi.mocked(getRecurrence).mockResolvedValue(
      datos({
        sufficient_history: false,
        observed_years: 2.4,
        ge50_every_years: null,
        ge100_every_years: null,
      }),
    )
    render(<Recurrencia stationId={1} />)
    expect(await screen.findByText(/no se calcula ninguna frecuencia/)).toBeInTheDocument()
    expect(screen.getAllByText(/Historia insuficiente/)).toHaveLength(2)
    expect(screen.queryByText(/una vez cada/)).not.toBeInTheDocument()
  })

  it('sin eventos no inventa una frecuencia', async () => {
    vi.mocked(getRecurrence).mockResolvedValue(
      datos({ ge50: 0, ge100: 0, ge50_every_years: null, ge100_every_years: null }),
    )
    render(<Recurrencia stationId={2} />)
    expect(await screen.findAllByText(/Sin eventos en el período observado/)).toHaveLength(2)
  })

  it('explica los ceros excluidos y los días sin dato (que no son 0 mm)', async () => {
    vi.mocked(getRecurrence).mockResolvedValue(datos({ excluded_zero_run_days: 281 }))
    render(<Recurrencia stationId={2} />)
    expect(await screen.findByText(/281 días con dato quedaron afuera/)).toBeInTheDocument()
    expect(screen.getByText(/no se cuentan como lluvia ni como días secos/)).toBeInTheDocument()
  })

  it('si la API falla lo dice y permite reintentar', async () => {
    vi.mocked(getRecurrence).mockRejectedValue(new ApiError(500, 'x', 'No se pudo cargar'))
    render(<Recurrencia stationId={2} />)
    expect(await screen.findByText(/No se pudo cargar/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /reintentar/i }))
    expect(getRecurrence).toHaveBeenCalledTimes(2)
  })
})
