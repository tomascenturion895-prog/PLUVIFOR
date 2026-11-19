import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { ImportLog, ImportReport } from '../api/types'
import Importar from './Importar'
import { esConfirmable } from './importar-datos'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  auditImport: vi.fn(),
  commitImport: vi.fn(),
  getImportLogs: vi.fn(),
}))
import { auditImport, commitImport, getImportLogs } from '../api/client'

function informe(overrides: Partial<ImportReport> = {}): ImportReport {
  return {
    filename: 'datos.csv',
    sha256: 'abc',
    mode: 'audit',
    saved: false,
    rows_read: 3,
    rows_accepted: 2,
    rows_rejected: 1,
    rejections_by_reason: { mm_negativo: 1 },
    rejections: [
      { line: 4, reason: 'mm_negativo', message: 'Los milímetros no pueden ser negativos.' },
    ],
    rejections_truncated: false,
    inserted: 0,
    updated: 0,
    ...overrides,
  }
}

const LOG: ImportLog = {
  id: 1,
  source: 'siga_inta',
  mode: 'commit',
  status: 'completed',
  filename: 'anterior.csv',
  sha256: 'def',
  rows_read: 10,
  rows_accepted: 9,
  rows_rejected: 1,
  rejections_by_reason: {},
  cutoff_applied: '2026-10-31',
  started_at: '2026-11-18T12:00:00Z',
}

const csv = (contenido = 'a,b\n1,2\n', nombre = 'datos.csv') =>
  new File([contenido], nombre, { type: 'text/csv' })

async function conClave(clave = 'clave-de-prueba') {
  render(<Importar />)
  await userEvent.type(screen.getByLabelText('Clave de administración'), clave)
}

async function subir(archivo: File) {
  await userEvent.upload(screen.getByLabelText(/Archivo \(\.csv/), archivo)
}

beforeEach(() => {
  vi.mocked(auditImport).mockReset()
  vi.mocked(commitImport).mockReset()
  vi.mocked(getImportLogs).mockReset().mockResolvedValue([LOG])
})

describe('permiso', () => {
  it('sin clave los botones están bloqueados y se explica por qué', async () => {
    render(<Importar />)
    expect(screen.getByRole('button', { name: 'Auditar' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Confirmar carga' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Ver historial' })).toBeDisabled()
    expect(screen.getByText(/Ingresá la clave de administración/)).toBeInTheDocument()
  })

  it('la clave no se muestra en pantalla ni se guarda en el navegador', async () => {
    await conClave('secreta-123')
    expect(screen.getByLabelText('Clave de administración')).toHaveAttribute('type', 'password')
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
    expect(document.body.textContent).not.toContain('secreta-123')
  })

  it('con clave pero sin archivo no se puede auditar', async () => {
    await conClave()
    expect(screen.getByRole('button', { name: 'Auditar' })).toBeDisabled()
  })

  it('si la API responde 401 se muestra el motivo y no se confirma nada', async () => {
    vi.mocked(auditImport).mockRejectedValue(
      new ApiError(401, 'unauthorized', 'Falta la clave de administración o es incorrecta.'),
    )
    await conClave('mala')
    await subir(csv())
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('clave de administración')
    expect(screen.getByRole('button', { name: 'Confirmar carga' })).toBeDisabled()
    expect(commitImport).not.toHaveBeenCalled()
  })
})

describe('archivo', () => {
  it('rechaza un archivo que no es .csv sin llamar a la API', async () => {
    await conClave()
    await subir(csv('x', 'datos.xlsx'))
    expect(await screen.findByRole('alert')).toHaveTextContent('debe ser un .csv')
    expect(screen.getByRole('button', { name: 'Auditar' })).toBeDisabled()
  })

  it('rechaza un archivo vacío', async () => {
    await conClave()
    await subir(csv('', 'vacio.csv'))
    expect(await screen.findByRole('alert')).toHaveTextContent('está vacío')
  })

  it('rechaza un archivo de más de 5 MB', async () => {
    await conClave()
    await subir(csv('x'.repeat(5 * 1024 * 1024 + 1), 'grande.csv'))
    expect(await screen.findByRole('alert')).toHaveTextContent('supera el máximo de 5 MB')
    expect(auditImport).not.toHaveBeenCalled()
  })
})

describe('auditoría y confirmación', () => {
  it('un archivo con filas inválidas muestra cada motivo en español', async () => {
    vi.mocked(auditImport).mockResolvedValue(informe())
    await conClave()
    await subir(csv('contenido,del,archivo\n'))
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    const seccion = (await screen.findByRole('heading', { name: 'Informe de auditoría' })).closest(
      'section',
    )!
    expect(within(seccion).getByText('Los milímetros no pueden ser negativos.')).toBeInTheDocument()
    expect(
      within(seccion).getByText('Todavía no se guardó nada: revisá el informe y confirmá.'),
    ).toBeInTheDocument()
    expect(auditImport).toHaveBeenCalledWith(
      expect.objectContaining({
        apiKey: 'clave-de-prueba',
        kind: 'rainfall',
        filename: 'datos.csv',
        content: 'contenido,del,archivo\n',
      }),
    )
  })

  it('un informe sin ninguna fila válida no se puede confirmar', async () => {
    vi.mocked(auditImport).mockResolvedValue(informe({ rows_accepted: 0, rows_rejected: 3 }))
    await conClave()
    await subir(csv())
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    expect(await screen.findByText(/Ninguna fila es válida/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Confirmar carga' })).toBeDisabled()
  })

  it('un archivo válido se confirma, se muestra el resultado y se recarga el historial', async () => {
    vi.mocked(auditImport).mockResolvedValue(informe({ rows_rejected: 0, rejections: [] }))
    vi.mocked(commitImport).mockResolvedValue(
      informe({ mode: 'commit', saved: true, rows_rejected: 0, rejections: [], inserted: 2 }),
    )
    await conClave()
    await subir(csv())
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Confirmar carga' })).toBeEnabled(),
    )
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar carga' }))
    expect(await screen.findByRole('heading', { name: 'Carga confirmada' })).toBeInTheDocument()
    expect(commitImport).toHaveBeenCalledTimes(1)
    expect(await screen.findByText('anterior.csv')).toBeInTheDocument()
  })

  it('después de confirmar no se puede confirmar de nuevo el mismo informe', async () => {
    vi.mocked(auditImport).mockResolvedValue(informe())
    vi.mocked(commitImport).mockResolvedValue(informe({ mode: 'commit', saved: true, inserted: 2 }))
    await conClave()
    await subir(csv())
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Confirmar carga' })).toBeEnabled(),
    )
    await userEvent.click(screen.getByRole('button', { name: 'Confirmar carga' }))
    await screen.findByRole('heading', { name: 'Carga confirmada' })
    expect(screen.getByRole('button', { name: 'Confirmar carga' })).toBeDisabled()
  })

  it('al cambiar de archivo se descarta el informe anterior', async () => {
    vi.mocked(auditImport).mockResolvedValue(informe())
    await conClave()
    await subir(csv())
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    await screen.findByRole('heading', { name: 'Informe de auditoría' })
    await subir(csv('otro,archivo\n', 'otro.csv'))
    expect(screen.queryByRole('heading', { name: 'Informe de auditoría' })).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Confirmar carga' })).toBeDisabled()
  })

  it('avisa si la lista de rechazos está recortada', async () => {
    vi.mocked(auditImport).mockResolvedValue(informe({ rejections_truncated: true }))
    await conClave()
    await subir(csv())
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    expect(
      await screen.findByText(/Se muestran solo las primeras filas rechazadas/),
    ).toBeInTheDocument()
  })

  it('envía el tipo de archivo elegido', async () => {
    vi.mocked(auditImport).mockResolvedValue(informe())
    await conClave()
    await userEvent.selectOptions(screen.getByLabelText('Tipo de archivo'), 'stations')
    await subir(csv())
    await userEvent.click(screen.getByRole('button', { name: 'Auditar' }))
    await waitFor(() =>
      expect(auditImport).toHaveBeenCalledWith(expect.objectContaining({ kind: 'stations' })),
    )
  })
})

describe('historial', () => {
  it('con clave se puede ver el historial de cargas', async () => {
    await conClave()
    await userEvent.click(screen.getByRole('button', { name: 'Ver historial' }))
    expect(await screen.findByText('anterior.csv')).toBeInTheDocument()
    expect(getImportLogs).toHaveBeenCalledWith('clave-de-prueba')
  })

  it('sin cargas muestra un mensaje vacío', async () => {
    vi.mocked(getImportLogs).mockResolvedValue([])
    await conClave()
    await userEvent.click(screen.getByRole('button', { name: 'Ver historial' }))
    expect(await screen.findByText('Todavía no hay cargas registradas.')).toBeInTheDocument()
  })

  it('si falla muestra el error y permite reintentar', async () => {
    vi.mocked(getImportLogs)
      .mockRejectedValueOnce(
        new ApiError(0, 'network_error', 'No se pudo conectar con el servidor.'),
      )
      .mockResolvedValueOnce([LOG])
    await conClave()
    await userEvent.click(screen.getByRole('button', { name: 'Ver historial' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No se pudo conectar')
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(await screen.findByText('anterior.csv')).toBeInTheDocument()
  })
})

describe('esConfirmable', () => {
  it('solo un informe de auditoría con filas aceptadas', () => {
    expect(esConfirmable(null)).toBe(false)
    expect(esConfirmable(informe())).toBe(true)
    expect(esConfirmable(informe({ rows_accepted: 0 }))).toBe(false)
    expect(esConfirmable(informe({ mode: 'commit' }))).toBe(false)
  })
})
