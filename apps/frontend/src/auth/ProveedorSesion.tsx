import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  ApiError,
  cerrarSesionApi,
  fijarTokenSesion,
  getMiCuenta,
  iniciarSesion,
  registrarCuenta,
} from '../api/client'
import type { Cuenta } from '../api/types'
import {
  ContextoSesionValor,
  esPersonalDe,
  guardarToken,
  leerTokenGuardado,
  type ContextoSesion,
} from './sesion-datos'

/** Mantiene la cuenta de la sesión y el token. Si el servidor ya no lo reconoce, se descarta. */
export function ProveedorSesion({ children }: { children: ReactNode }) {
  const [cuenta, setCuenta] = useState<Cuenta | null>(null)
  const [verificando, setVerificando] = useState(() => leerTokenGuardado() !== null)

  useEffect(() => {
    const token = leerTokenGuardado()
    if (!token) return
    fijarTokenSesion(token)
    const controller = new AbortController()
    getMiCuenta(controller.signal)
      .then((c) => setCuenta(c))
      .catch((e: unknown) => {
        if (controller.signal.aborted) return
        // Vencida o revocada: se descarta. Un corte de red no cierra la sesión del navegador.
        if (e instanceof ApiError && e.status === 401) {
          fijarTokenSesion(null)
          guardarToken(null)
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setVerificando(false)
      })
    return () => controller.abort()
  }, [])

  const ingresar = useCallback(async (email: string, password: string) => {
    const sesion = await iniciarSesion(email, password)
    fijarTokenSesion(sesion.token)
    guardarToken(sesion.token)
    setCuenta(sesion.user)
  }, [])

  const registrar = useCallback(
    async (datos: { email: string; password: string; display_name?: string }) => {
      await registrarCuenta(datos)
      await ingresar(datos.email, datos.password)
    },
    [ingresar],
  )

  const salir = useCallback(async () => {
    try {
      await cerrarSesionApi()
    } finally {
      fijarTokenSesion(null)
      guardarToken(null)
      setCuenta(null)
    }
  }, [])

  const valor = useMemo<ContextoSesion>(
    () => ({
      cuenta,
      verificando,
      esPersonal: esPersonalDe(cuenta),
      esAdministrador: cuenta?.role === 'administrador',
      ingresar,
      registrar,
      salir,
    }),
    [cuenta, verificando, ingresar, registrar, salir],
  )

  return <ContextoSesionValor.Provider value={valor}>{children}</ContextoSesionValor.Provider>
}
