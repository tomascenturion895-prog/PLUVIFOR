import { describe, expect, it } from 'vitest'
import { traducir } from './usar-idioma'
import {
  aplicarIdioma,
  CLAVE_IDIOMA,
  esIdioma,
  guardarIdioma,
  IDIOMA_POR_DEFECTO,
  IDIOMAS,
  leerIdioma,
} from './idioma-datos'
import { es, type ClaveTraduccion } from './traducciones/es'

describe('idioma de la interfaz', () => {
  it('sin nada guardado, el idioma por defecto es español', () => {
    expect(IDIOMA_POR_DEFECTO).toBe('es')
    expect(leerIdioma({ getItem: () => null })).toBe('es')
    expect(leerIdioma(null)).toBe('es')
  })

  it('guarda y vuelve a leer los 5 idiomas válidos', () => {
    const memoria = new Map<string, string>()
    const almacen = {
      getItem: (k: string) => memoria.get(k) ?? null,
      setItem: (k: string, v: string) => void memoria.set(k, v),
    }
    for (const idioma of IDIOMAS) {
      expect(guardarIdioma(almacen, idioma)).toBe(true)
      expect(memoria.get(CLAVE_IDIOMA)).toBe(idioma)
      expect(leerIdioma(almacen)).toBe(idioma)
    }
  })

  it('un valor ajeno o un almacén roto dejan español por defecto', () => {
    expect(leerIdioma({ getItem: () => 'fr' })).toBe('es')
    expect(
      leerIdioma({
        getItem: () => {
          throw new Error('bloqueado')
        },
      }),
    ).toBe('es')
    expect(esIdioma(123)).toBe(false)
    expect(esIdioma(undefined)).toBe(false)
  })

  it('si no se puede guardar, lo avisa sin romper', () => {
    expect(guardarIdioma(null, 'en')).toBe(false)
    expect(
      guardarIdioma(
        {
          setItem: () => {
            throw new Error('cuota')
          },
        },
        'gn',
      ),
    ).toBe(false)
  })

  it('aplica el atributo lang y data-idioma en <html>', () => {
    const raiz = document.createElement('html')
    aplicarIdioma(raiz, 'wlv')
    expect(raiz.lang).toBe('wlv')
    expect(raiz.dataset.idioma).toBe('wlv')
  })

  it('todos los idiomas tienen todas las claves sin textos vacíos', () => {
    const claves = Object.keys(es) as ClaveTraduccion[]
    for (const idioma of IDIOMAS) {
      for (const clave of claves) {
        const valor = traducir(idioma, clave)
        expect(valor, `${idioma}.${clave}`).toBeTruthy()
      }
    }
  })
})
