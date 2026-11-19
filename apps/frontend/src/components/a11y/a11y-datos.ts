/** Preferencias de accesibilidad (SCRUM-100). Se guardan solo en este dispositivo. */

export type Texto = 'normal' | 'grande' | 'muy-grande'
export type Contraste = 'normal' | 'alto'
export type Movimiento = 'normal' | 'reducido'

export interface Preferencias {
  texto: Texto
  contraste: Contraste
  movimiento: Movimiento
}

export const CLAVE_PREFERENCIAS = 'pluvifor.a11y'

export const TEXTOS: readonly Texto[] = ['normal', 'grande', 'muy-grande']
export const CONTRASTES: readonly Contraste[] = ['normal', 'alto']
export const MOVIMIENTOS: readonly Movimiento[] = ['normal', 'reducido']

/** Sin elección guardada, se respeta lo que pide el sistema para el movimiento. */
export function porDefecto(sistemaPideMenosMovimiento = false): Preferencias {
  return {
    texto: 'normal',
    contraste: 'normal',
    movimiento: sistemaPideMenosMovimiento ? 'reducido' : 'normal',
  }
}

function elegir<T extends string>(valor: unknown, permitidos: readonly T[], base: T): T {
  return permitidos.includes(valor as T) ? (valor as T) : base
}

/** Lee lo guardado. Un valor ajeno o roto se ignora y queda el valor por defecto. */
export function leer(
  almacen: Pick<Storage, 'getItem'> | null,
  base: Preferencias = porDefecto(),
): Preferencias {
  try {
    const crudo = almacen?.getItem(CLAVE_PREFERENCIAS)
    if (!crudo) return base
    const dato: unknown = JSON.parse(crudo)
    if (typeof dato !== 'object' || dato === null) return base
    const o = dato as Record<string, unknown>
    return {
      texto: elegir(o.texto, TEXTOS, base.texto),
      contraste: elegir(o.contraste, CONTRASTES, base.contraste),
      movimiento: elegir(o.movimiento, MOVIMIENTOS, base.movimiento),
    }
  } catch {
    return base
  }
}

/** Guarda la elección. Si el navegador no deja (modo privado, cuota), la elección rige igual. */
export function guardar(almacen: Pick<Storage, 'setItem'> | null, prefs: Preferencias): boolean {
  try {
    almacen?.setItem(CLAVE_PREFERENCIAS, JSON.stringify(prefs))
    return almacen !== null
  } catch {
    return false
  }
}

/** Las preferencias viajan como atributos de <html>; el CSS hace el resto. */
export function aplicar(raiz: HTMLElement, prefs: Preferencias): void {
  raiz.dataset.texto = prefs.texto
  raiz.dataset.contraste = prefs.contraste
  raiz.dataset.movimiento = prefs.movimiento
}

export function almacenLocal(): Storage | null {
  try {
    return window.localStorage
  } catch {
    return null
  }
}
