import { useState, type FormEvent } from 'react'
import {
  ApiError,
  bajaAvisos,
  confirmarAvisos,
  enviarAviso,
  getBandejaAvisos,
  getStations,
  previsualizarAviso,
  suscribirseAvisos,
} from '../api/client'
import type { AlertOutboxList, AlertPreview, Station } from '../api/types'
import BandejaCorreo from '../components/avisos/BandejaCorreo'
import CelularWhatsApp from '../components/avisos/CelularWhatsApp'
import NotificacionesSistema from '../components/avisos/NotificacionesSistema'
import { useSesion } from '../auth/usar-sesion'
import { ErrorEstado } from '../components/Estados'
import { FECHA_CORTE } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { useInboxAvisos } from '../hooks/useInboxAvisos'
import { useIdioma } from '../i18n/usar-idioma'
import '../avisos.css'
import { fechaHoraArgentina } from './sensores-datos'

/** Día real de la serie del SIGA/INTA (estación 424): 138 mm el 10/04/2014. Sirve para la demo. */
const EJEMPLO = { codigoEstacion: '424', fecha: '2014-04-10' }

function mensajeDe(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Ocurrió un error inesperado.'
}

type Paso = 'pedir' | 'confirmar' | 'listo' | 'baja'

function PanelPersonal({ estaciones }: { estaciones: Station[] }) {
  // La clave solo vive en esta variable: no se guarda en el navegador ni viaja en la URL.
  const { esPersonal } = useSesion()
  const [clave, setClave] = useState('')
  const [estacion, setEstacion] = useState('')
  const [fecha, setFecha] = useState('')
  const [vista, setVista] = useState<AlertPreview | null>(null)
  const [enviados, setEnviados] = useState<number | null>(null)
  const [bandeja, setBandeja] = useState<AlertOutboxList | null>(null)
  const [error, setError] = useState<string | null>(null)

  const conPermiso = esPersonal || clave !== ''
  const listo = conPermiso && estacion !== '' && fecha !== ''

  function cargarEjemplo() {
    const real = estaciones.find((e) => e.code === EJEMPLO.codigoEstacion)
    if (real) setEstacion(String(real.id))
    setFecha(EJEMPLO.fecha)
    setVista(null)
    setEnviados(null)
  }

  async function ejecutar(accion: () => Promise<void>) {
    setError(null)
    try {
      await accion()
    } catch (e) {
      setError(mensajeDe(e))
    }
  }

  const params = () => ({ stationId: Number(estacion), date: fecha })
  const ver = (e: FormEvent) => {
    e.preventDefault()
    void ejecutar(async () => {
      setEnviados(null)
      setVista(await previsualizarAviso(clave, params()))
    })
  }
  const enviar = () =>
    void ejecutar(async () => {
      const r = await enviarAviso(clave, params())
      setVista(r.preview)
      setEnviados(r.queued)
    })
  const verBandeja = () =>
    void ejecutar(async () => {
      setBandeja(await getBandejaAvisos(clave))
    })

  return (
    <details className="panel-personal">
      <summary>Panel del personal (disparar un aviso de ejemplo)</summary>
      <p className="nota">
        Un revisor del equipo mira la vista previa y recién ahí confirma el envío. Solo se avisa un
        día <strong>observado</strong> con 50 mm o más; un día sin dato no avisa nada.
      </p>
      <form onSubmit={ver} aria-label="Disparar aviso">
        {!esPersonal && (
          <label>
            Clave de administración
            <input
              type="password"
              autoComplete="off"
              value={clave}
              onChange={(e) => setClave(e.target.value)}
            />
          </label>
        )}
        <label>
          Estación
          <select value={estacion} onChange={(e) => setEstacion(e.target.value)}>
            <option value="">Elegí una estación</option>
            {estaciones.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.code})
              </option>
            ))}
          </select>
        </label>
        <label>
          Día
          <input
            type="date"
            max={FECHA_CORTE}
            value={fecha}
            onChange={(e) => setFecha(e.target.value)}
          />
        </label>
        <div className="acciones">
          <button type="button" onClick={cargarEjemplo}>
            Usar el día de ejemplo (138 mm, estación 424)
          </button>
          <button type="submit" disabled={!listo}>
            Ver vista previa
          </button>
          <button type="button" disabled={!listo || !vista?.would_send} onClick={enviar}>
            Enviar aviso (simulado)
          </button>
        </div>
      </form>
      {error && <ErrorEstado mensaje={error} />}
      {vista && (
        <div role="status" className="vista-previa">
          {vista.would_send ? (
            <>
              <strong>
                Se avisaría: {vista.mm} mm el {vista.date}
              </strong>
              <p>{vista.message}</p>
            </>
          ) : (
            <p>
              No se avisa:{' '}
              {vista.reason === 'sin_dato'
                ? 'ese día no tiene dato (un día sin dato no es 0 mm).'
                : `llovió ${vista.mm} mm, menos que el umbral de 50 mm.`}
            </p>
          )}
          {enviados !== null && (
            <p>
              <strong>
                {enviados} {enviados === 1 ? 'persona recibió' : 'personas recibieron'} el aviso
              </strong>{' '}
              (simulado).
            </p>
          )}
        </div>
      )}
      <p>
        <button type="button" disabled={!conPermiso} onClick={verBandeja}>
          Ver todos los mensajes simulados
        </button>
      </p>
      {bandeja && (
        <div className="tabla-scroll" role="region" aria-label="Mensajes simulados" tabIndex={0}>
          <table className="tabla-dias">
            <caption className="nota">
              Últimos {bandeja.items.length} de {bandeja.total} mensajes (hora de Argentina)
            </caption>
            <thead>
              <tr>
                <th scope="col">Fecha y hora</th>
                <th scope="col">Canal</th>
                <th scope="col">Para</th>
                <th scope="col">Mensaje</th>
              </tr>
            </thead>
            <tbody>
              {bandeja.items.map((m) => (
                <tr key={m.id}>
                  <th scope="row">{fechaHoraArgentina(m.created_at)}</th>
                  <td>{m.channel}</td>
                  <td>{m.recipient ?? '—'}</td>
                  <td>{m.subject ? `${m.subject}: ${m.body}` : m.body}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </details>
  )
}

/** Avisos de lluvia por WhatsApp, correo y el propio sistema. Hoy los canales son simulados. */
export default function Avisos() {
  const { t } = useIdioma()
  const [telefono, setTelefono] = useState('')
  const [correo, setCorreo] = useState('')
  const [estacion, setEstacion] = useState('')
  const [codigo, setCodigo] = useState('')
  const [paso, setPaso] = useState<Paso>('pedir')
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [registrado, setRegistrado] = useState<string | null>(null)
  const [correoRegistrado, setCorreoRegistrado] = useState('')

  const estaciones = useAsync((signal) => getStations({ limit: 100 }, signal), [])
  const lista = estaciones.estado.tipo === 'listo' ? estaciones.estado.datos.items : []
  const inbox = useInboxAvisos(registrado)
  const mensajes = inbox.tipo === 'listo' ? inbox.mensajes : []
  const porCanal = (canal: string) => mensajes.filter((m) => m.channel === canal)

  async function ejecutar(accion: () => Promise<unknown>, siguiente: Paso) {
    setError(null)
    setOcupado(true)
    try {
      await accion()
      setPaso(siguiente)
      return true
    } catch (e) {
      setError(mensajeDe(e))
      return false
    } finally {
      setOcupado(false)
    }
  }

  const pedir = async (e: FormEvent) => {
    e.preventDefault()
    const ok = await ejecutar(
      () =>
        suscribirseAvisos(telefono, {
          email: correo.trim() || undefined,
          stationId: estacion ? Number(estacion) : undefined,
        }),
      'confirmar',
    )
    if (ok) {
      setRegistrado(telefono)
      setCorreoRegistrado(correo.trim())
    }
  }
  const confirmar = (e: FormEvent) => {
    e.preventDefault()
    void ejecutar(() => confirmarAvisos(telefono, codigo), 'listo')
  }
  const darseDeBaja = () => void ejecutar(() => bajaAvisos(telefono), 'baja')

  return (
    <section className="avisos">
      <h2>
        {t('nav.avisos')} {registrado && <NotificacionesSistema mensajes={porCanal('sistema')} />}
      </h2>
      <p className="nota" role="note">
        <strong>Demostración:</strong> los canales (WhatsApp, correo y notificaciones del sistema)
        son simulados y <strong>no se envía nada real</strong>. Los avisos son informativos, se
        arman solo con lluvia <strong>observada</strong> de 50 mm o más y no son una orden ni una
        recomendación de evacuar: ante dudas, consultá a Defensa Civil.
      </p>

      <div className="avisos-grilla">
        <div className="avisos-formulario">
          {paso === 'pedir' && (
            <form onSubmit={(e) => void pedir(e)} aria-label="Pedir avisos">
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
              <label>
                Correo (opcional: te mandamos también un correo)
                <input
                  type="email"
                  autoComplete="email"
                  value={correo}
                  onChange={(e) => setCorreo(e.target.value)}
                />
              </label>
              <label>
                Estación de interés (opcional)
                <select value={estacion} onChange={(e) => setEstacion(e.target.value)}>
                  <option value="">Todas las estaciones</option>
                  {lista.map((s) => (
                    <option key={s.id} value={s.id}>
                      {s.name} ({s.code})
                    </option>
                  ))}
                </select>
              </label>
              <p className="nota">
                Del teléfono se guarda solo un resumen y los últimos 4 dígitos; el correo, solo
                enmascarado. Podés darte de baja cuando quieras.
              </p>
              <button type="submit" disabled={ocupado}>
                Pedir código
              </button>
            </form>
          )}

          {paso === 'confirmar' && (
            <form onSubmit={confirmar} aria-label="Confirmar avisos">
              <p>
                Te mandamos un código de 6 dígitos por WhatsApp al {telefono}. Mirá el celular de la
                derecha y escribilo acá.
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
              Listo: {telefono} quedó suscripto. Cuando una estación registre 50 mm o más vas a
              recibir el aviso por WhatsApp
              {correoRegistrado ? ', por correo' : ''} y en el sistema (simulado).
            </p>
          )}
          {paso === 'baja' && <p role="status">Listo: {telefono} no recibirá más avisos.</p>}

          {error && <ErrorEstado mensaje={error} />}

          {(paso === 'confirmar' || paso === 'listo') && (
            <p>
              <button type="button" disabled={ocupado} onClick={darseDeBaja}>
                Darme de baja
              </button>
            </p>
          )}
        </div>

        {registrado && (
          <div className="avisos-vista">
            {inbox.tipo === 'apagado' && (
              <p className="nota" role="status">
                La vista de demostración está apagada en este servidor (<code>ALERTS_DEMO</code>).
                Con canales reales nadie ve los mensajes de otra persona; para la presentación,
                activala en el <code>.env</code>.
              </p>
            )}
            {inbox.tipo === 'error' && <ErrorEstado mensaje={inbox.mensaje} />}
            {inbox.tipo !== 'apagado' && (
              <>
                <CelularWhatsApp mensajes={porCanal('whatsapp')} destinatario={registrado} />
                {correoRegistrado !== '' && (
                  <BandejaCorreo mensajes={porCanal('email')} destinatario={correoRegistrado} />
                )}
              </>
            )}
          </div>
        )}
      </div>

      <PanelPersonal estaciones={lista} />
    </section>
  )
}
