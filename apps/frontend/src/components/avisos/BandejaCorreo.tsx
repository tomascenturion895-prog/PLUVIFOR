import type { AlertMessage } from '../../api/types'
import { fechaHoraArgentina } from '../../pages/sensores-datos'

/**
 * Cómo se vería la bandeja de entrada de la persona. Maqueta: el correo es simulado y no se
 * envía nada a ninguna casilla real.
 */
export default function BandejaCorreo({
  mensajes,
  destinatario,
}: {
  mensajes: AlertMessage[]
  destinatario: string
}) {
  const ordenados = [...mensajes].reverse()
  return (
    <section className="correo" aria-labelledby="titulo-correo">
      <h4 id="titulo-correo">Correo · {destinatario}</h4>
      <p className="celular-simulado">SIMULACIÓN · no se envía ningún correo real</p>
      {ordenados.length === 0 ? (
        <p className="nota">Sin correos: no dejaste un correo al registrarte.</p>
      ) : (
        <ul className="correo-lista">
          {ordenados.map((m) => (
            <li key={m.id}>
              <details>
                <summary>
                  <strong>{m.subject ?? 'Sin asunto'}</strong>
                  <span className="nota">
                    de avisos@pluvifor.demo · {fechaHoraArgentina(m.created_at)}
                  </span>
                </summary>
                <p className="correo-cuerpo">{m.body}</p>
              </details>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
