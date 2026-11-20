import { useEffect, useState } from 'react'
import { ApiError, getInboxAvisos } from '../api/client'
import type { AlertMessage } from '../api/types'

export type EstadoInbox =
  | { tipo: 'inactivo' }
  | { tipo: 'listo'; mensajes: AlertMessage[] }
  | { tipo: 'apagado' } // ALERTS_DEMO desactivado en el servidor
  | { tipo: 'error'; mensaje: string }

/** Cada cuántos milisegundos se vuelve a mirar el celular simulado (para que los avisos «lleguen»). */
export const INTERVALO_INBOX_MS = 3000

/**
 * Mira cada pocos segundos los mensajes (simulados) de un teléfono, para que un aviso nuevo
 * aparezca en vivo. Se detiene al desmontar o cuando no hay teléfono.
 */
export function useInboxAvisos(phone: string | null): EstadoInbox {
  const [estado, setEstado] = useState<EstadoInbox>({ tipo: 'inactivo' })

  useEffect(() => {
    if (!phone) return
    const controller = new AbortController()
    let detenido = false
    const cargar = async () => {
      try {
        const inbox = await getInboxAvisos(phone, controller.signal)
        if (!controller.signal.aborted) setEstado({ tipo: 'listo', mensajes: inbox.items })
      } catch (e) {
        if (controller.signal.aborted) return
        if (e instanceof ApiError && e.status === 403) {
          detenido = true // la demostración está apagada: no tiene sentido seguir preguntando
          setEstado({ tipo: 'apagado' })
        } else {
          setEstado({
            tipo: 'error',
            mensaje: e instanceof ApiError ? e.message : 'Ocurrió un error inesperado.',
          })
        }
      }
    }
    void cargar()
    const timer = setInterval(() => {
      if (!detenido) void cargar()
    }, INTERVALO_INBOX_MS)
    return () => {
      controller.abort()
      clearInterval(timer)
    }
  }, [phone])

  return phone ? estado : { tipo: 'inactivo' }
}
