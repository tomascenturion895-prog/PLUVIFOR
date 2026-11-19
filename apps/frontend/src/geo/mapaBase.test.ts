import { describe, expect, it } from 'vitest'
import { MAPA_BASE, resolverMapaBase } from './mapaBase'

describe('resolverMapaBase', () => {
  it('es local cuando no hay variable', () => {
    expect(resolverMapaBase(undefined)).toBe('local')
    expect(resolverMapaBase('')).toBe('local')
  })

  it('usa OpenStreetMap solo si se pide «osm», sin importar mayúsculas ni espacios', () => {
    expect(resolverMapaBase('osm')).toBe('osm')
    expect(resolverMapaBase(' OSM ')).toBe('osm')
  })

  it('un valor inválido no activa Internet', () => {
    expect(resolverMapaBase('google')).toBe('local')
    expect(resolverMapaBase('http://tiles.example.com')).toBe('local')
  })

  it('la demo arranca con el mapa local', () => {
    expect(MAPA_BASE).toBe('local')
  })
})
