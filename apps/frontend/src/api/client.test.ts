import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, getRainfall, getSensorReadings, getStations, request } from './client'

function responder(status: number, cuerpo?: unknown, texto?: string) {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue({
      ok: status >= 200 && status < 300,
      status,
      json: () =>
        texto !== undefined ? Promise.reject(new Error('no es JSON')) : Promise.resolve(cuerpo),
    }),
  )
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('cliente de la API', () => {
  it('devuelve el cuerpo cuando todo sale bien', async () => {
    responder(200, { items: [], total: 0, limit: 50, offset: 0 })
    await expect(getStations()).resolves.toEqual({ items: [], total: 0, limit: 50, offset: 0 })
  })

  it('arma la consulta sin parámetros vacíos', async () => {
    responder(200, {})
    await getRainfall({ stationId: 7, from: '2016-01-01', to: '2016-01-31' })
    const url = (fetch as ReturnType<typeof vi.fn>).mock.calls[0][0] as string
    expect(url).toBe('/api/rainfall?station_id=7&from=2016-01-01&to=2016-01-31')
  })

  it('pide las lecturas de sensores con su filtro y sin parámetros vacíos', async () => {
    responder(200, { items: [], total: 0, notice: 'n' })
    await getSensorReadings({ deviceId: 'SIM-001', limit: 10 })
    await getSensorReadings()
    const llamadas = (fetch as ReturnType<typeof vi.fn>).mock.calls.map((c) => c[0] as string)
    expect(llamadas).toEqual([
      '/api/sensor-readings?device_id=SIM-001&limit=10',
      '/api/sensor-readings',
    ])
  })

  it('usa el mensaje en español que manda la API', async () => {
    responder(404, { error: { code: 'not_found', message: 'La estación no existe.' } })
    const error = await request('/api/stations/9').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({
      status: 404,
      code: 'not_found',
      message: 'La estación no existe.',
    })
  })

  it('si el cuerpo del error no es JSON, usa un mensaje por estado', async () => {
    responder(401, undefined, 'x')
    await expect(request('/api/import/commit')).rejects.toMatchObject({
      status: 401,
      message: 'Falta la clave de administración o es incorrecta.',
    })
  })

  it('un error del servidor no muestra detalles internos', async () => {
    responder(500, '<html>Traceback…</html>', 'x')
    const error = (await request('/x').catch((e: unknown) => e)) as ApiError
    expect(error.message).toBe('Ocurrió un error inesperado. Intentá de nuevo en unos minutos.')
  })

  it('si no hay conexión, explica que no se pudo conectar', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(request('/x')).rejects.toMatchObject({
      status: 0,
      code: 'network_error',
      message: expect.stringContaining('No se pudo conectar'),
    })
  })

  it('una respuesta que no es JSON es un error controlado', async () => {
    responder(200, undefined, 'x')
    await expect(request('/x')).rejects.toMatchObject({ code: 'invalid_response' })
  })
})
