import { useState, type FormEvent } from 'react'
import { ApiError, cambiarCuenta, getCuentas } from '../api/client'
import type { Cuenta as CuentaDatos, Rol } from '../api/types'
import { useSesion } from '../auth/usar-sesion'
import { Cargando, ErrorEstado } from '../components/Estados'
import { useAsync } from '../hooks/useAsync'
import { useIdioma } from '../i18n/usar-idioma'

const TEXTO_ROL: Record<Rol, string> = {
  ciudadano: 'Ciudadano',
  operador: 'Operador',
  administrador: 'Administrador',
}

const DESCRIPCION_ROL: Record<Rol, string> = {
  ciudadano: 'Puede gestionar sus suscripciones a avisos.',
  operador: 'Puede cargar datos, reportes de campo y mandar avisos.',
  administrador: 'Además, gestiona las cuentas.',
}

function mensajeDe(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Ocurrió un error inesperado.'
}

function Formulario({ modo }: { modo: 'ingresar' | 'registrar' }) {
  const { ingresar, registrar } = useSesion()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [nombre, setNombre] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  async function enviar(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setOcupado(true)
    try {
      if (modo === 'ingresar') await ingresar(email, password)
      else await registrar({ email, password, display_name: nombre.trim() || undefined })
    } catch (err) {
      setError(mensajeDe(err))
    } finally {
      setOcupado(false)
    }
  }

  return (
    <form
      onSubmit={(e) => void enviar(e)}
      aria-label={modo === 'ingresar' ? 'Ingresar' : 'Crear cuenta'}
    >
      {modo === 'registrar' && (
        <label>
          Nombre (opcional)
          <input
            autoComplete="name"
            maxLength={80}
            value={nombre}
            onChange={(e) => setNombre(e.target.value)}
          />
        </label>
      )}
      <label>
        Correo
        <input
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
      </label>
      <label>
        Contraseña
        <input
          type="password"
          autoComplete={modo === 'ingresar' ? 'current-password' : 'new-password'}
          required
          minLength={modo === 'registrar' ? 10 : undefined}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </label>
      {modo === 'registrar' && (
        <p className="nota">
          Mínimo 10 caracteres. Tu cuenta nace como ciudadano; un administrador puede darte otro
          rol.
        </p>
      )}
      {error && <ErrorEstado mensaje={error} />}
      <button type="submit" disabled={ocupado}>
        {modo === 'ingresar' ? 'Ingresar' : 'Crear cuenta'}
      </button>
    </form>
  )
}

function FilaCuenta({
  cuenta,
  esYo,
  onCambio,
}: {
  cuenta: CuentaDatos
  esYo: boolean
  onCambio: (c: CuentaDatos) => void
}) {
  const [error, setError] = useState<string | null>(null)

  async function cambiar(cambio: { role?: Rol; is_active?: boolean }) {
    setError(null)
    try {
      onCambio(await cambiarCuenta(cuenta.id, cambio))
    } catch (e) {
      setError(mensajeDe(e))
    }
  }

  return (
    <tr>
      <th scope="row">
        {cuenta.display_name ?? cuenta.email}
        <span className="nota"> {cuenta.display_name ? cuenta.email : ''}</span>
      </th>
      <td>
        <select
          aria-label={`Rol de ${cuenta.email}`}
          value={cuenta.role}
          disabled={esYo}
          onChange={(e) => void cambiar({ role: e.target.value as Rol })}
        >
          {(Object.keys(TEXTO_ROL) as Rol[]).map((r) => (
            <option key={r} value={r}>
              {TEXTO_ROL[r]}
            </option>
          ))}
        </select>
      </td>
      <td>{cuenta.is_active ? 'Activa' : 'Desactivada'}</td>
      <td>
        {esYo ? (
          <span className="nota">Tu cuenta</span>
        ) : (
          <button type="button" onClick={() => void cambiar({ is_active: !cuenta.is_active })}>
            {cuenta.is_active ? 'Desactivar' : 'Activar'}
          </button>
        )}
        {error && <span role="alert"> {error}</span>}
      </td>
    </tr>
  )
}

function PanelCuentas({ yo }: { yo: number }) {
  const { estado, reintentar } = useAsync((signal) => getCuentas(signal), [])
  const [cambios, setCambios] = useState<Record<number, CuentaDatos>>({})

  return (
    <section aria-labelledby="titulo-cuentas">
      <h3 id="titulo-cuentas">Cuentas</h3>
      {estado.tipo === 'cargando' && <Cargando />}
      {estado.tipo === 'error' && (
        <ErrorEstado mensaje={estado.mensaje} onReintentar={reintentar} />
      )}
      {estado.tipo === 'listo' && (
        <div className="tabla-scroll" role="region" aria-label="Tabla de cuentas" tabIndex={0}>
          <table className="tabla-dias">
            <caption className="nota">
              {estado.datos.total} cuentas. Cambiar un rol cierra las sesiones de esa cuenta.
            </caption>
            <thead>
              <tr>
                <th scope="col">Cuenta</th>
                <th scope="col">Rol</th>
                <th scope="col">Estado</th>
                <th scope="col">Acciones</th>
              </tr>
            </thead>
            <tbody>
              {estado.datos.items.map((c) => (
                <FilaCuenta
                  key={c.id}
                  cuenta={cambios[c.id] ?? c}
                  esYo={c.id === yo}
                  onCambio={(nueva) => setCambios((a) => ({ ...a, [nueva.id]: nueva }))}
                />
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

/** Registro e inicio de sesión; con sesión, la cuenta y (para administradores) la gestión. */
export default function Cuenta() {
  const { t } = useIdioma()
  const { cuenta, verificando, esAdministrador, salir } = useSesion()
  const [modo, setModo] = useState<'ingresar' | 'registrar'>('ingresar')

  return (
    <section>
      <h2>{t('nav.cuenta')}</h2>
      {verificando && <Cargando />}
      {!verificando && !cuenta && (
        <>
          <p className="nota" role="note">
            Con una cuenta podés gestionar tus avisos de lluvia. El personal del equipo la usa para
            cargar datos, y queda registrado quién cargó qué.
          </p>
          <div role="group" aria-label="Elegir" className="acciones">
            <button
              type="button"
              aria-pressed={modo === 'ingresar'}
              onClick={() => setModo('ingresar')}
            >
              Ya tengo cuenta
            </button>
            <button
              type="button"
              aria-pressed={modo === 'registrar'}
              onClick={() => setModo('registrar')}
            >
              Crear una cuenta
            </button>
          </div>
          <Formulario key={modo} modo={modo} />
        </>
      )}
      {!verificando && cuenta && (
        <>
          <p role="status">
            Sesión iniciada como <strong>{cuenta.display_name ?? cuenta.email}</strong> (
            {cuenta.email}).
          </p>
          <p>
            Rol: <strong>{TEXTO_ROL[cuenta.role]}</strong>. {DESCRIPCION_ROL[cuenta.role]}
          </p>
          <p>
            <button type="button" onClick={() => void salir()}>
              Cerrar sesión
            </button>
          </p>
          {esAdministrador && <PanelCuentas yo={cuenta.id} />}
        </>
      )}
    </section>
  )
}
