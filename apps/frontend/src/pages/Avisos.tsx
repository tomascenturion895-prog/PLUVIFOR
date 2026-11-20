import { useState, type FormEvent } from 'react'
import {
  ApiError,
  bajaAvisos,
  confirmarAvisos,
  getBandejaAvisos,
  suscribirseAvisos,
} from '../api/client'
import type { AlertOutboxList } from '../api/types'
import { ErrorEstado } from '../components/Estados'
import { useIdioma } from '../i18n/usar-idioma'
import { fechaHoraArgentina } from './sensores-datos'

function mensajeDe(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Ocurrió un error inesperado.'
}

/** Avisos de lluvia por mensajería. Hoy el canal es simulado: no se envía nada a nadie. */
export default function Avisos() {
  const { t } = useIdioma()
  const [telefono, setTelefono] = useState('')
  const [codigo, setCodigo] = useState('')
  const [paso, setPaso] = useState<'pedir' | 'confirmar' | 'listo' | 'baja'>('pedir')
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  // La clave solo vive en esta variable: no se guarda en el navegador ni viaja en la URL.
  const [clave, setClave] = useState('')
  const [bandeja, setBandeja] = useState<AlertOutboxList | null>(null)
  const [errorBandeja, setErrorBandeja] = useState<string | null>(null)

  async function ejecutar(accion: () => Promise<unknown>, siguiente: typeof paso) {
    setError(null)
    setOcupado(true)
    try {
      await accion()
      setPaso(siguiente)
    } catch (e) {
      setError(mensajeDe(e))
    } finally {
      setOcupado(false)
    }
  }

  const pedir = (e: FormEvent) => {
    e.preventDefault()
    void ejecutar(() => suscribirseAvisos(telefono), 'confirmar')
  }
  const confirmar = (e: FormEvent) => {
    e.preventDefault()
    void ejecutar(() => confirmarAvisos(telefono, codigo), 'listo')
  }

  async function verBandeja(e: FormEvent) {
    e.preventDefault()
    setErrorBandeja(null)
    try {
      setBandeja(await getBandejaAvisos(clave))
    } catch (err) {
      setBandeja(null)
      setErrorBandeja(mensajeDe(err))
    }
  }

  return (
    <section>
      <h2>{t('nav.avisos')}</h2>
      <p className="nota" role="note">
        Canal simulado: por ahora <strong>no se envía ningún mensaje real</strong>. Los avisos son
        informativos, se arman solo con lluvia <strong>observada</strong> de 50 mm o más y no son
        una orden ni una recomendación de evacuar: ante dudas, consultá a Defensa Civil.
      </p>

      {paso === 'pedir' && (
        <form onSubmit={pedir} aria-label="Pedir avisos">
          <label>
            Teléfono (con código de país, por ejemplo +54 370 4123456)
            <input
              type="tel"
              inputMode="tel"
              autoComplete="tel"
              required
              value={telefono}
              onChange={(e) => setTelefono(e.target.value)}
            />
          </label>
          <p className="nota">
            Del teléfono se guarda solo un resumen y los últimos 4 dígitos. Podés darte de baja
            cuando quieras.
          </p>
          <button type="submit" disabled={ocupado}>
            Pedir código
          </button>
        </form>
      )}

      {paso === 'confirmar' && (
        <form onSubmit={confirmar} aria-label="Confirmar avisos">
          <p>
            Te «mandamos» un código de 6 dígitos al {telefono}. Como el canal es simulado, lo lee el
            personal en la bandeja de abajo.
          </p>
          <label>
            Código de confirmación
            <input
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              value={codigo}
              onChange={(e) => setCodigo(e.target.value)}
            />
          </label>
          <button type="submit" disabled={ocupado}>
            Confirmar
          </button>
        </form>
      )}

      {paso === 'listo' && (
        <p role="status">
          Listo: {telefono} quedó suscripto. Cuando haya un aviso lo vas a recibir (hoy, solo en la
          bandeja simulada).
        </p>
      )}
      {paso === 'baja' && <p role="status">Listo: {telefono} no recibirá más avisos.</p>}

      {error && <ErrorEstado mensaje={error} />}

      {(paso === 'confirmar' || paso === 'listo') && (
        <p>
          <button
            type="button"
            disabled={ocupado}
            onClick={() => void ejecutar(() => bajaAvisos(telefono), 'baja')}
          >
            Darme de baja
          </button>
        </p>
      )}

      <h3>Bandeja simulada (personal)</h3>
      <form onSubmit={verBandeja} aria-label="Bandeja simulada">
        <label>
          Clave de administración
          <input
            type="password"
            autoComplete="off"
            value={clave}
            onChange={(e) => setClave(e.target.value)}
          />
        </label>
        <button type="submit" disabled={clave === ''}>
          Ver mensajes
        </button>
      </form>
      {errorBandeja && <ErrorEstado mensaje={errorBandeja} />}
      {bandeja && (
        <>
          <p className="nota" role="note">
            {bandeja.notice}
          </p>
          {bandeja.items.length === 0 ? (
            <p>No hay mensajes todavía.</p>
          ) : (
            <div
              className="tabla-scroll"
              role="region"
              aria-label="Mensajes simulados"
              tabIndex={0}
            >
              <table className="tabla-dias">
                <caption className="nota">
                  Últimos {bandeja.items.length} de {bandeja.total} mensajes (hora de Argentina)
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Fecha y hora</th>
                    <th scope="col">Tipo</th>
                    <th scope="col">Mensaje</th>
                    <th scope="col">Categoría</th>
                  </tr>
                </thead>
                <tbody>
                  {bandeja.items.map((m) => (
                    <tr key={m.id}>
                      <th scope="row">{fechaHoraArgentina(m.created_at)}</th>
                      <td>{m.kind === 'codigo' ? 'Código' : 'Aviso'}</td>
                      <td>{m.body}</td>
                      <td>Simulado</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  )
}
