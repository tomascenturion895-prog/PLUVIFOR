import { describe, expect, it } from 'vitest'
import { aplicar, CLAVE_PREFERENCIAS, guardar, leer, porDefecto } from './a11y-datos'

function almacen(inicial: Record<string, string> = {}) {
  const datos = { ...inicial }
  return {
    datos,
    getItem: (k: string) => datos[k] ?? null,
    setItem: (k: string, v: string) => {
      datos[k] = v
    },
  }
}

describe('preferencias de accesibilidad', () => {
  it('guarda y vuelve a leer la elección', () => {
    const a = almacen()
    const prefs = { texto: 'grande', contraste: 'alto', movimiento: 'reducido' } as const
    expect(guardar(a, prefs)).toBe(true)
    expect(leer(a)).toEqual(prefs)
  })

  it('sin nada guardado usa el valor por defecto, y respeta lo que pide el sistema', () => {
    expect(leer(almacen()).movimiento).toBe('normal')
    expect(leer(almacen(), porDefecto(true)).movimiento).toBe('reducido')
  })

  it('ignora valores ajenos o rotos y no falla', () => {
    expect(leer(almacen({ [CLAVE_PREFERENCIAS]: '{no es json' }))).toEqual(porDefecto())
    expect(leer(almacen({ [CLAVE_PREFERENCIAS]: '42' }))).toEqual(porDefecto())
    expect(
      leer(almacen({ [CLAVE_PREFERENCIAS]: '{"texto":"gigante","contraste":"alto"}' })),
    ).toEqual({ ...porDefecto(), contraste: 'alto' })
  })

  it('si el navegador no permite guardar, no revienta y avisa', () => {
    const roto = {
      setItem: () => {
        throw new Error('cuota')
      },
    }
    expect(guardar(roto, porDefecto())).toBe(false)
    expect(guardar(null, porDefecto())).toBe(false)
    expect(leer(null)).toEqual(porDefecto())
  })

  it('aplica las preferencias como atributos de la raíz', () => {
    const raiz = document.createElement('html')
    aplicar(raiz, { texto: 'muy-grande', contraste: 'alto', movimiento: 'reducido' })
    expect(raiz.dataset).toMatchObject({
      texto: 'muy-grande',
      contraste: 'alto',
      movimiento: 'reducido',
    })
  })
})
