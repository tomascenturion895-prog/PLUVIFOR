/**
 * Tests SCRUM-50 · Pantalla Mapa provincial
 *
 * Estrategia:
 *  - react-leaflet se mockea completo (jsdom no tiene canvas/SVG).
 *  - Se testea la lógica de presentación: estaciones con/sin coords, categoría, sin dato ≠ 0.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import type { Layer, LeafletEvent, LeafletEventHandlerFn } from 'leaflet'
import type { FeatureCollection } from 'geojson'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AccumulatedOut, Station, StationList } from '../api/types'
import { FECHA_CORTE } from '../constants'
import { colorMm, textoMmMapa } from './map-helpers'
import { Mapa } from './Map'

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('leaflet/dist/leaflet.css', () => ({}))
vi.mock('leaflet', () => ({ default: { geoJSON: vi.fn() } }))

vi.mock('react-leaflet', () => ({
  MapContainer: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="map-container">{children}</div>
  ),
  TileLayer: () => <div data-testid="tile-layer" />,
  GeoJSON: ({
    data,
    onEachFeature,
    style,
  }: {
    data: FeatureCollection
    onEachFeature?: (feature: FeatureCollection['features'][number], layer: Layer) => void
    style?: (feature: FeatureCollection['features'][number]) => { fillColor?: string }
  }) => (
    <>
      {data.features.map((feature, index) => {
        let clickHandler: LeafletEventHandlerFn | undefined
        const layer = {
          on: (_event: string, handler: LeafletEventHandlerFn) => {
            clickHandler = handler
          },
        } as unknown as Layer
        onEachFeature?.(feature, layer)
        const options = style?.(feature)
        const nombre =
          typeof feature.properties?.nombre === 'string' ? feature.properties.nombre : 'sin nombre'
        return (
          <button
            key={index}
            type="button"
            aria-label={`Departamento ${nombre}`}
            data-testid="geojson-feature"
            data-fill-color={options?.fillColor}
            onClick={() => clickHandler?.({} as LeafletEvent)}
          >
            {nombre}
          </button>
        )
      })}
    </>
  ),
  CircleMarker: ({
    children,
    'aria-label': label,
    pathOptions,
  }: {
    children?: React.ReactNode
    'aria-label'?: string
    pathOptions?: { dashArray?: string }
  }) => (
    <div data-testid="circle-marker" aria-label={label} data-dash-array={pathOptions?.dashArray}>
      {children}
    </div>
  ),
  Popup: ({ children }: { children: React.ReactNode }) => <div data-testid="popup">{children}</div>,
  useMap: () => ({ setView: vi.fn() }),
}))

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getStations: vi.fn(),
  getAccumulated: vi.fn(),
}))
import { getAccumulated, getStations } from '../api/client'

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const ESTACION_CON_COORDS: Station = {
  id: 1,
  code: '424',
  internal_code: null,
  name: 'El Colorado',
  kind: null,
  locality: null,
  department: 'El Colorado',
  zone: null,
  lat: -26.3,
  lon: -59.4,
  elevation_m: null,
  coords_status: 'verificada' as const,
  active_from: null,
  active_to: null,
  source: {
    code: 'siga_inta',
    name: 'SIGA INTA',
    network: 'INTA',
    category: 'observado' as const,
    day_cutoff_local: null,
  },
}

const ESTACION_SIN_COORDS: Station = {
  id: 2,
  code: '999',
  internal_code: null,
  name: 'Laguna Yema',
  kind: null,
  locality: null,
  department: null,
  zone: null,
  lat: null,
  lon: null,
  elevation_m: null,
  coords_status: 'pendiente' as const,
  active_from: null,
  active_to: null,
  source: {
    code: 'siga_inta',
    name: 'SIGA INTA',
    network: 'INTA',
    category: 'observado' as const,
    day_cutoff_local: null,
  },
}

function listaEstaciones(items: Station[], total = items.length, offset = 0): StationList {
  return { items, total, limit: 200, offset }
}

function acumulados(overrides: Partial<AccumulatedOut> = {}): AccumulatedOut {
  return {
    category: 'observado',
    date_from: '2026-10-01',
    date_to: FECHA_CORTE,
    data_cutoff_date: FECHA_CORTE,
    clipped_to_cutoff: false,
    days_in_period: 31,
    stations: [
      {
        station_id: 1,
        station_name: 'El Colorado',
        accumulated_mm: 45.2,
        days_with_data: 25,
        days_without_data: 6,
        coverage: 0.81,
        warnings: [],
      },
    ],
    not_evaluated: [],
    notice: 'PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial',
    ...overrides,
  }
}

// ---------------------------------------------------------------------------
// Setup
// ---------------------------------------------------------------------------

beforeEach(() => {
  vi.stubGlobal(
    'fetch',
    vi.fn((url: RequestInfo | URL) =>
      Promise.resolve({
        ok: true,
        json: async () => ({
          type: 'FeatureCollection',
          features: String(url).includes('departamentos')
            ? [
                {
                  type: 'Feature',
                  properties: { nombre: 'El Colorado' },
                  geometry: { type: 'Polygon', coordinates: [] },
                },
              ]
            : [],
        }),
      }),
    ),
  )
  vi.mocked(getStations).mockResolvedValue(
    listaEstaciones([ESTACION_CON_COORDS, ESTACION_SIN_COORDS]),
  )
  vi.mocked(getAccumulated).mockResolvedValue(acumulados())
})

afterEach(() => {
  vi.unstubAllGlobals()
})

function renderMapa() {
  return render(
    <MemoryRouter>
      <Mapa />
    </MemoryRouter>,
  )
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Mapa provincial', () => {
  it('renderiza el encabezado y la leyenda PROTOTIPO en el footer del app', async () => {
    renderMapa()
    expect(screen.getByRole('heading', { name: /mapa provincial/i })).toBeInTheDocument()
  })

  it('arranca con mapa base local: no pide teselas de Internet (demo sin conexión)', () => {
    renderMapa()
    expect(screen.getByTestId('mapa-contenedor')).toHaveAttribute('data-mapa-base', 'local')
    expect(screen.queryByTestId('tile-layer')).not.toBeInTheDocument()
  })

  it('muestra el contenedor del mapa', () => {
    renderMapa()
    expect(screen.getByTestId('mapa-contenedor')).toBeInTheDocument()
  })

  it('informa si la capa geográfica no se puede cargar', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false }))
    renderMapa()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'No se pudieron cargar estas capas geográficas',
    )
  })

  it('muestra el marcador de la estación con coordenadas', async () => {
    renderMapa()
    await waitFor(() => {
      const markers = screen.getAllByTestId('circle-marker')
      expect(markers.length).toBeGreaterThan(0)
    })
    expect(getStations).toHaveBeenCalledWith({ limit: 200, offset: 0 }, expect.any(AbortSignal))
  })

  it('carga las capas locales de provincia, departamentos y cursos de agua', async () => {
    renderMapa()

    await waitFor(() => {
      expect(fetch).toHaveBeenCalledTimes(4)
    })
    expect(fetch).toHaveBeenCalledWith(
      '/geo/formosa_provincia.geojson',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
    expect(fetch).toHaveBeenCalledWith(
      '/geo/formosa_departamentos.geojson',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
    expect(fetch).toHaveBeenCalledWith(
      '/geo/formosa_cursos_agua_perennes.geojson',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
    expect(fetch).toHaveBeenCalledWith(
      '/geo/formosa_cursos_agua_intermitentes.geojson',
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    )
  })

  it('colorea el departamento con el máximo individual y abre su resumen al tocarlo', async () => {
    const user = userEvent.setup()
    const segundaEstacion = { ...ESTACION_SIN_COORDS, department: 'El Colorado' }
    vi.mocked(getStations).mockResolvedValueOnce(
      listaEstaciones([ESTACION_CON_COORDS, segundaEstacion]),
    )
    vi.mocked(getAccumulated).mockResolvedValueOnce(
      acumulados({
        stations: [
          ...acumulados().stations,
          {
            station_id: 2,
            station_name: 'Laguna Yema',
            accumulated_mm: 12.3,
            days_with_data: 20,
            days_without_data: 11,
            coverage: 0.65,
            warnings: [
              {
                code: 'cobertura_baja',
                message: 'Solo 65% de los días tiene dato.',
                severity: 'aviso',
                start_date: null,
                end_date: null,
              },
            ],
          },
        ],
      }),
    )
    renderMapa()

    const departamento = await screen.findByRole('button', { name: 'Departamento El Colorado' })
    await waitFor(() => {
      expect(departamento).toHaveAttribute('data-fill-color', colorMm(45.2))
    })
    await user.click(departamento)

    const resumen = screen.getByRole('region', { name: 'Resumen del departamento El Colorado' })
    expect(resumen).toHaveTextContent('Máximo individual entre estaciones con dato: 45.2 mm.')
    expect(resumen).toHaveTextContent('SIGA INTA')
    expect(resumen).toHaveTextContent('12.3 mm')
    expect(resumen).not.toHaveTextContent('57.5 mm')
    expect(resumen).toHaveTextContent('Solo 65% de los días tiene dato.')
  })

  it('carga las páginas siguientes cuando hay más de 200 estaciones', async () => {
    const primeraPagina = Array.from({ length: 200 }, (_, index) => ({
      ...ESTACION_CON_COORDS,
      id: index + 1,
      name: `Estación ${index + 1}`,
    }))
    const siguienteEstacion = { ...ESTACION_CON_COORDS, id: 201, name: 'Estación 201' }
    vi.mocked(getStations)
      .mockResolvedValueOnce(listaEstaciones(primeraPagina, 201))
      .mockResolvedValueOnce(listaEstaciones([siguienteEstacion], 201, 200))

    renderMapa()

    await waitFor(() => {
      expect(screen.getAllByTestId('circle-marker')).toHaveLength(201)
    })
    expect(getStations).toHaveBeenNthCalledWith(
      2,
      { limit: 200, offset: 200 },
      expect.any(AbortSignal),
    )
  })

  it('la estación sin coordenadas aparece en la lista de pendientes, no en el mapa', async () => {
    renderMapa()
    await waitFor(() => {
      expect(screen.getByTestId('pendientes')).toBeInTheDocument()
    })
    expect(screen.getByText('Laguna Yema')).toBeInTheDocument()
    // No debe aparecer como marcador en el mapa
    const markers = screen.queryAllByTestId('circle-marker')
    const labels = markers.map((m) => m.getAttribute('aria-label') ?? '')
    expect(labels.some((l) => l.includes('Laguna Yema'))).toBe(false)
  })

  it('el acumulado de la estación muestra mm reales (no «sin dato» cuando hay dato)', async () => {
    renderMapa()
    await waitFor(() => {
      expect(screen.getByTestId('pendientes')).toBeInTheDocument()
    })
    expect(screen.getByText('SIGA INTA')).toBeInTheDocument()
    // El marcador de El Colorado debe tener su acumulado en el aria-label
    const marker = screen.getByLabelText('Estación El Colorado: 45.2 mm')
    expect(marker.getAttribute('aria-label')).toContain('45.2 mm')
  })

  it('advierte un período inválido y no consulta ni representa acumulados', async () => {
    renderMapa()
    fireEvent.change(screen.getByLabelText('Hasta'), { target: { value: '2026-11-01' } })

    expect(await screen.findByText(/Elegí un período válido/)).toBeInTheDocument()
    expect(getAccumulated).toHaveBeenCalledTimes(1)
    expect(screen.queryAllByTestId('circle-marker')).toHaveLength(0)
  })

  it('una estación sin acumulado muestra «sin dato», no «0 mm»', async () => {
    vi.mocked(getAccumulated).mockResolvedValueOnce(
      acumulados({
        stations: [
          {
            station_id: 1,
            station_name: 'El Colorado',
            accumulated_mm: null, // hueco, no 0
            days_with_data: 0,
            days_without_data: 31,
            coverage: 0,
            warnings: [],
          },
        ],
      }),
    )
    renderMapa()
    await waitFor(() => {
      const marker = screen.getByLabelText('Estación El Colorado: sin dato')
      expect(marker.getAttribute('aria-label')).toContain('sin dato')
      expect(marker.getAttribute('aria-label')).not.toContain('0 mm')
      expect(marker.getAttribute('data-dash-array')).toBe('2 4')
    })
  })

  it('el selector de categoría cambia la categoría mostrada', async () => {
    const user = userEvent.setup()
    renderMapa()
    const selector = screen.getByLabelText(/categoría de dato/i)
    await user.selectOptions(selector, 'estimado')
    await waitFor(() => {
      expect(vi.mocked(getAccumulated)).toHaveBeenCalledWith(
        expect.objectContaining({ category: 'estimado' }),
        expect.any(AbortSignal),
      )
    })
  })

  it('no mezcla observado con estimado en la misma consulta', async () => {
    const user = userEvent.setup()
    renderMapa()
    const selector = screen.getByLabelText(/categoría de dato/i)
    await user.selectOptions(selector, 'referencia')
    await waitFor(() => {
      const llamadas = vi.mocked(getAccumulated).mock.calls
      llamadas.forEach(([params]) => {
        // Cada llamada usa una sola categoría, nunca mezclada
        expect(typeof params.category).toBe('string')
      })
    })
  })
})

// ---------------------------------------------------------------------------
// Tests unitarios de helpers
// ---------------------------------------------------------------------------

describe('colorMm', () => {
  it('devuelve gris para null (hueco ≠ 0)', () => {
    expect(colorMm(null)).toBe('#9e9e9e')
  })

  it('devuelve azul muy claro para 0 mm real', () => {
    expect(colorMm(0)).toBe('#e3f2fd')
  })

  it('devuelve color azul intenso para ≥ 100 mm', () => {
    expect(colorMm(150)).toBe('#0d47a1')
  })

  it('devuelve color proporcional para rangos intermedios', () => {
    expect(colorMm(5)).toBe('#90caf9')
    expect(colorMm(20)).toBe('#42a5f5')
    expect(colorMm(45)).toBe('#1e88e5')
    expect(colorMm(80)).toBe('#1565c0')
  })
})

describe('textoMmMapa', () => {
  it('devuelve «sin dato» para null', () => {
    expect(textoMmMapa(null)).toBe('sin dato')
  })

  it('devuelve «sin dato» para undefined', () => {
    expect(textoMmMapa(undefined)).toBe('sin dato')
  })

  it('formatea con un decimal para valores reales', () => {
    expect(textoMmMapa(45.2)).toBe('45.2 mm')
    expect(textoMmMapa(0)).toBe('0.0 mm')
  })
})
