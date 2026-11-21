import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Series, StationList } from '../api/types'
import { aspectoDepartamento } from '../components/vista3d/provincia-aspecto'
import type { Departamento } from '../components/vista3d/exposicion-datos'
import Vista3D from './Vista3D'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getStations: vi.fn(),
  getRainfall: vi.fn(),
}))
import { getRainfall, getStations } from '../api/client'

const cuadro = (nombre: string, x0: number) => ({
  type: 'Feature',
  properties: { nombre },
  geometry: {
    type: 'Polygon',
    coordinates: [
      [
        [x0, -26],
        [x0 + 1, -26],
        [x0 + 1, -25],
        [x0, -25],
        [x0, -26],
      ],
    ],
  },
})
const DEPTOS = {
  type: 'FeatureCollection',
  features: [cuadro('Pirané', -60), cuadro('Patiño', -59)],
}
const RIOS = {
  type: 'FeatureCollection',
  features: [
    {
      type: 'Feature',
      properties: {},
      geometry: {
        type: 'LineString',
        coordinates: [
          [-58.9, -25.5],
          [-58.1, -25.5],
        ],
      },
    },
  ],
}

const FUENTE = {
  code: 's',
  name: 'SIGA',
  network: 'INTA',
  category: 'observado',
  day_cutoff_local: null,
}
const est = (id: number, name: string, lon: number) => ({
  id,
  code: String(id),
  name,
  department: null,
  lat: -25.5,
  lon,
  coords_status: 'verificada',
  active_from: '2013-01-01',
  active_to: '2023-01-01',
  source: FUENTE,
})
const CATALOGO = {
  items: [est(424, 'El Colorado - EEA', -59.5), est(425, 'Bartolomé de las Casas - EEA', -58.5)],
  total: 2,
  limit: 200,
  offset: 0,
} as unknown as StationList

function serie(id: number, mms: (number | null)[], codigos: string[] = []): Series {
  return {
    station_id: id,
    station_name: id === 424 ? 'El Colorado' : 'Bartolomé de las Casas',
    days: mms.map((mm, i) => ({
      obs_date: `2016-03-${String(i + 1).padStart(2, '0')}`,
      state: mm === null ? 'sin_fila' : 'dato',
      mm,
      category: 'observado',
      source: 's',
      flags: [],
    })),
    warnings: codigos.map((code) => ({ code, message: '', severity: 'aviso' })),
  } as unknown as Series
}

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: string) =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(url.includes('departamentos') ? DEPTOS : RIOS),
      }),
    ),
  )
  vi.mocked(getStations).mockResolvedValue(CATALOGO)
  vi.mocked(getRainfall).mockImplementation(({ stationId }) =>
    Promise.resolve(
      stationId === 424
        ? serie(424, [0, 0, 0], ['ceros_prolongados'])
        : serie(425, [null, 12, 115.4]),
    ),
  )
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

function mostrar(ruta = '/vista-3d') {
  return render(
    <MemoryRouter initialEntries={[ruta]}>
      <Vista3D />
    </MemoryRouter>,
  )
}

describe('Vista 3D', () => {
  it('sin WebGL avisa y la tabla muestra la exposición con el caso 424 descartado', async () => {
    mostrar()
    expect(await screen.findByText(/no puede dibujar 3D/)).toBeInTheDocument()
    const tabla = await screen.findByRole('table')
    await screen.findByText('Sin dato confiable')
    const patino = within(tabla).getByRole('row', { name: /Patiño/ })
    expect(within(patino).getAllByRole('cell')[0]).toHaveTextContent('Alta')
    const pirane = within(tabla).getByRole('row', { name: /Pirané/ })
    expect(within(pirane).getByText('Sin dato confiable')).toBeInTheDocument()
    expect(getRainfall).toHaveBeenCalledWith(
      expect.objectContaining({ from: '2015-09-01', to: '2016-06-30', category: 'observado' }),
      expect.anything(),
    )
  })

  it('el resumen concuerda en plural: «2 estaciones, 2 departamentos»', async () => {
    mostrar()
    expect(await screen.findByText(/2 estaciones, 2 departamentos\./)).toBeInTheDocument()
  })

  it('al elegir un departamento muestra por qué se descartó la estación', async () => {
    mostrar()
    const tabla = await screen.findByRole('table')
    await userEvent.click(within(tabla).getByRole('button', { name: 'Pirané' }))
    expect(await screen.findByText(/Descartada: racha de ceros/)).toBeInTheDocument()
    expect(screen.getByText(/asignado por la ubicación verificada/)).toBeInTheDocument()
  })

  it('si el mapa de departamentos no carga, lo dice', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({ ok: false, json: () => Promise.resolve({}) }),
    )
    mostrar()
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo cargar el mapa')
  })
})

describe('aspecto de un departamento', () => {
  const base: Departamento = {
    nombre: 'X',
    clave: 'x',
    hidrica: { kmCursos: 10, areaKm2: 100, densidad: 10, clase: 'media' },
    lecturas: [],
    estacionesSinSerie: 0,
    deducidas: [],
    pluvial: null,
    exposicion: null,
  }

  it('sin dato queda bajo y rayado, nunca con el color de «baja»', () => {
    expect(aspectoDepartamento(base, 'exposicion', 10)).toEqual({ alto: 4, color: null })
    expect(aspectoDepartamento({ ...base, exposicion: 'alta' }, 'exposicion', 10).color).toBe(
      '#e5482a',
    )
    expect(aspectoDepartamento(base, 'hidrica', 10).alto).toBeCloseTo(66)
  })
})
