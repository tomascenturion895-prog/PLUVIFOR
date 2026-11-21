import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { NetworkHealth } from '../api/types'
import UltimoPeriodoConDato from './UltimoPeriodoConDato'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getNetworkHealth: vi.fn(),
}))
import { getNetworkHealth } from '../api/client'

function salud(lecturas: (string | null)[]): NetworkHealth {
  return {
    category: 'observado',
    data_cutoff_date: '2026-10-31',
    silent_after_days: 30,
    active: 0,
    silent: lecturas.length,
    no_data: 0,
    stations: lecturas.map((last_reading_date, i) => ({
      station_id: i + 1,
      code: String(i),
      name: `E${i}`,
      zone: null,
      department: null,
      source: 'siga_inta',
      network: 'INTA',
      state: 'en_silencio',
      last_reading_date,
      last_reading_mm: null,
      days_since_last: null,
    })),
  } as unknown as NetworkHealth
}

beforeEach(() => vi.mocked(getNetworkHealth).mockReset())

describe('UltimoPeriodoConDato', () => {
  it('si el período empieza después de la última lectura de la red, ofrece saltar a ese período', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue(salud(['2022-12-06', '2023-03-23', null]))
    const onIr = vi.fn()
    render(<UltimoPeriodoConDato desde="2026-10-02" dias={30} onIr={onIr} />)
    expect(await screen.findByText(/es «sin dato», no 0 mm/)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /último período con dato/i }))
    expect(onIr).toHaveBeenCalledWith('2023-02-22', '2023-03-23')
  })

  it('si el período ya toca una lectura, no muestra nada', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue(salud(['2023-03-23']))
    const { container } = render(
      <UltimoPeriodoConDato desde="2023-03-01" dias={30} onIr={vi.fn()} />,
    )
    await waitFor(() => expect(getNetworkHealth).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it('si ninguna estación tiene lecturas no inventa una fecha', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue(salud([null, null]))
    const { container } = render(
      <UltimoPeriodoConDato desde="2026-10-02" dias={30} onIr={vi.fn()} />,
    )
    await waitFor(() => expect(getNetworkHealth).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it('si la consulta falla, no rompe la pantalla', async () => {
    vi.mocked(getNetworkHealth).mockRejectedValueOnce(
      new ApiError(0, 'network', 'No se pudo conectar con el servidor.'),
    )
    const { container } = render(
      <UltimoPeriodoConDato desde="2026-10-02" dias={30} onIr={vi.fn()} />,
    )
    await waitFor(() => expect(getNetworkHealth).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })
})
