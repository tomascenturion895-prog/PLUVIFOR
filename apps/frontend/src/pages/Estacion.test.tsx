import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { Day, Series, StationList } from '../api/types'
import { FECHA_CORTE } from '../constants'
import Estacion from './Estacion'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getStations: vi.fn(),
  getRainfall: vi.fn(),
  getEstimates: vi.fn(),
  getEvents: vi.fn(),
  getClimateReference: vi.fn(),
}))
import {
  getClimateReference,
  getEstimates,
  getEvents,
  getRainfall,
  getStations,
} from '../api/client'

const ESTACIONES = {
  items: [
    { id: 1, code: '424', name: 'El Colorado' },
    { id: 2, code: '425', name: 'Bartolomé de las Casas' },
  ],
  total: 2,
  limit: 200,
  offset: 0,
} as unknown as StationList

function dia(obs_date: string, state: Day['state'], mm: number | null): Day {
  return { obs_date, state, mm, category: 'observado', source: 'siga_inta', flags: [] }
}

function serie(overrides: Partial<Series> = {}): Series {
  return {
    station_id: 1,
    station_name: 'El Colorado',
    source: {
      code: 'siga_inta',
      name: 'SIGA INTA',
      network: 'INTA',
      category: 'observado',
      day_cutoff_local: null,
    },
    category: 'observado',
    date_from: '2016-01-01',
    date_to: '2016-01-04',
    data_cutoff_date: FECHA_CORTE,
    clipped_to_cutoff: false,
    summary: {
      days_in_period: 4,
      days_with_data: 2,
      days_sin_fila: 1,
      days_fila_sin_valor: 1,
      coverage: 0.5,
      accumulated_mm: 0,
    },
    warnings: [],
    days: [
      dia('2016-01-01', 'dato', 0),
      dia('2016-01-02', 'dato', 0),
      dia('2016-01-03', 'sin_fila', null),
      dia('2016-01-04', 'fila_sin_valor', null),
    ],
    notice: '',
    ...overrides,
  }
}

function ir(ruta = '/estacion/1') {
  return render(
    <MemoryRouter initialEntries={[ruta]}>
      <Routes>
        <Route path="/estacion" element={<Estacion />} />
        <Route path="/estacion/:id" element={<Estacion />} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.mocked(getStations).mockResolvedValue(ESTACIONES)
  vi.mocked(getRainfall).mockReset()
  vi.mocked(getEstimates).mockReset()
  vi.mocked(getEvents).mockReset()
  vi.mocked(getEvents).mockResolvedValue({
    category: 'observado',
    date_from: '2016-01-01',
    date_to: '2016-01-31',
    min_dry_days: 7,
    stations: [],
    notice: '',
    description: '',
  })
  vi.mocked(getClimateReference).mockReset()
  vi.mocked(getClimateReference).mockResolvedValue({
    station_id: 1,
    station_name: 'x',
    category: 'referencia',
    normals: [],
    notice: '',
  })
  vi.mocked(getEstimates).mockResolvedValue({
    category: 'estimado',
    notice: 'Valores estimados, no medidos.',
    items: [],
    total: 0,
    limit: 200,
    offset: 0,
  })
})

describe('pantalla Estación', () => {
  it('sin estación elegida pide elegir una y no consulta la lluvia', async () => {
    ir('/estacion')
    expect(await screen.findByText('Elegí una estación para ver su lluvia.')).toBeInTheDocument()
    expect(getRainfall).not.toHaveBeenCalled()
  })

  it('muestra los días estimados aparte y no los suma al acumulado observado', async () => {
    vi.mocked(getRainfall).mockResolvedValue(
      serie({ summary: { ...serie().summary, accumulated_mm: 12.5 } }),
    )
    vi.mocked(getEstimates).mockResolvedValue({
      category: 'estimado',
      notice: 'Valores estimados, no medidos.',
      items: [
        {
          station_id: 1,
          obs_date: '2016-01-03',
          mm: 40,
          category: 'estimado',
          gap_state: 'sin_fila',
          method: 'vecinas_idw_v1',
          detail: {},
          created_at: '2026-11-19T15:00:00Z',
        },
      ],
      total: 1,
      limit: 200,
      offset: 0,
    })
    ir()
    expect(await screen.findByText('12,5 mm')).toBeInTheDocument() // el acumulado sigue siendo el observado
    expect(await screen.findByText('40 mm')).toBeInTheDocument()
    expect(screen.queryByText('52,5 mm')).not.toBeInTheDocument()
    expect(getEstimates).toHaveBeenCalledWith(
      expect.objectContaining({ stationId: 1 }),
      expect.any(AbortSignal),
    )
  })

  it('muestra acumulado, días con dato, fuente y categoría', async () => {
    vi.mocked(getRainfall).mockResolvedValue(
      serie({ summary: { ...serie().summary, accumulated_mm: 12.5 } }),
    )
    ir()
    expect(await screen.findByText('12,5 mm')).toBeInTheDocument()
    expect(screen.getByText('2 de 4')).toBeInTheDocument()
    expect(screen.getByText(/SIGA INTA \(INTA\)/)).toBeInTheDocument()
    expect(screen.getAllByText('Observado').length).toBeGreaterThan(0)
  })

  it('un período sin ningún día con dato muestra «sin dato», no 0 mm', async () => {
    vi.mocked(getRainfall).mockResolvedValue(
      serie({ summary: { ...serie().summary, days_with_data: 0, accumulated_mm: null } }),
    )
    ir()
    const caja = (await screen.findByText('Acumulado del período')).closest('div')!
    expect(within(caja).getByText('sin dato')).toBeInTheDocument()
    expect(within(caja).queryByText(/^0 mm$/)).not.toBeInTheDocument()
  })

  it('en la tabla los huecos son huecos y un cero real es 0 mm', async () => {
    vi.mocked(getRainfall).mockResolvedValue(serie())
    ir()
    const filas = await screen.findAllByRole('row')
    const texto = (fecha: string) => filas.find((f) => f.textContent?.includes(fecha))!.textContent
    expect(texto('2016-01-01')).toContain('0 mm')
    expect(texto('2016-01-03')).toContain('sin dato')
    expect(texto('2016-01-03')).not.toContain('0 mm')
    expect(texto('2016-01-04')).toContain('Fila sin valor')
    expect(texto('2016-01-04')).not.toContain('0 mm')
  })

  it('la estación 424 muestra la racha de ceros como advertencia', async () => {
    vi.mocked(getRainfall).mockResolvedValue(
      serie({
        warnings: [
          {
            code: 'ceros_prolongados',
            message: '281 días seguidos en 0 mm (2015-09-20 a 2016-06-26).',
            severity: 'alerta',
            start_date: '2015-09-20',
            end_date: '2016-06-26',
          },
        ],
      }),
    )
    ir()
    const seccion = (
      await screen.findByRole('heading', { name: 'Advertencias de calidad' })
    ).closest('section')!
    expect(within(seccion).getByText('Racha de ceros')).toBeInTheDocument()
    expect(
      within(seccion).getByText(/281 días seguidos en 0 mm/, { selector: 'p' }),
    ).toBeInTheDocument()
  })

  it('sin advertencias no muestra esa sección', async () => {
    vi.mocked(getRainfall).mockResolvedValue(serie())
    ir()
    await screen.findByText('Acumulado del período')
    expect(
      screen.queryByRole('heading', { name: 'Advertencias de calidad' }),
    ).not.toBeInTheDocument()
  })

  it('avisa si el período se recortó a la fecha de corte', async () => {
    vi.mocked(getRainfall).mockResolvedValue(serie({ clipped_to_cutoff: true }))
    ir()
    expect(await screen.findByText(/se recortó a la fecha de corte/)).toBeInTheDocument()
  })

  it('los selectores de fecha no pasan del corte 31/10/2026', async () => {
    vi.mocked(getRainfall).mockResolvedValue(serie())
    ir()
    await screen.findByText('Acumulado del período')
    expect(screen.getByLabelText('Desde')).toHaveAttribute('max', FECHA_CORTE)
    expect(screen.getByLabelText('Hasta')).toHaveAttribute('max', FECHA_CORTE)
  })

  it('un período invertido muestra un error y no consulta de nuevo', async () => {
    vi.mocked(getRainfall).mockResolvedValue(serie())
    ir()
    await screen.findByText('Acumulado del período')
    const desde = screen.getByLabelText('Desde')
    await userEvent.clear(desde)
    await userEvent.type(desde, '2026-10-31')
    await screen.findByText('Acumulado del período')
    vi.mocked(getRainfall).mockClear()
    const hasta = screen.getByLabelText('Hasta')
    await userEvent.clear(hasta)
    await userEvent.type(hasta, '2026-10-01')
    expect(await screen.findByText(/Elegí un período válido/)).toBeInTheDocument()
    expect(getRainfall).not.toHaveBeenCalled()
  })

  it('si la API falla muestra el mensaje en español y permite reintentar', async () => {
    vi.mocked(getRainfall)
      .mockRejectedValueOnce(new ApiError(404, 'not_found', 'La estación no existe.'))
      .mockResolvedValueOnce(serie())
    ir()
    expect(await screen.findByRole('alert')).toHaveTextContent('La estación no existe.')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    await waitFor(() => expect(screen.getByText('Acumulado del período')).toBeInTheDocument())
  })

  it('un id que no es un número se trata como sin estación elegida', async () => {
    ir('/estacion/abc')
    expect(await screen.findByText('Elegí una estación para ver su lluvia.')).toBeInTheDocument()
    expect(getRainfall).not.toHaveBeenCalled()
  })
})
