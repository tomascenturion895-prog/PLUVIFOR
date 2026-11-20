import { createContext, useContext } from 'react'
import { IDIOMA_POR_DEFECTO, type Idioma } from './idioma-datos'
import { en } from './traducciones/en'
import { es, type ClaveTraduccion, type Diccionario } from './traducciones/es'
import { gn } from './traducciones/gn'
import { tob } from './traducciones/tob'
import { wlv } from './traducciones/wlv'

const DICCIONARIOS: Record<Idioma, Diccionario> = { es, en, gn, wlv, tob }

export interface ContextoIdiomaValor {
  idioma: Idioma
  cambiarIdioma: (nuevo: Idioma) => void
  t: (clave: ClaveTraduccion) => string
}

export function traducir(idioma: Idioma, clave: ClaveTraduccion): string {
  return DICCIONARIOS[idioma]?.[clave] ?? DICCIONARIOS.es[clave]
}

export const ContextoIdioma = createContext<ContextoIdiomaValor>({
  idioma: IDIOMA_POR_DEFECTO,
  cambiarIdioma: () => {},
  t: (clave) => traducir(IDIOMA_POR_DEFECTO, clave),
})

export function useIdioma(): ContextoIdiomaValor {
  return useContext(ContextoIdioma)
}
