import { useCallback, useEffect, useState } from 'react'
import { ApiError } from '../api/client'

export type Estado<T> =
  { tipo: 'cargando' } | { tipo: 'error'; mensaje: string } | { tipo: 'listo'; datos: T }

/** Ejecuta una carga y expone sus tres estados. Cancela la carga si se desmonta o cambia. */
export function useAsync<T>(cargar: (signal: AbortSignal) => Promise<T>, deps: unknown[]) {
  const [estado, setEstado] = useState<Estado<T>>({ tipo: 'cargando' })
  const [intento, setIntento] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setEstado({ tipo: 'cargando' })
    cargar(controller.signal).then(
      (datos) => {
        if (!controller.signal.aborted) setEstado({ tipo: 'listo', datos })
      },
      (error: unknown) => {
        if (controller.signal.aborted) return
        const mensaje = error instanceof ApiError ? error.message : 'Ocurrió un error inesperado.'
        setEstado({ tipo: 'error', mensaje })
      },
    )
    return () => controller.abort()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, intento])

  const reintentar = useCallback(() => setIntento((n) => n + 1), [])
  return { estado, reintentar }
}
