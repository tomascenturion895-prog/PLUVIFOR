import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { GapEstimate, GapEstimateList } from '../api/types'
import EstimacionesHuecos from './EstimacionesHuecos'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getEstimates: vi.fn(),
}))
import { getEstimates } from '../api/client'

const AVISO =
  'Valores estimados, no medidos: cubren días SIN DATO y nunca se suman ni se promedian.'

function estimacion(extra: Partial<GapEstimate> = {}): GapEstimate {
  return {
    station_id: 1,
    obs_date: '2020-01-04',
    mm: 10,
    category: 'estimado',
    gap_state: 'sin_fila',
    method: 'vecinas_idw_v1',
    detail: { vecinas: [{ station_id: 2, name: 'Vecina B', distance_km: 4.5, mm: 10 }] },
    created_at: '2026-11-19T15:00:00Z',
    ...extra,
  }
}

function lista(items: GapEstimate[], total = items.length): GapEstimateList {
  return { category: 'estimado', notice: AVISO, items, total, limit: 200, offset: 0 }
}

function ver() {
  return render(<EstimacionesHuecos stationId={1} desde="2020-01-01" hasta="2020-01-31" />)
}

afterEach(() => vi.clearAllMocks())

describe('Días sin dato con valor estimado', () => {
  it('muestra cada día como Estimado, con su método, vecinas y el aviso de que no es medido', async () => {
    vi.mocked(getEstimates).mockResolvedValue(
      lista([
        estimacion(),
        estimacion({ obs_date: '2020-01-05', mm: 0, gap_state: 'fila_sin_valor' }),
      ]),
    )
    ver()
    expect(await screen.findByText(AVISO)).toBeInTheDocument()
    const tabla = screen.getByRole('table')
    const filas = within(tabla).getAllByRole('row').slice(1)
    expect(filas).toHaveLength(2)
    expect(within(filas[0]).getByText('10 mm')).toBeInTheDocument()
    expect(within(filas[0]).getByText('Estimado')).toBeInTheDocument()
    expect(within(filas[0]).getByText(/Vecina B \(4,5 km, 10 mm\)/)).toBeInTheDocument()
    // Un cero estimado se muestra como valor, y el día original sigue siendo un hueco.
    expect(within(filas[1]).getByText('0 mm')).toBeInTheDocument()
    expect(within(filas[1]).getByText('Fila sin valor')).toBeInTheDocument()
  })

  it('aclara en el título de la tabla que no suman al acumulado observado', async () => {
    vi.mocked(getEstimates).mockResolvedValue(lista([estimacion()], 3))
    ver()
    expect(
      await screen.findByText(/1 de 3 días estimados \(no suman al acumulado/),
    ).toBeInTheDocument()
  })

  it('un método desconocido se muestra tal cual, sin inventar un nombre', async () => {
    vi.mocked(getEstimates).mockResolvedValue(
      lista([estimacion({ method: 'otro_v9', detail: {} })]),
    )
    ver()
    expect(await screen.findByText('otro_v9')).toBeInTheDocument()
  })

  it('sin estimaciones dice que los días sin dato siguen sin dato', async () => {
    vi.mocked(getEstimates).mockResolvedValue(lista([]))
    ver()
    expect(await screen.findByText(/los días sin dato siguen sin dato/)).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('pide solo la estación y el período que se están viendo', async () => {
    vi.mocked(getEstimates).mockResolvedValue(lista([]))
    ver()
    await screen.findByText(AVISO)
    expect(getEstimates).toHaveBeenCalledWith(
      { stationId: 1, from: '2020-01-01', to: '2020-01-31', limit: 200 },
      expect.any(AbortSignal),
    )
  })

  it('si falla muestra el error en español y permite reintentar', async () => {
    vi.mocked(getEstimates)
      .mockRejectedValueOnce(new ApiError(0, 'network', 'No se pudo conectar con el servidor.'))
      .mockResolvedValueOnce(lista([estimacion()]))
    ver()
    expect(await screen.findByText('No se pudo conectar con el servidor.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /reintentar/i }))
    expect(
      await screen.findByText('Vecina B (4,5 km, 10 mm)', { exact: false }),
    ).toBeInTheDocument()
  })
})
