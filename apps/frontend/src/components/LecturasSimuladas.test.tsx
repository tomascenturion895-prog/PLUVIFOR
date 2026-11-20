import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { SensorReading, SensorReadingList } from '../api/types'
import LecturasSimuladas from './LecturasSimuladas'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getSensorReadings: vi.fn(),
}))
import { getSensorReadings } from '../api/client'

function lectura(extra: Partial<SensorReading>): SensorReading {
  return {
    id: 1,
    device_id: 'SIM-001',
    read_at: '2026-10-20T10:00:00Z',
    mm: 12.5,
    lat: null,
    lon: null,
    category: 'simulado',
    source: 'sensor_simulado',
    created_at: '2026-11-19T15:00:00Z',
    ...extra,
  }
}

function lista(items: SensorReading[], total = items.length): SensorReadingList {
  return {
    items,
    total,
    notice:
      'Lecturas simuladas: no son datos de sensores reales ni se suman a las series de lluvia.',
  }
}

afterEach(() => vi.clearAllMocks())

describe('Sensores (simulados)', () => {
  it('rotula cada lectura como simulada y avisa que no son datos reales', async () => {
    vi.mocked(getSensorReadings).mockResolvedValue(
      lista(
        [
          lectura({ id: 1 }),
          lectura({ id: 2, device_id: 'SIM-002', mm: 0, read_at: '2026-10-20T11:00:00Z' }),
        ],
        16,
      ),
    )
    render(<LecturasSimuladas />)
    expect(await screen.findByText(/no son datos de sensores reales/i)).toBeInTheDocument()
    const filas = within(screen.getByRole('table')).getAllByRole('row').slice(1)
    expect(filas).toHaveLength(2)
    for (const fila of filas) {
      expect(within(fila).getByText('Simulado')).toBeInTheDocument()
    }
    expect(screen.getByText(/Últimas 2 de 16 lecturas/)).toBeInTheDocument()
    expect(screen.getByText('20/10/2026 07:00')).toBeInTheDocument()
    expect(screen.getByText('12,5 mm')).toBeInTheDocument()
    expect(screen.getByText('08:00', { exact: false })).toBeInTheDocument()
  })

  it('sin lecturas explica cómo generarlas y no inventa una tabla', async () => {
    vi.mocked(getSensorReadings).mockResolvedValue(lista([]))
    render(<LecturasSimuladas />)
    expect(await screen.findByText(/Todavía no llegó ninguna lectura/)).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })

  it('si falla, lo dice y permite reintentar; el aviso de simuladas sigue visible', async () => {
    vi.mocked(getSensorReadings)
      .mockRejectedValueOnce(new ApiError(500, 'internal', 'No se pudo cargar.'))
      .mockResolvedValueOnce(lista([lectura({})]))
    render(<LecturasSimuladas />)
    expect(await screen.findByText('No se pudo cargar.')).toBeInTheDocument()
    expect(screen.getByText(/no son datos de sensores reales/i)).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: /reintentar/i }))
    expect(await screen.findByRole('table')).toBeInTheDocument()
  })

  it('pide solo las últimas 10', async () => {
    vi.mocked(getSensorReadings).mockResolvedValue(lista([]))
    render(<LecturasSimuladas />)
    await screen.findByText(/Todavía no llegó/)
    expect(getSensorReadings).toHaveBeenCalledWith({ limit: 10 }, expect.any(AbortSignal))
  })
})
