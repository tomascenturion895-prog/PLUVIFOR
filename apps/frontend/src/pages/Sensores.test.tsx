import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { SensorDevice, SensorReading } from '../api/types'
import Sensores from './Sensores'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getSensorDevices: vi.fn(),
  getSensorReadings: vi.fn(),
}))
import { getSensorDevices, getSensorReadings } from '../api/client'

const RESUMEN = {
  data_cutoff_date: '2026-10-31',
  silent_after_days: 30,
  active: 1,
  silent: 1,
}

const AVISO =
  'Lecturas simuladas: no son datos de sensores reales ni se suman a las series de lluvia.'

function dispositivo(extra: Partial<SensorDevice>): SensorDevice {
  return {
    device_id: 'SIM-001',
    readings: 2,
    first_read_at: '2026-10-20T10:00:00Z',
    last_read_at: '2026-10-22T10:00:00Z',
    last_mm: 0,
    category: 'simulado',
    state: 'activa',
    last_read_date: '2026-10-22',
    days_since_last: 9,
    ...extra,
  }
}

function lectura(id: number, read_at: string, mm: number, device_id = 'SIM-001'): SensorReading {
  return {
    id,
    device_id,
    read_at,
    mm,
    lat: null,
    lon: null,
    category: 'simulado',
    source: 'sensor_simulado',
    created_at: '2026-11-19T15:00:00Z',
  }
}

function montar() {
  return render(
    <MemoryRouter>
      <Sensores />
    </MemoryRouter>,
  )
}

afterEach(() => vi.clearAllMocks())

describe('Sensores (pantalla)', () => {
  it('marca en silencio al dispositivo sin lecturas recientes y no lo muestra como 0 mm', async () => {
    vi.mocked(getSensorDevices).mockResolvedValue({
      items: [
        dispositivo({ device_id: 'SIM-001' }),
        dispositivo({
          device_id: 'SIM-002',
          state: 'en_silencio',
          days_since_last: 41,
          last_read_date: '2026-09-20',
          last_mm: 7.5,
        }),
      ],
      total: 2,
      notice: AVISO,
      ...RESUMEN,
    })
    vi.mocked(getSensorReadings).mockResolvedValue({ items: [], total: 0, notice: AVISO })
    montar()
    const lista = within(await screen.findByRole('list', { name: 'Dispositivos' }))
    const silencio = lista.getByRole('button', { name: /SIM-002/ })
    expect(within(silencio).getByText('En silencio')).toBeInTheDocument()
    expect(within(silencio).getByText(/hace 41 días/)).toBeInTheDocument()
    expect(within(silencio).getByText(/7,5 mm/)).toBeInTheDocument()
    const resumen = within(screen.getByRole('list', { name: 'Resumen de dispositivos' }))
    expect(resumen.getByText(/activos/)).toBeInTheDocument()
    expect(resumen.getByText(/en silencio/)).toBeInTheDocument()
    expect(screen.getByText(/Un silencio no es 0 mm/)).toBeInTheDocument()
  })

  it('muestra una tarjeta por dispositivo, simulada, y un 0 real como 0 mm', async () => {
    vi.mocked(getSensorDevices).mockResolvedValue({
      items: [dispositivo({}), dispositivo({ device_id: 'SIM-002', last_mm: 3, readings: 1 })],
      total: 2,
      notice: AVISO,
      ...RESUMEN,
    })
    vi.mocked(getSensorReadings).mockImplementation(async ({ deviceId } = {}) => ({
      items: [lectura(1, '2026-10-22T10:00:00Z', 0, deviceId)],
      total: 1,
      notice: AVISO,
    }))
    montar()
    expect(await screen.findByText(/no son datos de sensores reales/i)).toBeInTheDocument()
    const lista = within(screen.getByRole('list', { name: 'Dispositivos' }))
    expect(lista.getAllByRole('button')).toHaveLength(2)
    expect(lista.getAllByText('Simulado')).toHaveLength(2)
    expect(lista.getByText(/22\/10\/2026 07:00 · 0 mm/)).toBeInTheDocument()
    expect(lista.getByText('1 lectura')).toBeInTheDocument()
  })

  it('al elegir otro dispositivo pide sus lecturas', async () => {
    vi.mocked(getSensorDevices).mockResolvedValue({
      items: [dispositivo({}), dispositivo({ device_id: 'SIM-002' })],
      total: 2,
      notice: AVISO,
      ...RESUMEN,
    })
    vi.mocked(getSensorReadings).mockResolvedValue({
      items: [],
      total: 0,
      notice: AVISO,
      ...RESUMEN,
    })
    montar()
    await userEvent.click(await screen.findByRole('button', { name: /SIM-002/ }))
    expect(getSensorReadings).toHaveBeenCalledWith(
      expect.objectContaining({ deviceId: 'SIM-002' }),
      expect.anything(),
    )
  })

  it('pagina las lecturas con Siguiente y Anterior', async () => {
    vi.mocked(getSensorDevices).mockResolvedValue({
      items: [dispositivo({ readings: 25 })],
      total: 1,
      notice: AVISO,
      ...RESUMEN,
    })
    vi.mocked(getSensorReadings).mockResolvedValue({
      items: [lectura(1, '2026-10-22T10:00:00Z', 5)],
      total: 25,
      notice: AVISO,
    })
    montar()
    const siguiente = await screen.findByRole('button', { name: 'Siguiente' })
    expect(screen.getByRole('button', { name: 'Anterior' })).toBeDisabled()
    await userEvent.click(siguiente)
    expect(getSensorReadings).toHaveBeenCalledWith(
      expect.objectContaining({ offset: 10, limit: 10 }),
      expect.anything(),
    )
  })

  it('sin dispositivos explica cómo generarlos y no inventa ninguno', async () => {
    vi.mocked(getSensorDevices).mockResolvedValue({
      items: [],
      total: 0,
      notice: AVISO,
      ...RESUMEN,
    })
    montar()
    expect(await screen.findByText(/Todavía no llegó ninguna lectura/)).toBeInTheDocument()
    expect(screen.queryByRole('list', { name: 'Dispositivos' })).not.toBeInTheDocument()
  })

  it('si la API falla, lo dice y permite reintentar', async () => {
    vi.mocked(getSensorDevices).mockRejectedValue(new ApiError(500, 'x', 'No se pudo cargar'))
    montar()
    expect(await screen.findByText(/No se pudo cargar/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reintentar/i })).toBeInTheDocument()
  })
})
