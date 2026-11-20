import { createContext } from 'react'
import type { Cuenta } from '../api/types'

export const CLAVE_SESION = 'pluvifor.sesion'

/** Lee el token guardado. Si el navegador no deja (modo privado), simplemente no hay sesión. */
export function leerTokenGuardado(): string | null {
  try {
    return window.sessionStorage.getItem(CLAVE_SESION)
  } catch {
    return null
  }
}

export function guardarToken(token: string | null): void {
  try {
    if (token) window.sessionStorage.setItem(CLAVE_SESION, token)
    else window.sessionStorage.removeItem(CLAVE_SESION)
  } catch {
    // Sin almacenamiento la sesión dura lo que dure la pestaña abierta: no es un error.
  }
}

/** Operadores y administradores pueden cargar datos. Los ciudadanos solo gestionan sus avisos. */
export function esPersonalDe(cuenta: Cuenta | null): boolean {
  return cuenta?.role === 'operador' || cuenta?.role === 'administrador'
}

export interface ContextoSesion {
  cuenta: Cuenta | null
  /** true mientras se comprueba con el servidor un token que había quedado guardado. */
  verificando: boolean
  esPersonal: boolean
  esAdministrador: boolean
  ingresar: (email: string, password: string) => Promise<void>
  registrar: (datos: { email: string; password: string; display_name?: string }) => Promise<void>
  salir: () => Promise<void>
}

export const ContextoSesionValor = createContext<ContextoSesion>({
  cuenta: null,
  verificando: false,
  esPersonal: false,
  esAdministrador: false,
  ingresar: async () => {},
  registrar: async () => {},
  salir: async () => {},
})
