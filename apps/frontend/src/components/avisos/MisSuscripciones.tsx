import { useState } from 'react'
import {
  ApiError,
  bajaMiSuscripcion,
  cambiarEstacionesSuscripcion,
  getMisNotificaciones,
  getMisSuscripciones,
} from '../../api/client'
import type { EstacionRef, MiSuscripcion } from '../../api/types'
import { useAsync } from '../../hooks/useAsync'
import { fechaHoraArgentina } from '../../pages/sensores-datos'
import { Cargando, ErrorEstado } from '../Estados'
import SelectorEstaciones from './SelectorEstaciones'

const TEXTO_ESTADO: Record<MiSuscripcion['status'], string> = {
  pendiente: 'Pendiente de confirmar',
  confirmada: 'Activa',
  baja: 'De baja',
}

function mensajeDe(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Ocurrió un error inesperado.'
}

function Tarjeta({
  suscripcion,
  estaciones,
  onCambio,
}: {
  suscripcion: MiSuscripcion
  estaciones: EstacionRef[]
  onCambio: (s: MiSuscripcion) => void
}) {
  const [elegidas, setElegidas] = useState(suscripcion.stations.map((s) => s.id))
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  async function ejecutar(accion: () => Promise<MiSuscripcion>) {
    setError(null)
    setOcupado(true)
    try {
      onCambio(await accion())
    } catch (e) {
      setError(mensajeDe(e))
    } finally {
      setOcupado(false)
    }
  }

  const enBaja = suscripcion.status === 'baja'
  return (
    <li className="mi-suscripcion">
      <strong>…{suscripcion.phone_last4}</strong> · {TEXTO_ESTADO[suscripcion.status]}
      {suscripcion.email_masked && <span className="nota"> · {suscripcion.email_masked}</span>}
      <p className="nota">
        {suscripcion.stations.length === 0
          ? 'Recibe los avisos de todas las estaciones.'
          : `Estaciones: ${suscripcion.stations.map((s) => `${s.name} (${s.code})`).join(', ')}.`}
      </p>
      {!enBaja && (
        <details>
          <summary>Cambiar estaciones o darme de baja</summary>
          <SelectorEstaciones estaciones={estaciones} elegidas={elegidas} onCambio={setElegidas} />
          <div className="acciones">
            <button
              type="button"
              disabled={ocupado}
              onClick={() =>
                void ejecutar(() => cambiarEstacionesSuscripcion(suscripcion.id, elegidas))
              }
            >
              Guardar estaciones
            </button>
            <button
              type="button"
              disabled={ocupado}
              onClick={() => void ejecutar(() => bajaMiSuscripcion(suscripcion.id))}
            >
              Darme de baja
            </button>
          </div>
        </details>
      )}
      {error && <ErrorEstado mensaje={error} />}
    </li>
  )
}

/** Las suscripciones y notificaciones de la cuenta con sesión iniciada. */
export default function MisSuscripciones({ estaciones }: { estaciones: EstacionRef[] }) {
  const mias = useAsync((signal) => getMisSuscripciones(signal), [])
  const notas = useAsync((signal) => getMisNotificaciones(signal), [])
  const [cambios, setCambios] = useState<Record<number, MiSuscripcion>>({})

  return (
    <section className="mis-avisos" aria-labelledby="titulo-mis-avisos">
      <h3 id="titulo-mis-avisos">Mis avisos</h3>
      {mias.estado.tipo === 'cargando' && <Cargando />}
      {mias.estado.tipo === 'error' && (
        <ErrorEstado mensaje={mias.estado.mensaje} onReintentar={mias.reintentar} />
      )}
      {mias.estado.tipo === 'listo' &&
        (mias.estado.datos.items.length === 0 ? (
          <p className="nota">
            Todavía no tenés suscripciones. Pedí avisos con el formulario: quedan a nombre de tu
            cuenta y podés cambiarlas o darte de baja desde acá, sin necesitar el teléfono.
          </p>
        ) : (
          <ul className="lista-sensores" aria-label="Mis suscripciones">
            {mias.estado.datos.items.map((s) => (
              <Tarjeta
                key={s.id}
                suscripcion={cambios[s.id] ?? s}
                estaciones={estaciones}
                onCambio={(nueva) => setCambios((a) => ({ ...a, [nueva.id]: nueva }))}
              />
            ))}
          </ul>
        ))}
      {notas.estado.tipo === 'listo' && notas.estado.datos.items.length > 0 && (
        <details open>
          <summary>Notificaciones del sistema ({notas.estado.datos.items.length})</summary>
          <p className="nota" role="note">
            {notas.estado.datos.notice}
          </p>
          <ul className="notificaciones">
            {notas.estado.datos.items.map((m) => (
              <li key={m.id}>
                <time dateTime={m.created_at}>{fechaHoraArgentina(m.created_at)}</time> {m.body}
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  )
}
