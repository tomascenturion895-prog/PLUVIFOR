import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError } from '../api/client'
import type { FieldReport as Reporte } from '../api/types'
import FieldReport from './FieldReport'
import { aNumero, armarPedido, type FormularioReporte } from './field-report-datos'

vi.mock('../api/client', async (original) => ({
  ...(await original<typeof import('../api/client')>()),
  postFieldReport: vi.fn(),
}))
import { postFieldReport } from '../api/client'

const BASE: FormularioReporte = {
  fecha: '2026-10-20',
  mm: '12,5',
  lugar: 'Comisaría',
  quien: 'Agente',
  lat: '',
  lon: '',
  origen: null,
}

function guardado(extra: Partial<Reporte> = {}): Reporte {
  return {
    id: 1,
    obs_date: '2026-10-20',
    mm: 12.5,
    place: 'Comisaría',
    reporter: 'Agente',
    lat: null,
    lon: null,
    location_status: 'pendiente',
    location_source: null,
    category: 'observado',
    validation: 'sin_validar',
    source: 'reporte_policial',
    created_at: '2026-11-19T10:00:00Z',
    ...extra,
  }
}

afterEach(() => {
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

async function completar(usuario: ReturnType<typeof userEvent.setup>) {
  await usuario.type(screen.getByLabelText('Clave'), 'secreta')
  await usuario.type(screen.getByLabelText('Fecha de la lluvia'), '2026-10-20')
  await usuario.type(screen.getByLabelText('Milímetros'), '12,5')
  await usuario.type(screen.getByLabelText('Lugar'), 'Comisaría')
  await usuario.type(screen.getByLabelText('Quién reporta'), 'Agente')
}

describe('armarPedido', () => {
  it('acepta coma decimal y deja la ubicación fuera si no se informó', () => {
    const r = armarPedido(BASE)
    expect(r).toEqual({
      ok: true,
      sinUbicacion: true,
      pedido: { obs_date: '2026-10-20', mm: 12.5, place: 'Comisaría', reporter: 'Agente' },
    })
  })

  it('un 0 mm es un dato válido', () => {
    expect(armarPedido({ ...BASE, mm: '0' })).toMatchObject({ ok: true })
  })

  it.each([
    ['mm', '-1', 'negativos'],
    ['mm', 'mucho', 'como número'],
    ['mm', '1001', 'pasar de'],
    ['mm', '', 'como número'],
    ['fecha', '2026-11-01', 'posterior al corte'],
    ['fecha', '', 'fecha'],
    ['lugar', '   ', 'lugar'],
    ['quien', '', 'quién'],
    ['lat', '-26', 'juntas'],
    ['lon', '-58', 'juntas'],
  ])('rechaza %s = «%s»', (campo, valor, texto) => {
    const r = armarPedido({ ...BASE, [campo]: valor })
    expect(r.ok).toBe(false)
    if (!r.ok) expect(r.errores.join(' ')).toContain(texto)
  })

  it('rechaza coordenadas fuera de rango', () => {
    expect(armarPedido({ ...BASE, lat: '95', lon: '-58' }).ok).toBe(false)
    expect(armarPedido({ ...BASE, lat: '-26', lon: '-200' }).ok).toBe(false)
  })

  it('con ubicación manda el origen (manual por defecto)', () => {
    expect(armarPedido({ ...BASE, lat: '-26,18', lon: '-58,17' })).toMatchObject({
      ok: true,
      sinUbicacion: false,
      pedido: { lat: -26.18, lon: -58.17, location_source: 'manual' },
    })
  })

  it('aNumero no acepta basura', () => {
    expect(aNumero('1e3')).toBeNull()
    expect(aNumero('1,5')).toBe(1.5)
    expect(aNumero('')).toBeNull()
  })
})

describe('Reporte de campo', () => {
  it('envía un reporte sin ubicación y avisa que queda pendiente', async () => {
    vi.mocked(postFieldReport).mockResolvedValue(guardado())
    const usuario = userEvent.setup()
    render(<FieldReport />)
    await completar(usuario)
    await usuario.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(postFieldReport).toHaveBeenCalledWith('secreta', {
      obs_date: '2026-10-20',
      mm: 12.5,
      place: 'Comisaría',
      reporter: 'Agente',
    })
    expect(await screen.findByRole('status')).toHaveTextContent('con ubicación pendiente')
    expect(screen.getByRole('status')).toHaveTextContent('observado, sin validar')
  })

  it('no envía nada si falta algo y lo explica', async () => {
    const usuario = userEvent.setup()
    render(<FieldReport />)
    await usuario.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Indicá la fecha')
    expect(postFieldReport).not.toHaveBeenCalled()
  })

  it('pide la clave antes de enviar', async () => {
    const usuario = userEvent.setup()
    render(<FieldReport />)
    await usuario.type(screen.getByLabelText('Fecha de la lluvia'), '2026-10-20')
    await usuario.type(screen.getByLabelText('Milímetros'), '5')
    await usuario.type(screen.getByLabelText('Lugar'), 'x')
    await usuario.type(screen.getByLabelText('Quién reporta'), 'y')
    await usuario.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Ingresá la clave')
    expect(postFieldReport).not.toHaveBeenCalled()
  })

  it('muestra el error de la API en español', async () => {
    vi.mocked(postFieldReport).mockRejectedValue(
      new ApiError(401, 'unauthorized', 'Falta la clave de administración o es incorrecta.'),
    )
    const usuario = userEvent.setup()
    render(<FieldReport />)
    await completar(usuario)
    await usuario.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('clave de administración')
  })

  it('«Usar mi ubicación» completa los campos y marca el origen del dispositivo', async () => {
    vi.stubGlobal('navigator', {
      geolocation: {
        getCurrentPosition: (ok: (p: GeolocationPosition) => void) =>
          ok({ coords: { latitude: -26.18, longitude: -58.17 } } as GeolocationPosition),
      },
    })
    vi.mocked(postFieldReport).mockResolvedValue(
      guardado({
        lat: -26.18,
        lon: -58.17,
        location_status: 'informada',
        location_source: 'dispositivo',
      }),
    )
    const usuario = userEvent.setup()
    render(<FieldReport />)
    await completar(usuario)
    await usuario.click(screen.getByRole('button', { name: 'Usar mi ubicación' }))
    expect(screen.getByLabelText('Latitud')).toHaveValue('-26.18000')
    await usuario.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(postFieldReport).toHaveBeenCalledWith(
      'secreta',
      expect.objectContaining({ lat: -26.18, lon: -58.17, location_source: 'dispositivo' }),
    )
  })

  it('si niegan el permiso, avisa y deja la ubicación vacía (no se inventa)', async () => {
    vi.stubGlobal('navigator', {
      geolocation: {
        getCurrentPosition: (_ok: unknown, error: () => void) => error(),
      },
    })
    const usuario = userEvent.setup()
    render(<FieldReport />)
    await usuario.click(screen.getByRole('button', { name: 'Usar mi ubicación' }))
    expect(screen.getByRole('status')).toHaveTextContent('No se pudo obtener la ubicación')
    expect(screen.getByLabelText('Latitud')).toHaveValue('')
  })

  it('editar la ubicación a mano cambia el origen a manual', async () => {
    vi.stubGlobal('navigator', {
      geolocation: {
        getCurrentPosition: (ok: (p: GeolocationPosition) => void) =>
          ok({ coords: { latitude: -26, longitude: -58 } } as GeolocationPosition),
      },
    })
    vi.mocked(postFieldReport).mockResolvedValue(guardado())
    const usuario = userEvent.setup()
    render(<FieldReport />)
    await completar(usuario)
    await usuario.click(screen.getByRole('button', { name: 'Usar mi ubicación' }))
    await usuario.type(screen.getByLabelText('Latitud'), '1')
    await usuario.click(screen.getByRole('button', { name: 'Enviar reporte' }))
    expect(postFieldReport).toHaveBeenCalledWith(
      'secreta',
      expect.objectContaining({ location_source: 'manual' }),
    )
  })
})
