import { useSyncExternalStore } from 'react'
import type { Tema } from './tema-datos'

/**
 * Colores de datos para el tema daltónico. En los otros temas rigen los de siempre (la escala de
 * lluvia, la exposición y el 3D no cambian). Escalas viridis y naranjas: más lluvia = más oscuro,
 * sin rojo ni verde como único contraste. «Sin dato» sigue siendo gris y rayado en todos los temas.
 */
export const DALTONICO = {
  // Escala de lluvia en mm: 0, <10, <30, <60, <100, ≥100 (viridis, apta para los tres tipos)
  mm: ['#fde725', '#7ad151', '#22a884', '#2a788e', '#414487', '#440154'],
  // Exposición baja / media / alta
  clase: { baja: '#fde725', media: '#21918c', alta: '#440154' },
  // Densidad hídrica baja / media / alta (escala naranja, distinta a la de lluvia)
  hidrica: { baja: '#fee6ce', media: '#fd8d3c', alta: '#a63603' },
  provincia: { trazo: '#e69f00', relleno: '#fff3d6' },
  departamento: '#e0e6ee',
  rioPerenne: '#56b4e9',
  rioIntermitente: '#9fd3f2',
  capa: { observado: '#e8eaee', referencia: '#cc79a7', estimado: '#f0e442' },
  silencio: '#e69f00',
  barras: '#56b4e9',
  // THREE (hex numéricos)
  tres: { rio: 0x0072b2, rioIntermitente: 0x56b4e9, grilla: 0x7a7f8a, grillaFina: 0x3a3f4a },
} as const

export function temaActual(): Tema {
  const t = typeof document === 'undefined' ? undefined : document.documentElement.dataset.tema
  return t === 'claro' || t === 'daltonico' ? t : 'oscuro'
}

export function esDaltonico(): boolean {
  return temaActual() === 'daltonico'
}

function suscribir(avisar: () => void) {
  const obs = new MutationObserver(avisar)
  obs.observe(document.documentElement, { attributes: true, attributeFilter: ['data-tema'] })
  return () => obs.disconnect()
}

/** Tema vigente; el componente se vuelve a dibujar cuando cambia. */
export function useTema(): Tema {
  return useSyncExternalStore(suscribir, temaActual, () => 'oscuro' as Tema)
}
