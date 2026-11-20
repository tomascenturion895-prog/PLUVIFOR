import { useContext } from 'react'
import { ContextoSesionValor, type ContextoSesion } from './sesion-datos'

export function useSesion(): ContextoSesion {
  return useContext(ContextoSesionValor)
}
