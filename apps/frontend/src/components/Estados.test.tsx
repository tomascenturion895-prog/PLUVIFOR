import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Cargando, ErrorEstado } from './Estados'

describe('estados reutilizables', () => {
  it('Cargando avisa con un estado accesible', () => {
    render(<Cargando />)
    expect(screen.getByRole('status')).toHaveTextContent('Cargando…')
  })

  it('ErrorEstado muestra el mensaje como alerta', () => {
    render(<ErrorEstado mensaje="No se pudo conectar con el servidor." />)
    expect(screen.getByRole('alert')).toHaveTextContent('No se pudo conectar con el servidor.')
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })

  it('ErrorEstado ofrece reintentar', async () => {
    const reintentar = vi.fn()
    render(<ErrorEstado mensaje="Falló" onReintentar={reintentar} />)
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(reintentar).toHaveBeenCalledOnce()
  })
})
