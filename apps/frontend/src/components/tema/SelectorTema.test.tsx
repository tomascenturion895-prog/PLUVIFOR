import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import SelectorTema from './SelectorTema'
import { CLAVE_TEMA } from './tema-datos'

beforeEach(() => localStorage.clear())
afterEach(() => delete document.documentElement.dataset.tema)

describe('selector de tema', () => {
  it('ofrece los tres temas y empieza en el oscuro', () => {
    render(<SelectorTema />)
    expect(screen.getByRole('group', { name: 'Tema de color' })).toBeInTheDocument()
    expect(screen.getByRole('radio', { name: /Claro/ })).not.toBeChecked()
    expect(screen.getByRole('radio', { name: /Oscuro/ })).toBeChecked()
    expect(screen.getByRole('radio', { name: /Daltónico/ })).not.toBeChecked()
    expect(document.documentElement.dataset.tema).toBe('oscuro')
  })

  it('cambia de tema, lo aplica a la página y lo guarda', async () => {
    render(<SelectorTema />)
    await userEvent.click(screen.getByRole('radio', { name: /Claro/ }))
    expect(document.documentElement.dataset.tema).toBe('claro')
    expect(localStorage.getItem(CLAVE_TEMA)).toBe('claro')
    await userEvent.click(screen.getByRole('radio', { name: /Daltónico/ }))
    expect(document.documentElement.dataset.tema).toBe('daltonico')
    expect(localStorage.getItem(CLAVE_TEMA)).toBe('daltonico')
  })

  it('recupera el tema guardado al recargar', () => {
    localStorage.setItem(CLAVE_TEMA, 'daltonico')
    render(<SelectorTema />)
    expect(screen.getByRole('radio', { name: /Daltónico/ })).toBeChecked()
    expect(document.documentElement.dataset.tema).toBe('daltonico')
  })

  it('un valor guardado inválido vuelve al tema oscuro', () => {
    localStorage.setItem(CLAVE_TEMA, 'rosa')
    render(<SelectorTema />)
    expect(screen.getByRole('radio', { name: /Oscuro/ })).toBeChecked()
  })
})
