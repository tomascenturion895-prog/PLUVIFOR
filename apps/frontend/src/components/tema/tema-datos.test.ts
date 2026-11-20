import { describe, expect, it } from 'vitest'
import {
  aplicarTema,
  CLAVE_TEMA,
  esTema,
  guardarTema,
  leerTema,
  TEMA_POR_DEFECTO,
} from './tema-datos'

describe('tema visual', () => {
  it('sin nada guardado, el tema es el oscuro original', () => {
    expect(TEMA_POR_DEFECTO).toBe('oscuro')
    expect(leerTema({ getItem: () => null })).toBe('oscuro')
    expect(leerTema(null)).toBe('oscuro')
  })

  it('guarda y vuelve a leer cada tema válido', () => {
    const memoria = new Map<string, string>()
    const almacen = {
      getItem: (k: string) => memoria.get(k) ?? null,
      setItem: (k: string, v: string) => void memoria.set(k, v),
    }
    for (const tema of ['claro', 'oscuro', 'daltonico'] as const) {
      expect(guardarTema(almacen, tema)).toBe(true)
      expect(memoria.get(CLAVE_TEMA)).toBe(tema)
      expect(leerTema(almacen)).toBe(tema)
    }
  })

  it('un valor ajeno o un almacén roto dejan el tema por defecto', () => {
    expect(leerTema({ getItem: () => 'rosa' })).toBe('oscuro')
    expect(
      leerTema({
        getItem: () => {
          throw new Error('bloqueado')
        },
      }),
    ).toBe('oscuro')
    expect(esTema(42)).toBe(false)
    expect(esTema(undefined)).toBe(false)
  })

  it('si no se puede guardar, lo avisa sin romper', () => {
    expect(guardarTema(null, 'claro')).toBe(false)
    expect(
      guardarTema(
        {
          setItem: () => {
            throw new Error('cuota')
          },
        },
        'claro',
      ),
    ).toBe(false)
  })

  it('el tema se aplica como atributo de <html>', () => {
    const raiz = document.createElement('html')
    aplicarTema(raiz, 'daltonico')
    expect(raiz.dataset.tema).toBe('daltonico')
  })
})
