import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'
import { almacenLocal, aplicarIdioma, guardarIdioma, leerIdioma, type Idioma } from './idioma-datos'
import type { ClaveTraduccion } from './traducciones/es'
import { ContextoIdioma, traducir } from './usar-idioma'

export function ProveedorIdioma({ children }: { children: ReactNode }) {
  const [idioma, setIdioma] = useState<Idioma>(() => leerIdioma(almacenLocal()))

  useEffect(() => {
    aplicarIdioma(document.documentElement, idioma)
  }, [idioma])

  const cambiarIdioma = useCallback((nuevo: Idioma) => {
    setIdioma(nuevo)
    guardarIdioma(almacenLocal(), nuevo)
  }, [])

  const t = useCallback((clave: ClaveTraduccion) => traducir(idioma, clave), [idioma])

  const valor = useMemo(() => ({ idioma, cambiarIdioma, t }), [idioma, cambiarIdioma, t])

  return <ContextoIdioma.Provider value={valor}>{children}</ContextoIdioma.Provider>
}
