import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { Report, StationList } from '../api/types'
import { FECHA_CORTE } from '../constants'
import Parte from './Parte'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  getStations: vi.fn(),
  getReport: vi.fn(),
}))
import { getReport, getStations } from '../api/client'

const ESTACIONES = {
  items: [
    { id: 1, code: '424', name: 'El Colorado' },
    { id: 2, code: '425', name: 'Bartolomé de las Casas' },
  ],
  total: 2,
  limit: 200,
  offset: 0,
} as unknown as StationList

const TEXTO = [
  'PARTE PLUVIAL · Formosa',
  'El Colorado: 67,5 mm en 3 de 5 días.',
  '2 días sin dato: no se cuentan como 0 mm.',
  'PROTOTIPO · AI LAB Misión: Código Formosa · no es una herramienta oficial',
].join('\n')

function parte(overrides: Partial<Report> = {}): Report {
  return {
    category: 'observado',
    date_from: '2026-10-25',
    date_to: FECHA_CORTE,
    data_cutoff_date: FECHA_CORTE,
    clipped_to_cutoff: false,
    stations: [],
    comparability_warnings: [],
    not_evaluated: [],
    text: TEXTO,
    notice: 'PROTOTIPO',
    ...overrides,
  }
}

async function generar(...nombres: string[]) {
  render(<Parte />)
  for (const nombre of nombres) {
    await userEvent.click(await screen.findByRole('checkbox', { name: new RegExp(nombre) }))
  }
  await userEvent.click(screen.getByRole('button', { name: 'Generar parte' }))
}

let escribir: ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.mocked(getStations).mockResolvedValue(ESTACIONES)
  vi.mocked(getReport).mockReset().mockResolvedValue(parte())
  escribir = vi.fn().mockResolvedValue(undefined)
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText: escribir },
    configurable: true,
  })
})

afterEach(() => vi.restoreAllMocks())

describe('pantalla Parte pluvial', () => {
  it('sin estaciones elegidas no se puede generar', async () => {
    render(<Parte />)
    await screen.findByRole('checkbox', { name: /El Colorado/ })
    expect(screen.getByRole('button', { name: 'Generar parte' })).toBeDisabled()
  })

  it('pide el parte con las estaciones y el período elegidos', async () => {
    await generar('El Colorado', 'Bartolomé')
    await screen.findByLabelText('Parte pluvial')
    expect(getReport).toHaveBeenCalledWith(
      expect.objectContaining({ stationIds: [1, 2], to: FECHA_CORTE }),
    )
  })

  it('muestra el texto completo con los huecos declarados y la leyenda de prototipo', async () => {
    await generar('El Colorado')
    const texto = await screen.findByText(/PARTE PLUVIAL/)
    expect(texto.textContent).toBe(TEXTO)
    expect(texto.textContent).toContain('no se cuentan como 0 mm')
    expect(texto.textContent).toContain('no es una herramienta oficial')
  })

  it('Copiar pega el texto completo', async () => {
    await generar('El Colorado')
    await userEvent.click(await screen.findByRole('button', { name: 'Copiar texto' }))
    expect(escribir).toHaveBeenCalledWith(TEXTO)
    expect(await screen.findByText(/Texto copiado/)).toBeInTheDocument()
  })

  it('si el navegador no deja copiar, lo avisa en vez de fingir que copió', async () => {
    escribir.mockRejectedValue(new Error('denegado'))
    await generar('El Colorado')
    await userEvent.click(await screen.findByRole('button', { name: 'Copiar texto' }))
    expect(await screen.findByText(/No se pudo copiar automáticamente/)).toBeInTheDocument()
    expect(screen.queryByText(/Texto copiado/)).not.toBeInTheDocument()
  })

  it('Imprimir abre el diálogo de impresión', async () => {
    const imprimir = vi.spyOn(window, 'print').mockImplementation(() => {})
    await generar('El Colorado')
    await userEvent.click(await screen.findByRole('button', { name: 'Imprimir' }))
    expect(imprimir).toHaveBeenCalledTimes(1)
  })

  it('los controles se ocultan al imprimir y el texto del parte no', async () => {
    await generar('El Colorado')
    const articulo = await screen.findByLabelText('Parte pluvial')
    const ocultos = articulo.querySelectorAll('.no-imprimir')
    expect(ocultos.length).toBeGreaterThan(0)
    expect(screen.getByText(/PARTE PLUVIAL/)).not.toHaveClass('no-imprimir')
    expect(screen.getByText(/PARTE PLUVIAL/).closest('.no-imprimir')).toBeNull()
  })

  it('muestra las advertencias de comparabilidad y las reglas no evaluadas', async () => {
    vi.mocked(getReport).mockResolvedValue(
      parte({
        comparability_warnings: [
          {
            code: 'horario_corte_distinto',
            message: 'Las redes cierran el día a horas distintas.',
            severity: 'aviso',
            start_date: null,
            end_date: null,
          },
        ],
        not_evaluated: [{ code: 'inconsistente_con_vecinas', reason: 'Faltan coordenadas.' }],
      }),
    )
    await generar('El Colorado', 'Bartolomé')
    expect(await screen.findByText('Horario de corte distinto')).toBeInTheDocument()
    expect(screen.getByText('Faltan coordenadas.')).toBeInTheDocument()
  })

  it('si la API falla muestra el mensaje y no deja un parte viejo en pantalla', async () => {
    await generar('El Colorado')
    await screen.findByLabelText('Parte pluvial')
    vi.mocked(getReport).mockRejectedValue(
      new ApiError(404, 'station_not_found', 'No existe la estación pedida.'),
    )
    await userEvent.click(screen.getByRole('button', { name: 'Generar parte' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('No existe la estación pedida.')
    await waitFor(() => expect(screen.queryByLabelText('Parte pluvial')).not.toBeInTheDocument())
  })

  it('un período invertido bloquea el botón y lo explica', async () => {
    render(<Parte />)
    await userEvent.click(await screen.findByRole('checkbox', { name: /El Colorado/ }))
    const hasta = screen.getByLabelText('Hasta')
    await userEvent.clear(hasta)
    await userEvent.type(hasta, '2026-01-01')
    expect(await screen.findByText(/Elegí un período válido/)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Generar parte' })).toBeDisabled()
  })

  it('las fechas no pasan del corte 31/10/2026', async () => {
    render(<Parte />)
    await screen.findByRole('checkbox', { name: /El Colorado/ })
    expect(screen.getByLabelText('Desde')).toHaveAttribute('max', FECHA_CORTE)
    expect(screen.getByLabelText('Hasta')).toHaveAttribute('max', FECHA_CORTE)
  })

  it('sin estaciones cargadas lo dice', async () => {
    vi.mocked(getStations).mockResolvedValue({ ...ESTACIONES, items: [], total: 0 })
    render(<Parte />)
    expect(await screen.findByText('No hay estaciones cargadas.')).toBeInTheDocument()
  })
})
