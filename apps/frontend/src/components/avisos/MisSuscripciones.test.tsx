import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../api/client'
import type { MiSuscripcion } from '../../api/types'
import MisSuscripciones from './MisSuscripciones'

vi.mock('../../api/client', async (original) => ({
  ...(await original<typeof import('../../api/client')>()),
  getMisSuscripciones: vi.fn(),
  getMisNotificaciones: vi.fn(),
  cambiarEstacionesSuscripcion: vi.fn(),
  bajaMiSuscripcion: vi.fn(),
}))
import {
  bajaMiSuscripcion,
  cambiarEstacionesSuscripcion,
  getMisNotificaciones,
  getMisSuscripciones,
} from '../../api/client'

const ESTACIONES = [
  { id: 1, code: '51', name: 'EMC' },
  { id: 2, code: '424', name: 'El Colorado' },
]

function suscripcion(extra: Partial<MiSuscripcion>): MiSuscripcion {
  return {
    id: 7,
    status: 'confirmada',
    phone_last4: '3456',
    email_masked: 't****@correo.com',
    stations: [{ id: 2, code: '424', name: 'El Colorado' }],
    created_at: '2026-11-20T10:00:00Z',
    confirmed_at: '2026-11-20T10:05:00Z',
    ...extra,
  }
}

function cargar(items: MiSuscripcion[]) {
  vi.mocked(getMisSuscripciones).mockResolvedValue({ items, total: items.length })
  vi.mocked(getMisNotificaciones).mockResolvedValue({
    items: [],
    notice: 'Canal simulado.',
  })
}

afterEach(() => vi.clearAllMocks())

describe('MisSuscripciones', () => {
  it('muestra cada suscripción con el teléfono enmascarado y sus estaciones', async () => {
    cargar([suscripcion({})])
    render(<MisSuscripciones estaciones={ESTACIONES} />)
    const lista = await screen.findByRole('list', { name: 'Mis suscripciones' })
    expect(within(lista).getByText('…3456')).toBeInTheDocument()
    expect(within(lista).getByText(/Activa/)).toBeInTheDocument()
    expect(within(lista).getByText(/Estaciones: El Colorado \(424\)/)).toBeInTheDocument()
    expect(within(lista).getByText(/t\*\*\*\*@correo.com/)).toBeInTheDocument()
  })

  it('una suscripción sin estaciones dice que recibe las de todas', async () => {
    cargar([suscripcion({ stations: [] })])
    render(<MisSuscripciones estaciones={ESTACIONES} />)
    expect(await screen.findByText(/Recibe los avisos de todas las estaciones/)).toBeInTheDocument()
  })

  it('sin suscripciones explica cómo crear una', async () => {
    cargar([])
    render(<MisSuscripciones estaciones={ESTACIONES} />)
    expect(await screen.findByText(/Todavía no tenés suscripciones/)).toBeInTheDocument()
  })

  it('cambia las estaciones y muestra el resultado', async () => {
    cargar([suscripcion({})])
    vi.mocked(cambiarEstacionesSuscripcion).mockResolvedValue(suscripcion({ stations: ESTACIONES }))
    render(<MisSuscripciones estaciones={ESTACIONES} />)
    await userEvent.click(await screen.findByText(/Cambiar estaciones o darme de baja/))
    await userEvent.click(screen.getByRole('checkbox', { name: /EMC \(51\)/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Guardar estaciones' }))
    expect(cambiarEstacionesSuscripcion).toHaveBeenCalledWith(7, [2, 1])
    expect(
      await screen.findByText(/Estaciones: EMC \(51\), El Colorado \(424\)/),
    ).toBeInTheDocument()
  })

  it('se da de baja sin pedir el teléfono', async () => {
    cargar([suscripcion({})])
    vi.mocked(bajaMiSuscripcion).mockResolvedValue(suscripcion({ status: 'baja' }))
    render(<MisSuscripciones estaciones={ESTACIONES} />)
    await userEvent.click(await screen.findByText(/Cambiar estaciones o darme de baja/))
    await userEvent.click(screen.getByRole('button', { name: 'Darme de baja' }))
    expect(bajaMiSuscripcion).toHaveBeenCalledWith(7)
    expect(await screen.findByText(/De baja/)).toBeInTheDocument()
    expect(screen.queryByText(/Cambiar estaciones o darme de baja/)).not.toBeInTheDocument()
  })

  it('si el cambio falla muestra el motivo y no cambia lo que se ve', async () => {
    cargar([suscripcion({})])
    vi.mocked(bajaMiSuscripcion).mockRejectedValue(
      new ApiError(404, 'subscription_not_found', 'No existe esa suscripción.'),
    )
    render(<MisSuscripciones estaciones={ESTACIONES} />)
    await userEvent.click(await screen.findByText(/Cambiar estaciones o darme de baja/))
    await userEvent.click(screen.getByRole('button', { name: 'Darme de baja' }))
    expect(await screen.findByText(/No existe esa suscripción/)).toBeInTheDocument()
    expect(screen.getByText(/Activa/)).toBeInTheDocument()
  })

  it('muestra las notificaciones del sistema si hay', async () => {
    cargar([suscripcion({})])
    vi.mocked(getMisNotificaciones).mockResolvedValue({
      notice: 'Canal simulado.',
      items: [
        {
          id: 1,
          subscription_id: 7,
          kind: 'aviso',
          channel: 'sistema',
          recipient: '…3456',
          subject: null,
          body: 'PLUVIFOR · aviso informativo: 138 mm.',
          category: 'simulado',
          created_at: '2026-10-20T10:00:00Z',
        },
      ],
    })
    render(<MisSuscripciones estaciones={ESTACIONES} />)
    expect(await screen.findByText(/Notificaciones del sistema \(1\)/)).toBeInTheDocument()
    expect(screen.getByText(/138 mm/)).toBeInTheDocument()
  })
})
