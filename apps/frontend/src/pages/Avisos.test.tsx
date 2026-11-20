import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import Avisos from './Avisos'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  suscribirseAvisos: vi.fn(),
  confirmarAvisos: vi.fn(),
  bajaAvisos: vi.fn(),
  getBandejaAvisos: vi.fn(),
}))
import { bajaAvisos, confirmarAvisos, getBandejaAvisos, suscribirseAvisos } from '../api/client'

const AVISO = 'Canal simulado: los mensajes quedan registrados y no salen a nadie.'
const ok = (status: 'pendiente' | 'confirmada' | 'baja') => ({ status, notice: AVISO })

afterEach(() => vi.clearAllMocks())

describe('Avisos', () => {
  it('avisa desde el principio que el canal es simulado y que no ordena evacuar', () => {
    render(<Avisos />)
    expect(screen.getByRole('note')).toHaveTextContent(/no se envía ningún mensaje real/)
    expect(screen.getByRole('note')).toHaveTextContent(/ni una recomendación de evacuar/)
  })

  it('pide el código, lo confirma y queda suscripto', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(confirmarAvisos).mockResolvedValue(ok('confirmada'))
    render(<Avisos />)
    await userEvent.type(screen.getByLabelText(/Teléfono/), '+54 370 4123456')
    await userEvent.click(screen.getByRole('button', { name: 'Pedir código' }))
    expect(suscribirseAvisos).toHaveBeenCalledWith('+54 370 4123456')
    await userEvent.type(await screen.findByLabelText(/Código de confirmación/), '123456')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(confirmarAvisos).toHaveBeenCalledWith('+54 370 4123456', '123456')
    expect(await screen.findByRole('status')).toHaveTextContent(/quedó suscripto/)
  })

  it('un código incorrecto muestra el error y no confirma', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(confirmarAvisos).mockRejectedValue(
      new ApiError(422, 'invalid_code', 'El código es incorrecto o venció.'),
    )
    render(<Avisos />)
    await userEvent.type(screen.getByLabelText(/Teléfono/), '+543704123456')
    await userEvent.click(screen.getByRole('button', { name: 'Pedir código' }))
    await userEvent.type(await screen.findByLabelText(/Código de confirmación/), '000000')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(await screen.findByText(/El código es incorrecto o venció/)).toBeInTheDocument()
    expect(screen.queryByText(/quedó suscripto/)).not.toBeInTheDocument()
  })

  it('permite darse de baja', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(bajaAvisos).mockResolvedValue(ok('baja'))
    render(<Avisos />)
    await userEvent.type(screen.getByLabelText(/Teléfono/), '+543704123456')
    await userEvent.click(screen.getByRole('button', { name: 'Pedir código' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Darme de baja' }))
    expect(bajaAvisos).toHaveBeenCalledWith('+543704123456')
    expect(await screen.findByRole('status')).toHaveTextContent(/no recibirá más avisos/)
  })

  it('la bandeja pide la clave y rotula cada mensaje como simulado', async () => {
    vi.mocked(getBandejaAvisos).mockResolvedValue({
      items: [
        {
          id: 1,
          subscription_id: 1,
          kind: 'codigo',
          body: 'PLUVIFOR: tu código es 123456.',
          category: 'simulado',
          created_at: '2026-10-20T10:00:00Z',
        },
      ],
      total: 1,
      notice: AVISO,
    })
    render(<Avisos />)
    expect(screen.getByRole('button', { name: 'Ver mensajes' })).toBeDisabled()
    await userEvent.type(screen.getByLabelText(/Clave de administración/), 'secreta')
    await userEvent.click(screen.getByRole('button', { name: 'Ver mensajes' }))
    expect(getBandejaAvisos).toHaveBeenCalledWith('secreta')
    expect(await screen.findByText(/tu código es 123456/)).toBeInTheDocument()
    expect(screen.getByText('Simulado')).toBeInTheDocument()
  })

  it('una clave incorrecta muestra el error y no deja ver mensajes', async () => {
    vi.mocked(getBandejaAvisos).mockRejectedValue(
      new ApiError(401, 'unauthorized', 'Falta la clave de administración o es incorrecta.'),
    )
    render(<Avisos />)
    await userEvent.type(screen.getByLabelText(/Clave de administración/), 'mala')
    await userEvent.click(screen.getByRole('button', { name: 'Ver mensajes' }))
    expect(await screen.findByText(/clave de administración o es incorrecta/)).toBeInTheDocument()
    expect(screen.queryByRole('table')).not.toBeInTheDocument()
  })
})
