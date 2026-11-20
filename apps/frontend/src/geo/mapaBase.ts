/**
 * Mapa base del mapa provincial.
 *
 * Por defecto es «local»: el mapa se dibuja solo con los GeoJSON del repositorio
 * (public/geo), sin pedir nada a Internet, así la demo funciona con la conexión apagada.
 * Con VITE_MAPA_BASE=osm se suman las teselas de OpenStreetMap (requiere conexión).
 */
export type MapaBase = 'local' | 'osm'

/** Cualquier valor que no sea exactamente «osm» (sin importar mayúsculas) deja el mapa local. */
export function resolverMapaBase(valor: string | undefined): MapaBase {
  return valor?.trim().toLowerCase() === 'osm' ? 'osm' : 'local'
}

export const MAPA_BASE: MapaBase = resolverMapaBase(import.meta.env.VITE_MAPA_BASE)

export const TESELAS_OSM = {
  url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
  atribucion: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
} as const
