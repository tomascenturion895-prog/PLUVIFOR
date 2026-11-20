/** Idioma de la interfaz. Solo presentación: los datos y reglas de integridad no cambian. */

export type Idioma = 'es' | 'en' | 'gn' | 'wlv' | 'tob'

export const CLAVE_IDIOMA = 'pluvifor.idioma'

export const IDIOMA_POR_DEFECTO: Idioma = 'es'

export const IDIOMAS: readonly Idioma[] = ['es', 'en', 'gn', 'wlv', 'tob']

export const NOMBRE_IDIOMA: Record<Idioma, string> = {
  es: 'Español',
  en: 'English',
  gn: "Guaraní (Avañe'ẽ)",
  wlv: 'Wichí (Wichí Lhamtés)',
  tob: "Toba (Qom l'aqtaqa)",
}

export function esIdioma(valor: unknown): valor is Idioma {
  return typeof valor === 'string' && (IDIOMAS as readonly string[]).includes(valor)
}

export function almacenLocal(): Storage | null {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

/** Lee el idioma guardado. Un valor ajeno, roto o ausente deja español por defecto. */
export function leerIdioma(almacen: Pick<Storage, 'getItem'> | null): Idioma {
  try {
    const valor = almacen?.getItem(CLAVE_IDIOMA)
    return esIdioma(valor) ? valor : IDIOMA_POR_DEFECTO
  } catch {
    return IDIOMA_POR_DEFECTO
  }
}

/** Guarda la elección. Si el navegador no deja (modo privado, cuota), la elección rige igual. */
export function guardarIdioma(almacen: Pick<Storage, 'setItem'> | null, idioma: Idioma): boolean {
  try {
    almacen?.setItem(CLAVE_IDIOMA, idioma)
    return almacen !== null
  } catch {
    return false
  }
}

/** Actualiza el atributo lang y data-idioma en <html>. */
export function aplicarIdioma(raiz: HTMLElement, idioma: Idioma): void {
  raiz.lang = idioma
  raiz.dataset.idioma = idioma
}
