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
  it('muestra una tarjeta por dispositivo, simulada, y un 0 real como 0 mm', async () => {
    vi.mocked(getSensorDevices).mockResolvedValue({
      items: [dispositivo({}), dispositivo({ device_id: 'SIM-002', last_mm: 3, readings: 1 })],
      total: 2,
      notice: AVISO,
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
    })
    vi.mocked(getSensorReadings).mockResolvedValue({ items: [], total: 0, notice: AVISO })
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
    vi.mocked(getSensorDevices).mockResolvedValue({ items: [], total: 0, notice: AVISO })
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
