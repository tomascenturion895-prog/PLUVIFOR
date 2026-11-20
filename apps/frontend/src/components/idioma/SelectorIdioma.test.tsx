import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { ProveedorIdioma } from '../../i18n/contexto'
import { CLAVE_IDIOMA } from '../../i18n/idioma-datos'
import SelectorIdioma from './SelectorIdioma'

beforeEach(() => localStorage.clear())
afterEach(() => {
  document.documentElement.lang = 'es'
  delete document.documentElement.dataset.idioma
})

describe('selector de idioma', () => {
  it('ofrece los 5 idiomas y empieza en español', () => {
    render(
      <ProveedorIdioma>
        <SelectorIdioma />
      </ProveedorIdioma>,
    )
    const select = screen.getByRole('combobox', { name: 'Idioma de la interfaz' })
    expect(select).toHaveValue('es')
    expect(screen.getAllByRole('option')).toHaveLength(5)
    expect(document.documentElement.lang).toBe('es')
  })

  it('cambia de idioma, actualiza html[lang] y guarda en localStorage', async () => {
    render(
      <ProveedorIdioma>
        <SelectorIdioma />
      </ProveedorIdioma>,
    )
    const select = screen.getByRole('combobox')
    await userEvent.selectOptions(select, 'gn')
    expect(select).toHaveValue('gn')
    expect(document.documentElement.lang).toBe('gn')
    expect(localStorage.getItem(CLAVE_IDIOMA)).toBe('gn')

    await userEvent.selectOptions(select, 'tob')
    expect(select).toHaveValue('tob')
    expect(document.documentElement.lang).toBe('tob')
    expect(localStorage.getItem(CLAVE_IDIOMA)).toBe('tob')
  })

  it('recupera el idioma guardado al recargar', () => {
    localStorage.setItem(CLAVE_IDIOMA, 'en')
    render(
      <ProveedorIdioma>
        <SelectorIdioma />
      </ProveedorIdioma>,
    )
    expect(screen.getByRole('combobox')).toHaveValue('en')
    expect(document.documentElement.lang).toBe('en')
  })

  it('un valor guardado inválido vuelve a español', () => {
    localStorage.setItem(CLAVE_IDIOMA, 'jp')
    render(
      <ProveedorIdioma>
        <SelectorIdioma />
      </ProveedorIdioma>,
    )
    expect(screen.getByRole('combobox')).toHaveValue('es')
  })
})
