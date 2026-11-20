import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { Cuenta as CuentaDatos } from '../api/types'
import { ProveedorSesion } from '../auth/ProveedorSesion'
import { CLAVE_SESION } from '../auth/sesion-datos'
import Cuenta from './Cuenta'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  iniciarSesion: vi.fn(),
  registrarCuenta: vi.fn(),
  getMiCuenta: vi.fn(),
  cerrarSesionApi: vi.fn(),
  getCuentas: vi.fn(),
  cambiarCuenta: vi.fn(),
}))
import {
  cambiarCuenta,
  cerrarSesionApi,
  getCuentas,
  getMiCuenta,
  iniciarSesion,
  registrarCuenta,
} from '../api/client'

function cuenta(extra: Partial<CuentaDatos>): CuentaDatos {
  return {
    id: 1,
    email: 'ana@correo.com',
    display_name: null,
    role: 'ciudadano',
    is_active: true,
    created_at: '2026-11-20T10:00:00Z',
    last_login_at: null,
    ...extra,
  }
}

function montar() {
  return render(
    <ProveedorSesion>
      <Cuenta />
    </ProveedorSesion>,
  )
}

beforeEach(() => window.sessionStorage.clear())
afterEach(() => vi.clearAllMocks())

describe('Cuenta', () => {
  it('sin sesión muestra el ingreso y explica para qué sirve la cuenta', () => {
    montar()
    expect(screen.getByRole('note')).toHaveTextContent(/gestionar tus avisos/)
    expect(screen.getByRole('form', { name: 'Ingresar' })).toBeInTheDocument()
  })

  it('inicia sesión, muestra el rol y guarda el token solo en la pestaña', async () => {
    vi.mocked(iniciarSesion).mockResolvedValue({
      token: 'tok-123',
      expires_at: '2026-11-21T00:00:00Z',
      user: cuenta({ display_name: 'Ana' }),
    })
    montar()
    await userEvent.type(screen.getByLabelText('Correo'), 'ana@correo.com')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'una-clave-larga-1')
    await userEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(iniciarSesion).toHaveBeenCalledWith('ana@correo.com', 'una-clave-larga-1')
    expect(await screen.findByRole('status')).toHaveTextContent(/Sesión iniciada como Ana/)
    expect(screen.getByText('Ciudadano')).toBeInTheDocument()
    expect(window.sessionStorage.getItem(CLAVE_SESION)).toBe('tok-123')
    // Un ciudadano no ve el panel de cuentas.
    expect(screen.queryByRole('heading', { name: 'Cuentas' })).not.toBeInTheDocument()
  })

  it('una clave incorrecta muestra el error sin decir cuál de los dos datos falló', async () => {
    vi.mocked(iniciarSesion).mockRejectedValue(
      new ApiError(401, 'invalid_credentials', 'Correo o contraseña incorrectos.'),
    )
    montar()
    await userEvent.type(screen.getByLabelText('Correo'), 'ana@correo.com')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'x'.repeat(12))
    await userEvent.click(screen.getByRole('button', { name: 'Ingresar' }))
    expect(await screen.findByText('Correo o contraseña incorrectos.')).toBeInTheDocument()
    expect(window.sessionStorage.getItem(CLAVE_SESION)).toBeNull()
  })

  it('al crear una cuenta no se puede elegir el rol y se ingresa enseguida', async () => {
    vi.mocked(registrarCuenta).mockResolvedValue(cuenta({}))
    vi.mocked(iniciarSesion).mockResolvedValue({
      token: 'tok-9',
      expires_at: '2026-11-21T00:00:00Z',
      user: cuenta({}),
    })
    montar()
    await userEvent.click(screen.getByRole('button', { name: 'Crear una cuenta' }))
    expect(screen.queryByLabelText(/rol/i)).not.toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Correo'), 'ana@correo.com')
    await userEvent.type(screen.getByLabelText('Contraseña'), 'una-clave-larga-1')
    await userEvent.click(screen.getByRole('button', { name: 'Crear cuenta' }))
    expect(registrarCuenta).toHaveBeenCalledWith({
      email: 'ana@correo.com',
      password: 'una-clave-larga-1',
      display_name: undefined,
    })
    expect(await screen.findByRole('status')).toHaveTextContent(/Sesión iniciada/)
  })

  it('recupera la sesión guardada al recargar y descarta un token que ya no sirve', async () => {
    window.sessionStorage.setItem(CLAVE_SESION, 'tok-viejo')
    vi.mocked(getMiCuenta).mockResolvedValue(cuenta({ display_name: 'Ana' }))
    const { unmount } = montar()
    expect(await screen.findByText(/Sesión iniciada como/)).toHaveTextContent(/Ana/)
    unmount()

    vi.mocked(getMiCuenta).mockRejectedValue(new ApiError(401, 'unauthorized', 'Vencida'))
    montar()
    await screen.findByRole('form', { name: 'Ingresar' })
    expect(window.sessionStorage.getItem(CLAVE_SESION)).toBeNull()
  })

  it('cerrar sesión borra el token', async () => {
    window.sessionStorage.setItem(CLAVE_SESION, 'tok')
    vi.mocked(getMiCuenta).mockResolvedValue(cuenta({}))
    vi.mocked(cerrarSesionApi).mockResolvedValue()
    montar()
    await userEvent.click(await screen.findByRole('button', { name: 'Cerrar sesión' }))
    expect(cerrarSesionApi).toHaveBeenCalled()
    expect(await screen.findByRole('form', { name: 'Ingresar' })).toBeInTheDocument()
    expect(window.sessionStorage.getItem(CLAVE_SESION)).toBeNull()
  })
})

describe('Cuenta · administración', () => {
  beforeEach(() => {
    window.sessionStorage.setItem(CLAVE_SESION, 'tok-admin')
    vi.mocked(getMiCuenta).mockResolvedValue(
      cuenta({ id: 1, email: 'root@correo.com', role: 'administrador' }),
    )
    vi.mocked(getCuentas).mockResolvedValue({
      total: 2,
      items: [
        cuenta({ id: 1, email: 'root@correo.com', role: 'administrador' }),
        cuenta({ id: 2, email: 'cris@correo.com' }),
      ],
    })
  })

  it('el administrador ve las cuentas y no puede cambiarse a sí mismo', async () => {
    montar()
    const tabla = await screen.findByRole('region', { name: 'Tabla de cuentas' })
    expect(within(tabla).getByLabelText('Rol de root@correo.com')).toBeDisabled()
    expect(within(tabla).getByText('Tu cuenta')).toBeInTheDocument()
    expect(within(tabla).getByLabelText('Rol de cris@correo.com')).toBeEnabled()
  })

  it('cambia el rol de otra cuenta', async () => {
    vi.mocked(cambiarCuenta).mockResolvedValue(
      cuenta({ id: 2, email: 'cris@correo.com', role: 'operador' }),
    )
    montar()
    const lista = await screen.findByLabelText('Rol de cris@correo.com')
    await userEvent.selectOptions(lista, 'operador')
    expect(cambiarCuenta).toHaveBeenCalledWith(2, { role: 'operador' })
    expect(await screen.findByDisplayValue('Operador')).toBeInTheDocument()
  })

  it('si el cambio falla muestra el motivo', async () => {
    vi.mocked(cambiarCuenta).mockRejectedValue(
      new ApiError(409, 'cannot_modify_self', 'No podés cambiar tu propio rol ni desactivarte.'),
    )
    montar()
    await userEvent.click(await screen.findByRole('button', { name: 'Desactivar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(/No podés cambiar tu propio rol/)
  })
})
