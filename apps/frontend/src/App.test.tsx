import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import App from './App'
import { LEYENDA_PROTOTIPO } from './constants'

describe('App', () => {
  it('muestra el nombre del proyecto', () => {
    render(<App />)
    expect(screen.getByRole('heading', { name: 'PLUVIFOR' })).toBeInTheDocument()
  })

  it('muestra siempre la leyenda obligatoria de prototipo', () => {
    render(<App />)
    expect(screen.getByText(LEYENDA_PROTOTIPO)).toBeInTheDocument()
  })
})
