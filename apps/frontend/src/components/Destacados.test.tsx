import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { ClimateReferenceOut, EventsOut, EventsStation } from '../api/types'
import Destacados from './Destacados'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getEvents: vi.fn(),
  getClimateReference: vi.fn(),
}))
import { getClimateReference, getEvents } from '../api/client'

function estacion(extra: Partial<EventsStation> = {}): EventsStation {
  return {
    station_id: 1,
    station_name: 'El Colorado',
    summary: {} as EventsStation['summary'],
    days_50mm_or_more: [
      { obs_date: '2016-01-03', mm: 62.5 },
      { obs_date: '2016-01-20', mm: 110 },
    ],
    days_100mm_or_more: [{ obs_date: '2016-01-20', mm: 110 }],
    dry_streaks: [],
    longest_dry_streak: {
      start_date: '2016-02-01',
      end_date: '2016-02-09',
      days: 9,
      zero_run_warning: false,
    },
    warnings: [],
    ...extra,
  }
}

function eventos(e: EventsStation | null): EventsOut {
  return {
    category: 'observado',
    date_from: '2016-01-01',
    date_to: '2016-02-29',
    min_dry_days: 7,
    stations: e ? [e] : [],
    notice: '',
    description: '',
  }
}

const SIN_NORMAL: ClimateReferenceOut = {
  station_id: 1,
  station_name: 'El Colorado',
  category: 'referencia',
  normals: [],
  notice: 'Referencia climática: no es lluvia observada.',
}

afterEach(() => vi.clearAllMocks())

function ver(compacto = false) {
  return render(
    <Destacados stationId={1} desde="2016-01-01" hasta="2016-02-29" compacto={compacto} />,
  )
}

describe('Destacados del período', () => {
  it('cuenta los días de 50 y 100 mm y muestra la racha seca más larga', async () => {
    vi.mocked(getEvents).mockResolvedValue(eventos(estacion()))
    vi.mocked(getClimateReference).mockResolvedValue(SIN_NORMAL)
    ver()
    expect(await screen.findByText(/2 días/)).toBeInTheDocument() // 50 mm o más
    expect(screen.getByText(/1 día(?!s)/)).toBeInTheDocument() // 100 mm o más
    expect(screen.getByText(/9 días seguidos con dato y 0 mm/)).toBeInTheDocument()
    await userEvent.click(screen.getAllByText('Ver fechas')[0])
    expect(screen.getByText(/2016-01-03: 62,5 mm/)).toBeInTheDocument()
  })

  it('es descriptivo: dice que no es una alerta y que un día sin dato no es seco', async () => {
    vi.mocked(getEvents).mockResolvedValue(eventos(estacion()))
    vi.mocked(getClimateReference).mockResolvedValue(SIN_NORMAL)
    ver()
    expect(await screen.findByRole('note')).toHaveTextContent(/no es una alerta/)
    expect(screen.getByRole('note')).toHaveTextContent(/Un día sin dato no cuenta como seco/)
  })

  it('una racha sobre ceros prolongados lleva la advertencia y no se da por buena', async () => {
    vi.mocked(getEvents).mockResolvedValue(
      eventos(
        estacion({
          longest_dry_streak: {
            start_date: '2015-09-20',
            end_date: '2016-06-26',
            days: 281,
            zero_run_warning: true,
          },
        }),
      ),
    )
    vi.mocked(getClimateReference).mockResolvedValue(SIN_NORMAL)
    ver()
    expect(await screen.findByText(/281 días seguidos/)).toBeInTheDocument()
    expect(screen.getByText(/Racha de ceros/i)).toBeInTheDocument()
  })

  it('sin racha seca con dato lo dice, y sin eventos cuenta cero días', async () => {
    vi.mocked(getEvents).mockResolvedValue(
      eventos(
        estacion({ days_50mm_or_more: [], days_100mm_or_more: [], longest_dry_streak: null }),
      ),
    )
    vi.mocked(getClimateReference).mockResolvedValue(SIN_NORMAL)
    ver()
    expect(await screen.findByText(/ninguna con dato en el período/)).toBeInTheDocument()
    expect(screen.getAllByText(/0 días/)).toHaveLength(2)
  })

  it('sin normal cargada dice que falta la fuente y no inventa un valor', async () => {
    vi.mocked(getEvents).mockResolvedValue(eventos(estacion()))
    vi.mocked(getClimateReference).mockResolvedValue(SIN_NORMAL)
    ver()
    expect(await screen.findByText(/No hay normal mensual cargada/)).toBeInTheDocument()
    expect(screen.queryByText(/Normal mensual 1991/)).not.toBeInTheDocument()
  })

  it('con normal cargada la muestra como referencia, aparte', async () => {
    vi.mocked(getEvents).mockResolvedValue(eventos(estacion()))
    vi.mocked(getClimateReference).mockResolvedValue({
      ...SIN_NORMAL,
      normals: [
        { period: '1991-2020', source_note: 'SMN', months: [{ month: 1, normal_mm: 150.4 }] },
      ],
    })
    ver()
    expect(await screen.findByText(/Normal mensual 1991-2020/)).toBeInTheDocument()
    expect(screen.getByText('enero')).toBeInTheDocument()
    expect(screen.getByText('150,4 mm')).toBeInTheDocument()
    expect(screen.getByText('Referencia')).toBeInTheDocument()
  })

  it('en el mapa (compacto) no pide la normal mensual', async () => {
    vi.mocked(getEvents).mockResolvedValue(eventos(estacion()))
    ver(true)
    expect(await screen.findByText(/9 días seguidos/)).toBeInTheDocument()
    expect(getClimateReference).not.toHaveBeenCalled()
  })

  it('si falla la API muestra el error y permite reintentar', async () => {
    vi.mocked(getClimateReference).mockResolvedValue(SIN_NORMAL)
    vi.mocked(getEvents)
      .mockRejectedValueOnce(new ApiError(0, 'network', 'No se pudo conectar con el servidor.'))
      .mockResolvedValueOnce(eventos(estacion()))
    ver()
    expect(await screen.findByText('No se pudo conectar con el servidor.')).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /reintentar/i }))
    expect(await screen.findByText(/9 días seguidos/)).toBeInTheDocument()
  })

  it('sin estaciones en la respuesta dice que no hay datos del período', async () => {
    vi.mocked(getEvents).mockResolvedValue(eventos(null))
    vi.mocked(getClimateReference).mockResolvedValue(SIN_NORMAL)
    ver()
    expect(await screen.findByText(/Sin datos para este período/)).toBeInTheDocument()
  })
})
