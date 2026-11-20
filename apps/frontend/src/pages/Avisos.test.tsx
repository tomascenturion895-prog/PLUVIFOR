import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { AlertInbox, AlertMessage } from '../api/types'
import Avisos from './Avisos'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  suscribirseAvisos: vi.fn(),
  confirmarAvisos: vi.fn(),
  bajaAvisos: vi.fn(),
  getInboxAvisos: vi.fn(),
  getStations: vi.fn(),
  previsualizarAviso: vi.fn(),
  enviarAviso: vi.fn(),
  getBandejaAvisos: vi.fn(),
}))
import {
  bajaAvisos,
  confirmarAvisos,
  enviarAviso,
  getBandejaAvisos,
  getInboxAvisos,
  getStations,
  previsualizarAviso,
  suscribirseAvisos,
} from '../api/client'

const AVISO = 'Canal simulado: los mensajes quedan registrados y no salen a nadie.'
const ok = (status: 'pendiente' | 'confirmada' | 'baja') => ({ status, notice: AVISO })

function mensaje(extra: Partial<AlertMessage>): AlertMessage {
  return {
    id: 1,
    subscription_id: 1,
    kind: 'codigo',
    channel: 'whatsapp',
    recipient: '…3456',
    subject: null,
    body: 'PLUVIFOR: tu código es 123456.',
    category: 'simulado',
    created_at: '2026-10-20T10:00:00Z',
    ...extra,
  }
}

function inbox(items: AlertMessage[]): AlertInbox {
  return { status: 'pendiente', items, notice: AVISO }
}

beforeEach(() => {
  vi.mocked(getStations).mockResolvedValue({
    items: [
      {
        id: 2,
        code: '424',
        name: 'El Colorado',
        internal_code: null,
        kind: null,
        locality: null,
        department: null,
        zone: null,
        lat: null,
        lon: null,
        elevation_m: null,
      },
    ] as never,
    total: 1,
    limit: 100,
    offset: 0,
  })
  vi.mocked(getInboxAvisos).mockResolvedValue(inbox([]))
})
afterEach(() => vi.clearAllMocks())

async function registrar(correo?: string) {
  await userEvent.type(screen.getByLabelText(/^Teléfono/), '+54 370 4123456')
  if (correo) await userEvent.type(screen.getByLabelText(/^Correo/), correo)
  await userEvent.click(screen.getByRole('button', { name: 'Pedir código' }))
}

describe('Avisos', () => {
  it('avisa desde el principio que los canales son simulados y que no ordena evacuar', () => {
    render(<Avisos />)
    expect(screen.getAllByRole('note')[0]).toHaveTextContent(/no se envía nada real/)
    expect(screen.getAllByRole('note')[0]).toHaveTextContent(/ni una recomendación de evacuar/)
  })

  it('al registrarse con correo manda el correo opcional y muestra el celular y el correo simulados', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(getInboxAvisos).mockResolvedValue(
      inbox([
        mensaje({}),
        mensaje({
          id: 2,
          kind: 'bienvenida',
          channel: 'email',
          recipient: 't****@correo.com',
          subject: 'PLUVIFOR · recibimos tu registro',
          body: 'Recibimos tu pedido.',
        }),
      ]),
    )
    render(<Avisos />)
    await registrar('tomas@correo.com')
    expect(suscribirseAvisos).toHaveBeenCalledWith('+54 370 4123456', {
      email: 'tomas@correo.com',
      stationId: undefined,
    })
    const celular = await screen.findByLabelText('Vista simulada de WhatsApp')
    expect(within(celular).getByText(/no se envía nada a WhatsApp/)).toBeInTheDocument()
    expect(within(celular).getByText(/tu código es 123456/)).toBeInTheDocument()
    const correo = screen.getByRole('region', { name: /Correo/ })
    expect(within(correo).getByText('PLUVIFOR · recibimos tu registro')).toBeInTheDocument()
    expect(within(correo).getByText(/no se envía ningún correo real/)).toBeInTheDocument()
  })

  it('sin correo no muestra la bandeja de correo', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    render(<Avisos />)
    await registrar()
    await screen.findByLabelText('Vista simulada de WhatsApp')
    expect(screen.queryByRole('region', { name: /Correo/ })).not.toBeInTheDocument()
  })

  it('confirma con el código y queda suscripto', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(confirmarAvisos).mockResolvedValue(ok('confirmada'))
    render(<Avisos />)
    await registrar()
    await userEvent.type(await screen.findByLabelText(/Código de confirmación/), '123456')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(confirmarAvisos).toHaveBeenCalledWith('+54 370 4123456', '123456')
    expect(await screen.findByText(/quedó suscripto/)).toBeInTheDocument()
  })

  it('un código incorrecto muestra el error y no confirma', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(confirmarAvisos).mockRejectedValue(
      new ApiError(422, 'invalid_code', 'El código es incorrecto o venció.'),
    )
    render(<Avisos />)
    await registrar()
    await userEvent.type(await screen.findByLabelText(/Código de confirmación/), '000000')
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar' }))
    expect(await screen.findByText(/El código es incorrecto o venció/)).toBeInTheDocument()
    expect(screen.queryByText(/quedó suscripto/)).not.toBeInTheDocument()
  })

  it('permite darse de baja', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(bajaAvisos).mockResolvedValue(ok('baja'))
    render(<Avisos />)
    await registrar()
    await userEvent.click(await screen.findByRole('button', { name: 'Darme de baja' }))
    expect(bajaAvisos).toHaveBeenCalledWith('+54 370 4123456')
    expect(await screen.findByText(/no recibirá más avisos/)).toBeInTheDocument()
  })

  it('si la demostración está apagada lo explica y no muestra mensajes ajenos', async () => {
    vi.mocked(suscribirseAvisos).mockResolvedValue(ok('pendiente'))
    vi.mocked(getInboxAvisos).mockRejectedValue(
      new ApiError(403, 'forbidden', 'La vista de demostración está apagada (ALERTS_DEMO).'),
    )
    render(<Avisos />)
    await registrar()
    expect(await screen.findByText(/está apagada en este servidor/)).toBeInTheDocument()
    expect(screen.queryByLabelText('Vista simulada de WhatsApp')).not.toBeInTheDocument()
  })
})

describe('Avisos · panel del personal', () => {
  async function abrirPanel() {
    render(<Avisos />)
    await userEvent.click(screen.getByText(/Panel del personal/))
    await userEvent.type(screen.getByLabelText(/Clave de administración/), 'secreta')
  }

  it('el día de ejemplo carga la estación 424 y la fecha real de 138 mm', async () => {
    await abrirPanel()
    await userEvent.click(await screen.findByRole('button', { name: /Usar el día de ejemplo/ }))
    expect(screen.getByLabelText('Día')).toHaveValue('2014-04-10')
    expect(await screen.findAllByRole('option', { name: /El Colorado \(424\)/ })).toHaveLength(2)
    expect(screen.getByLabelText('Estación')).toHaveValue('2')
  })

  it('muestra la vista previa y recién después deja enviar el aviso simulado', async () => {
    vi.mocked(previsualizarAviso).mockResolvedValue({
      station_id: 2,
      date: '2014-04-10',
      would_send: true,
      reason: 'enviar',
      level: 100,
      mm: 138,
      message: 'PLUVIFOR · aviso informativo: la estación El Colorado registró 138 mm.',
      category: 'observado',
    })
    vi.mocked(enviarAviso).mockResolvedValue({
      preview: {
        station_id: 2,
        date: '2014-04-10',
        would_send: true,
        reason: 'enviar',
        level: 100,
        mm: 138,
        message: 'PLUVIFOR · aviso informativo: la estación El Colorado registró 138 mm.',
        category: 'observado',
      },
      queued: 3,
      notice: AVISO,
    })
    await abrirPanel()
    const enviar = screen.getByRole('button', { name: 'Enviar aviso (simulado)' })
    expect(enviar).toBeDisabled()
    await userEvent.click(await screen.findByRole('button', { name: /Usar el día de ejemplo/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Ver vista previa' }))
    expect(previsualizarAviso).toHaveBeenCalledWith('secreta', { stationId: 2, date: '2014-04-10' })
    expect(await screen.findByText(/Se avisaría: 138 mm/)).toBeInTheDocument()
    await userEvent.click(enviar)
    expect(await screen.findByText(/3 personas recibieron el aviso/)).toBeInTheDocument()
  })

  it('un día sin dato no avisa y lo dice (no es 0 mm)', async () => {
    vi.mocked(previsualizarAviso).mockResolvedValue({
      station_id: 2,
      date: '2014-04-12',
      would_send: false,
      reason: 'sin_dato',
      level: null,
      mm: null,
      message: null,
      category: 'observado',
    })
    await abrirPanel()
    await userEvent.click(await screen.findByRole('button', { name: /Usar el día de ejemplo/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Ver vista previa' }))
    expect(
      await screen.findByText(/ese día no tiene dato \(un día sin dato no es 0 mm\)/),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Enviar aviso (simulado)' })).toBeDisabled()
  })

  it('una clave incorrecta muestra el error', async () => {
    vi.mocked(getBandejaAvisos).mockRejectedValue(
      new ApiError(401, 'unauthorized', 'Falta la clave de administración o es incorrecta.'),
    )
    await abrirPanel()
    await userEvent.click(screen.getByRole('button', { name: /Ver todos los mensajes/ }))
    expect(await screen.findByText(/clave de administración o es incorrecta/)).toBeInTheDocument()
  })
})
