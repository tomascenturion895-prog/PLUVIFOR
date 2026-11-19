import { render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import { ADVERTENCIAS } from '../components/insignias-datos'
import Help from './Help'
import Home from './Home'

const enRouter = (el: React.ReactElement) => render(<MemoryRouter>{el}</MemoryRouter>)

describe('Inicio', () => {
  it('muestra la pregunta y que un día sin dato no es 0 mm', () => {
    enRouter(<Home />)
    expect(
      screen.getByRole('heading', { name: '¿Cuánto llovió, dónde y en qué período?' }),
    ).toBeInTheDocument()
    expect(screen.getByText(/nunca como 0 mm/)).toBeInTheDocument()
  })

  it('tiene accesos rápidos a maqueta, mapa, comparador, parte y reporte', () => {
    enRouter(<Home />)
    const accesos = within(screen.getByRole('list', { name: 'Accesos rápidos' }))
    const destinos = accesos.getAllByRole('link').map((a) => a.getAttribute('href'))
    expect(destinos).toEqual(['/maqueta', '/mapa', '/comparador', '/parte', '/reporte'])
  })

  it('enlaza a la ayuda y avisa el corte de datos', () => {
    enRouter(<Home />)
    expect(screen.getByRole('link', { name: 'Ayuda' })).toHaveAttribute('href', '/ayuda')
    expect(screen.getByText(/31\/10\/2026/)).toBeInTheDocument()
  })
})

describe('Ayuda', () => {
  it('explica los tres estados de un día', () => {
    enRouter(<Help />)
    for (const texto of ['Dato', 'Sin dato', 'Fila sin valor']) {
      expect(screen.getAllByText(texto, { exact: false }).length).toBeGreaterThan(0)
    }
    expect(screen.getAllByText(/No significa que no haya llovido/).length).toBeGreaterThan(0)
  })

  it('explica observado, estimado y referencia sin mezclarlos', () => {
    enRouter(<Help />)
    expect(screen.getByRole('heading', { name: 'Categorías del dato' })).toBeInTheDocument()
    expect(
      screen.getAllByText(/Nunca se suma ni se promedia con lo observado/).length,
    ).toBeGreaterThan(0)
  })

  it('lista las 6 advertencias con su descripción', () => {
    enRouter(<Help />)
    const lista = document.querySelector('.ayuda-advertencias') as HTMLElement
    expect(lista.querySelectorAll('dt')).toHaveLength(6)
    for (const a of Object.values(ADVERTENCIAS)) {
      expect(within(lista).getByText(a.texto)).toBeInTheDocument()
      expect(within(lista).getByText(a.descripcion)).toBeInTheDocument()
    }
  })

  it('aclara que una estación en silencio no es 0 mm y que no se suman acumulados', () => {
    enRouter(<Help />)
    expect(screen.getByText(/nunca con el color de 0 mm/)).toBeInTheDocument()
    expect(screen.getByText(/no se suman/)).toBeInTheDocument()
  })
})
