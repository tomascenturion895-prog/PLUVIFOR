import { SECCIONES } from './constants'

/** Título de la pestaña del navegador para cada ruta: así se distingue cada pantalla. */
export function tituloDe(ruta: string): string {
  const seccion =
    ruta === '/'
      ? SECCIONES[0]
      : SECCIONES.find((s) => s.ruta !== '/' && (ruta === s.ruta || ruta.startsWith(`${s.ruta}/`)))
  return `${seccion ? seccion.nombre : 'Página no encontrada'} · PLUVIFOR`
}
