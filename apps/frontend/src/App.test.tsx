import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'
import { LEYENDA_PROTOTIPO, SECCIONES } from './constants'

function ir(ruta: string) {
  return render(
    <MemoryRouter initialEntries={[ruta]}>
      <App />
    </MemoryRouter>,
  )
}

describe('App', () => {
  it('muestra el nombre del proyecto', () => {
    ir('/')
    expect(screen.getByRole('heading', { name: 'PLUVIFOR' })).toBeInTheDocument()
  })

  it.each([...SECCIONES.map((s) => s.ruta), '/estacion/3', '/no-existe'])(
    'muestra la leyenda obligatoria de prototipo en %s',
    (ruta) => {
      ir(ruta)
      expect(screen.getByText(LEYENDA_PROTOTIPO)).toBeInTheDocument()
    },
  )

  it('tiene un enlace de navegación por cada sección', () => {
    ir('/')
    const nav = screen.getByRole('navigation', { name: 'Secciones' })
    for (const seccion of SECCIONES) {
      expect(nav).toHaveTextContent(seccion.nombre)
    }
    expect(nav.querySelectorAll('a')).toHaveLength(SECCIONES.length)
  })

  it('pone un título de pestaña distinto en cada pantalla', () => {
    ir('/comparador')
    expect(document.title).toBe('Comparador · PLUVIFOR')
  })

  it('el botón de menú despliega las secciones y se cierra al elegir una', async () => {
    ir('/mapa')
    const boton = screen.getByRole('button', { name: /Menú/ })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    expect(boton).toHaveTextContent('Mapa')
    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    await userEvent.click(screen.getByRole('link', { name: 'Comparador' }))
    expect(screen.getByRole('button', { name: /Menú/ })).toHaveAttribute('aria-expanded', 'false')
  })

  it('marca la sección actual', () => {
    ir('/mapa')
    expect(screen.getByRole('link', { name: 'Mapa' })).toHaveAttribute('aria-current', 'page')
  })

  it('una dirección inexistente muestra «Página no encontrada»', () => {
    ir('/no-existe')
    expect(screen.getByRole('heading', { name: 'Página no encontrada' })).toBeInTheDocument()
  })
})
