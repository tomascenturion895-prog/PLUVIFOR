/** Helpers de presentación de lluvia para el Mapa. Separados para fast-refresh. */

/** Devuelve un color CSS según mm acumulados. null/undefined = sin dato. */
export function colorMm(mm: number | null | undefined): string {
  if (mm == null) return '#9e9e9e' // gris: sin dato (nunca confundir con 0)
  if (mm === 0) return '#e3f2fd' // azul muy claro: dato real de 0 mm
  if (mm < 10) return '#90caf9'
  if (mm < 30) return '#42a5f5'
  if (mm < 60) return '#1e88e5'
  if (mm < 100) return '#1565c0'
  return '#0d47a1'
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
