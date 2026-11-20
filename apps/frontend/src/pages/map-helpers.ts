import { DALTONICO, esDaltonico } from '../components/tema/tema-colores'

/** Helpers de presentación de lluvia para el Mapa. Separados para fast-refresh. */

/** Devuelve un color CSS según mm acumulados. null/undefined = sin dato. */
/**
 * Escala secuencial amarillo-verde-azul (ColorBrewer YlGnBu, Apache 2.0), apta para daltonismo:
 * más lluvia = más oscuro y más azul. El 0 mm real es el tono más claro; sin dato no usa esta escala.
 */
export function colorMm(mm: number | null | undefined): string {
  if (mm == null) return '#9e9e9e' // gris: sin dato (nunca confundir con 0)
  if (esDaltonico()) return colorMmDaltonico(mm)
  if (mm === 0) return '#ffffd9' // dato real de 0 mm
  if (mm < 10) return '#c7e9b4'
  if (mm < 30) return '#7fcdbb'
  if (mm < 60) return '#41b6c4'
  if (mm < 100) return '#1d91c0'
  return '#0c2c84'
}

export function radiusMm(mm: number | null | undefined): number {
  if (mm == null) return 7
  if (mm === 0) return 6
  if (mm < 10) return 7
  if (mm < 30) return 9
  if (mm < 60) return 11
  if (mm < 100) return 13
  return 15
}

/** Texto legible de mm. null/undefined = «sin dato» (nunca confundir con 0 mm). */
export function textoMmMapa(mm: number | null | undefined): string {
  if (mm == null) return 'sin dato'
  return `${mm.toFixed(1)} mm`
}

/** Tema daltónico: escala viridis, de más claro (0 mm) a más oscuro (≥ 100 mm). */
function colorMmDaltonico(mm: number): string {
  const e = DALTONICO.mm
  if (mm === 0) return e[0]
  if (mm < 10) return e[1]
  if (mm < 30) return e[2]
  if (mm < 60) return e[3]
  if (mm < 100) return e[4]
  return e[5]
}
