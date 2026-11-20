import type { AlertMessage } from '../../api/types'
import { horaDe } from './avisos-datos'

const ETIQUETA: Record<AlertMessage['kind'], string> = {
  codigo: 'Código',
  bienvenida: 'Bienvenida',
  aviso: 'Aviso de lluvia',
}

/**
 * Cómo se vería el chat en el celular de la persona. Es una maqueta: el canal es simulado y
 * no se envía nada a WhatsApp. Se rotula así adentro del propio marco.
 */
export default function CelularWhatsApp({
  mensajes,
  destinatario,
}: {
  mensajes: AlertMessage[]
  destinatario: string
}) {
  return (
    <figure className="celular" aria-label="Vista simulada de WhatsApp">
      <div className="celular-marco">
        <div className="celular-cabecera">
          <span className="celular-avatar" aria-hidden="true">
            P
          </span>
          <div>
            <strong>PLUVIFOR · Avisos</strong>
            <small>para {destinatario}</small>
          </div>
        </div>
        <div
          className="celular-chat"
          role="log"
          aria-live="polite"
          aria-label="Mensajes de WhatsApp"
        >
          <p className="celular-simulado">SIMULACIÓN · no se envía nada a WhatsApp</p>
          {mensajes.length === 0 && (
            <p className="celular-vacio">Todavía no hay mensajes. Registrate para recibirlos.</p>
          )}
          {mensajes.map((m) => (
            <div
              key={m.id}
              className={`burbuja burbuja-${m.kind}`}
              data-nuevo={m.kind === 'aviso' ? 'true' : undefined}
            >
              <span className="burbuja-tipo">{ETIQUETA[m.kind]}</span>
              <p>{m.body}</p>
              <time dateTime={m.created_at}>{horaDe(m.created_at)} ✓✓</time>
            </div>
          ))}
        </div>
      </div>
      <figcaption className="nota">Así se vería en WhatsApp. Hoy es una simulación.</figcaption>
    </figure>
  )
}
