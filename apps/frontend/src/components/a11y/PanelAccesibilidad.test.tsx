import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import PanelAccesibilidad from './PanelAccesibilidad'
import { CLAVE_PREFERENCIAS } from './a11y-datos'

beforeEach(() => localStorage.clear())
afterEach(() => {
  for (const k of ['texto', 'contraste', 'movimiento']) delete document.documentElement.dataset[k]
})

describe('panel de accesibilidad', () => {
  it('empieza cerrado y se abre con el botón, que informa su estado', async () => {
    render(<PanelAccesibilidad />)
    const boton = screen.getByRole('button', { name: 'Accesibilidad' })
    expect(boton).toHaveAttribute('aria-expanded', 'false')
    expect(screen.queryByRole('group', { name: 'Contraste' })).not.toBeInTheDocument()
    await userEvent.click(boton)
    expect(boton).toHaveAttribute('aria-expanded', 'true')
    expect(screen.getByRole('group', { name: 'Contraste' })).toBeInTheDocument()
  })

  it('cambia texto, contraste y movimiento, lo aplica a la página y lo guarda', async () => {
    render(<PanelAccesibilidad />)
    await userEvent.click(screen.getByRole('button', { name: 'Accesibilidad' }))
    await userEvent.click(screen.getByRole('radio', { name: 'Muy grande' }))
    await userEvent.click(screen.getByRole('radio', { name: 'Alto contraste' }))
    await userEvent.click(screen.getByRole('radio', { name: 'Reducir movimiento' }))
    expect(document.documentElement.dataset).toMatchObject({
      texto: 'muy-grande',
      contraste: 'alto',
      movimiento: 'reducido',
    })
    expect(JSON.parse(localStorage.getItem(CLAVE_PREFERENCIAS) ?? '{}')).toEqual({
      texto: 'muy-grande',
      contraste: 'alto',
      movimiento: 'reducido',
    })
  })

  it('recupera la elección guardada al volver a cargar', () => {
    localStorage.setItem(
      CLAVE_PREFERENCIAS,
      JSON.stringify({ texto: 'grande', contraste: 'alto', movimiento: 'normal' }),
    )
    render(<PanelAccesibilidad />)
    expect(document.documentElement.dataset.contraste).toBe('alto')
    expect(document.documentElement.dataset.texto).toBe('grande')
  })

  it('se maneja solo con el teclado y Restablecer vuelve a lo normal', async () => {
    const u = userEvent.setup()
    render(<PanelAccesibilidad />)
    await u.tab()
    expect(screen.getByRole('button', { name: 'Accesibilidad' })).toHaveFocus()
    await u.keyboard('{Enter}')
    await u.tab() // primer radio del grupo de texto
    await u.keyboard('{ArrowDown}') // las flechas mueven la selección dentro del grupo
    expect(document.documentElement.dataset.texto).toBe('grande')
    await u.click(screen.getByRole('button', { name: 'Restablecer' }))
    expect(document.documentElement.dataset.texto).toBe('normal')
    expect(document.documentElement.dataset.contraste).toBe('normal')
  })
})
