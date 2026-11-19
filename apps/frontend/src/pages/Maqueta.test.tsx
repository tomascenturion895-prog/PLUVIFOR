import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AccumulatedOut, NetworkHealth, StationList } from '../api/types'
import Maqueta from './Maqueta'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getStations: vi.fn(),
  getAccumulated: vi.fn(),
  getNetworkHealth: vi.fn(),
}))
import { getAccumulated, getNetworkHealth, getStations } from '../api/client'

const GEO = {
  type: 'FeatureCollection',
  features: ['Pirané', 'Bermejo'].map((nombre, i) => ({
    type: 'Feature',
    properties: { nombre },
    geometry: {
      type: 'Polygon',
      coordinates: [
        [
          [-60 + i, -25],
          [-59 + i, -25],
          [-59 + i, -26],
          [-60 + i, -26],
          [-60 + i, -25],
        ],
      ],
    },
  })),
}

const FUENTE = {
  code: 's',
  name: 'SIGA',
  network: 'INTA',
  category: 'observado',
  day_cutoff_local: '09:00',
}
const estacion = (
  id: number,
  name: string,
  department: string,
  lat: number | null,
  lon: number | null,
) => ({
  id,
  code: String(id),
  name,
  department,
  zone: null,
  lat,
  lon,
  source: FUENTE,
})

const CATALOGO = {
  items: [
    estacion(1, 'Uno', 'Pirané', -25.5, -59.5),
    estacion(2, 'Dos', 'Pirané', -25.6, -59.6),
    estacion(3, 'Tres', 'Bermejo', null, null),
  ],
  total: 3,
  limit: 200,
  offset: 0,
} as unknown as StationList

function acumulado(
  valores: Record<number, number | null>,
  extra: Partial<AccumulatedOut> = {},
): AccumulatedOut {
  return {
    category: 'observado',
    date_from: '2026-10-02',
    date_to: '2026-10-31',
    data_cutoff_date: '2026-10-31',
    clipped_to_cutoff: false,
    days_in_period: 30,
    stations: Object.entries(valores).map(([id, mm]) => ({
      station_id: Number(id),
      station_name: `E${id}`,
      accumulated_mm: mm,
      days_with_data: mm === null ? 0 : 20,
      days_without_data: mm === null ? 30 : 10,
      coverage: 0.5,
      warnings: [],
    })),
    not_evaluated: [],
    notice: 'PROTOTIPO',
    ...extra,
  }
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve(GEO) }))
  vi.mocked(getStations).mockResolvedValue(CATALOGO)
  vi.mocked(getAccumulated).mockResolvedValue(acumulado({ 1: 12, 2: 30, 3: null }))
  vi.mocked(getNetworkHealth).mockResolvedValue({ stations: [] } as unknown as NetworkHealth)
})
afterEach(() => {
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

describe('Maqueta', () => {
  it('cada departamento es un botón con texto alternativo', async () => {
    render(<Maqueta />)
    const pirane = await screen.findByRole('button', {
      name: /Pirané: mayor acumulado individual 30\.0 mm/,
    })
    expect(pirane).toHaveAttribute('tabindex', '0')
    expect(
      screen.getByRole('button', {
        name: /Bermejo: sin estaciones con dato|Bermejo: 1 estaciones, ninguna con dato/,
      }),
    ).toBeInTheDocument()
  })

  it('el departamento sin dato dice sin dato, no 0 mm', async () => {
    render(<Maqueta />)
    const b = await screen.findByRole('button', { name: /Bermejo/ })
    expect(b.getAttribute('aria-label')).toContain('sin dato')
    expect(b.getAttribute('aria-label')).not.toContain('0.0 mm')
  })

  it('al tocar un departamento se abre su detalle y se activa con teclado', async () => {
    const usuario = userEvent.setup()
    render(<Maqueta />)
    const pirane = await screen.findByRole('button', { name: /Pirané/ })
    pirane.focus()
    await usuario.keyboard('{Enter}')
    const detalle = await screen.findByRole('region', { name: 'Detalle de Pirané' })
    expect(within(detalle).getByText(/2 de 2 estaciones con dato/)).toBeInTheDocument()
    expect(pirane).toHaveAttribute('aria-pressed', 'true')
  })

  it('los resultados leen de la API y cambiar el período vuelve a pedir', async () => {
    const usuario = userEvent.setup()
    render(<Maqueta />)
    await screen.findByRole('table', { name: /Un acumulado por estación/ })
    vi.mocked(getAccumulated).mockResolvedValue(acumulado({ 1: 99, 2: 1, 3: null }))
    const desde = screen.getByLabelText('Desde')
    await usuario.clear(desde)
    await usuario.type(desde, '2026-10-20')
    await waitFor(() =>
      expect(getAccumulated).toHaveBeenLastCalledWith(
        expect.objectContaining({ from: '2026-10-20', to: '2026-10-31' }),
        expect.anything(),
      ),
    )
    expect(await screen.findByText('99 mm')).toBeInTheDocument()
  })

  it('los huecos se muestran como sin dato', async () => {
    render(<Maqueta />)
    const tabla = await screen.findByRole('table', { name: /Un acumulado por estación/ })
    const fila = within(tabla).getByRole('row', { name: /Tres/ })
    expect(fila).toHaveTextContent('sin dato')
    expect(fila).not.toHaveTextContent('0 mm')
  })

  it('un período inválido avisa y no pide a la API', async () => {
    const usuario = userEvent.setup()
    render(<Maqueta />)
    await screen.findByRole('table', { name: /Un acumulado por estación/ })
    vi.mocked(getAccumulated).mockClear()
    const hasta = screen.getByLabelText('Hasta')
    await usuario.clear(hasta)
    await usuario.type(hasta, '2000-01-01')
    expect(await screen.findByText(/Elegí un período válido/)).toBeInTheDocument()
    expect(getAccumulated).not.toHaveBeenCalled()
  })

  it('«Probá un cambio» muestra la diferencia y no compara si falta el dato', async () => {
    const usuario = userEvent.setup()
    render(<Maqueta />)
    await screen.findByRole('table', { name: /Un acumulado por estación/ })
    vi.mocked(getAccumulated).mockResolvedValue(acumulado({ 1: 20, 2: 30, 3: 5 }))
    await usuario.click(screen.getByRole('button', { name: 'Período anterior' }))
    const tabla = await screen.findByRole('table', { name: /Con el cambio/ })
    expect(within(tabla).getByRole('row', { name: /E1|Uno/ })).toHaveTextContent('+8 mm')
    expect(within(tabla).getByRole('row', { name: /Tres/ })).toHaveTextContent('no comparable')
  })

  it('las estaciones sin coordenadas no se dibujan en la maqueta', async () => {
    const { container } = render(<Maqueta />)
    await screen.findByRole('button', { name: /Pirané/ })
    expect(container.querySelectorAll('.maqueta-pieza')).toHaveLength(2)
  })

  it('una estación en silencio se dibuja apagada, distinta de una con 0 mm', async () => {
    vi.mocked(getNetworkHealth).mockResolvedValue({
      stations: [
        { station_id: 1, state: 'en_silencio' },
        { station_id: 2, state: 'activa' },
      ],
    } as unknown as NetworkHealth)
    vi.mocked(getAccumulated).mockResolvedValue(acumulado({ 1: 0, 2: 0, 3: null }))
    const { container } = render(<Maqueta />)
    await screen.findByRole('button', { name: /Pirané/ })
    await waitFor(() =>
      expect(container.querySelector('.maqueta-pieza-en_silencio')).not.toBeNull(),
    )
    expect(container.querySelectorAll('.maqueta-pieza-con_dato')).toHaveLength(1)
  })

  it('si falla la carga muestra un error en español', async () => {
    vi.mocked(getStations).mockRejectedValue(new Error('x'))
    render(<Maqueta />)
    expect(await screen.findByRole('alert')).toBeInTheDocument()
  })
})
