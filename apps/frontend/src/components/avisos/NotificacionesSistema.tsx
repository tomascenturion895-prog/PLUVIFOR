import { useEffect, useRef, useState } from 'react'
import type { AlertMessage } from '../../api/types'
import { horaDe } from './avisos-datos'

/**
 * Notificaciones dentro del propio sistema: una campana con el contador y un aviso emergente
 * cuando llega una nueva. También son simuladas: viven en la bandeja de la demostración.
 */
export default function NotificacionesSistema({ mensajes }: { mensajes: AlertMessage[] }) {
  const [abierta, setAbierta] = useState(false)
  const [emergente, setEmergente] = useState<AlertMessage | null>(null)
  const vistos = useRef<number | null>(null)

  const ultimo = mensajes.length > 0 ? mensajes[mensajes.length - 1] : null
  useEffect(() => {
    if (!ultimo) return
    // La primera carga no es una novedad: solo avisa lo que llega después.
    if (vistos.current !== null && ultimo.id > vistos.current) {
      setEmergente(ultimo)
      const t = setTimeout(() => setEmergente(null), 6000)
      vistos.current = ultimo.id
      return () => clearTimeout(t)
    }
    vistos.current = ultimo.id
  }, [ultimo])

  return (
    <div className="campana">
      <button
        type="button"
        className="campana-boton"
        aria-expanded={abierta}
        aria-label={`Notificaciones del sistema: ${mensajes.length}`}
        onClick={() => setAbierta(!abierta)}
      >
        <span aria-hidden="true">🔔</span>
        {mensajes.length > 0 && <span className="campana-cuenta">{mensajes.length}</span>}
      </button>
      {abierta && (
        <ul className="campana-lista" aria-label="Notificaciones">
          {mensajes.length === 0 && <li className="nota">Sin notificaciones.</li>}
          {[...mensajes].reverse().map((m) => (
            <li key={m.id}>
              <time dateTime={m.created_at}>{horaDe(m.created_at)}</time> {m.body}
            </li>
          ))}
        </ul>
      )}
      {emergente && (
        <div className="emergente" role="status">
          <strong>Nuevo aviso (simulado)</strong>
          <p>{emergente.body}</p>
        </div>
      )}
    </div>
  )
}
