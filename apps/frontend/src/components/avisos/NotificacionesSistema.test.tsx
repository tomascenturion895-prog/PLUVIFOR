import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import type { AlertMessage } from '../../api/types'
import NotificacionesSistema from './NotificacionesSistema'

function nota(id: number, body: string): AlertMessage {
  return {
    id,
    subscription_id: 1,
    kind: 'aviso',
    channel: 'sistema',
    recipient: '…3456',
    subject: null,
    body,
    category: 'simulado',
    created_at: '2026-10-20T10:00:00Z',
  }
}

describe('NotificacionesSistema', () => {
  it('muestra el contador y la lista al abrir la campana', async () => {
    render(<NotificacionesSistema mensajes={[nota(1, 'Primera'), nota(2, 'Segunda')]} />)
    const boton = screen.getByRole('button', { name: /Notificaciones del sistema: 2/ })
    await userEvent.click(boton)
    expect(screen.getByText(/Segunda/)).toBeInTheDocument()
    expect(screen.getByText(/Primera/)).toBeInTheDocument()
  })

  it('lo que ya estaba al cargar no salta como novedad; un aviso nuevo sí', () => {
    const { rerender } = render(<NotificacionesSistema mensajes={[nota(1, 'Vieja')]} />)
    expect(screen.queryByText(/Nuevo aviso \(simulado\)/)).not.toBeInTheDocument()
    rerender(<NotificacionesSistema mensajes={[nota(1, 'Vieja'), nota(2, 'Aviso fresco')]} />)
    expect(screen.getByRole('status')).toHaveTextContent(/Nuevo aviso \(simulado\)/)
    expect(screen.getByRole('status')).toHaveTextContent(/Aviso fresco/)
  })

  it('sin notificaciones lo dice', async () => {
    render(<NotificacionesSistema mensajes={[]} />)
    await userEvent.click(screen.getByRole('button', { name: /Notificaciones del sistema: 0/ }))
    expect(screen.getByText('Sin notificaciones.')).toBeInTheDocument()
  })
})
