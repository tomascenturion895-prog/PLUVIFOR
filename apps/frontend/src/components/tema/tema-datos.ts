/** Tema visual de la interfaz. Solo presentación: ningún dato ni regla del dato cambia. */

export type Tema = 'oscuro' | 'claro' | 'daltonico'

export const CLAVE_TEMA = 'pluvifor.tema'

/** El oscuro es el tema base: es la apariencia original de la interfaz. */
export const TEMA_POR_DEFECTO: Tema = 'oscuro'

export const TEMAS: readonly Tema[] = ['claro', 'oscuro', 'daltonico']

export const ETIQUETA_TEMA: Record<Tema, string> = {
  claro: 'Claro',
  oscuro: 'Oscuro',
  daltonico: 'Daltónico',
}

/** Símbolo decorativo (aria-hidden): el nombre del tema siempre va escrito. */
export const SIMBOLO_TEMA: Record<Tema, string> = {
  claro: '☀',
  oscuro: '☾',
  daltonico: '◑',
}

export const DESCRIPCION_TEMA: Record<Tema, string> = {
  claro: 'Fondo gris claro, de bajo brillo',
  oscuro: 'Tema original, fondo oscuro',
  daltonico: 'Azul y naranja, con íconos y subrayados además del color',
}

export function esTema(valor: unknown): valor is Tema {
  return typeof valor === 'string' && (TEMAS as readonly string[]).includes(valor)
}

export function almacenLocal(): Storage | null {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

/** Lee el tema guardado. Un valor ajeno, roto o ausente deja el tema por defecto. */
export function leerTema(almacen: Pick<Storage, 'getItem'> | null): Tema {
  try {
    const valor = almacen?.getItem(CLAVE_TEMA)
    return esTema(valor) ? valor : TEMA_POR_DEFECTO
  } catch {
    return TEMA_POR_DEFECTO
  }
}

/** Guarda la elección. Si el navegador no deja (modo privado, cuota), la elección rige igual. */
export function guardarTema(almacen: Pick<Storage, 'setItem'> | null, tema: Tema): boolean {
  try {
    almacen?.setItem(CLAVE_TEMA, tema)
    return almacen !== null
  } catch {
    return false
  }
}

/** El tema viaja como atributo de <html>; el CSS (temas.css) hace el resto. */
export function aplicarTema(raiz: HTMLElement, tema: Tema): void {
  raiz.dataset.tema = tema
}
