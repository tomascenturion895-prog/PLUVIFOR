import type {
  AccumulatedOut,
  DataCategory,
  ImportKind,
  ImportLog,
  ImportReport,
  NetworkHealth,
  Report,
  Series,
  Station,
  StationList,
} from './types'

/** Error de la API o de la red, con un mensaje listo para mostrar (en español). */
export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(status: number, code: string, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
  }
}

const MENSAJES_POR_ESTADO: Record<number, string> = {
  400: 'El pedido no es válido.',
  401: 'Falta la clave de administración o es incorrecta.',
  403: 'No tenés permiso para hacer esto.',
  404: 'No se encontró lo que buscabas.',
  413: 'El archivo es demasiado grande.',
  422: 'Los datos enviados no son válidos.',
  429: 'Hiciste demasiados pedidos seguidos. Esperá un momento.',
}

const MENSAJE_RED = 'No se pudo conectar con el servidor. Revisá tu conexión e intentá de nuevo.'
const MENSAJE_GENERICO = 'Ocurrió un error inesperado. Intentá de nuevo en unos minutos.'

/** Dirección base de la API. Vacía en desarrollo: Vite reenvía /api al backend. */
export function apiBase(): string {
  const base = import.meta.env.VITE_API_URL
  return typeof base === 'string' && import.meta.env.PROD ? base.replace(/\/$/, '') : ''
}

async function leerError(response: Response): Promise<ApiError> {
  let code = 'http_error'
  let message = MENSAJES_POR_ESTADO[response.status]
  try {
    const body: unknown = await response.json()
    const error = (body as { error?: { code?: unknown; message?: unknown } }).error
    if (typeof error?.message === 'string' && error.message) message = error.message
    if (typeof error?.code === 'string') code = error.code
  } catch {
    // el cuerpo no era JSON: se usa el mensaje por estado
  }
  if (!message) message = response.status >= 500 ? MENSAJE_GENERICO : MENSAJES_POR_ESTADO[400]
  return new ApiError(response.status, code, message)
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${apiBase()}${path}`, init)
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause
    throw new ApiError(0, 'network_error', MENSAJE_RED)
  }
  if (!response.ok) throw await leerError(response)
  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(response.status, 'invalid_response', MENSAJE_GENERICO)
  }
}

function query(params: Record<string, string | number | undefined>): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') search.set(key, String(value))
  }
  const text = search.toString()
  return text ? `?${text}` : ''
}

export function getStations(
  params: { q?: string; limit?: number; offset?: number } = {},
  signal?: AbortSignal,
): Promise<StationList> {
  return request<StationList>(`/api/stations${query(params)}`, { signal })
}

export function getStation(id: number, signal?: AbortSignal): Promise<Station> {
  return request<Station>(`/api/stations/${id}`, { signal })
}

export function getRainfall(
  params: { stationId: number; from: string; to: string; category?: DataCategory },
  signal?: AbortSignal,
): Promise<Series> {
  const { stationId, from, to, category } = params
  return request<Series>(`/api/rainfall${query({ station_id: stationId, from, to, category })}`, {
    signal,
  })
}

/** Fuente que hoy sabe leer la API. No se agregan otras hasta que exista su conector. */
export const FUENTE_IMPORTACION = 'siga_inta'

function conClave(apiKey: string): Record<string, string> {
  return { 'X-API-Key': apiKey }
}

function importar(
  accion: 'audit' | 'commit',
  params: { apiKey: string; kind: ImportKind; filename: string; content: string },
  signal?: AbortSignal,
): Promise<ImportReport> {
  const { apiKey, kind, filename, content } = params
  const search = query({ source: FUENTE_IMPORTACION, kind, filename })
  return request<ImportReport>(`/api/import/${accion}${search}`, {
    method: 'POST',
    headers: { ...conClave(apiKey), 'Content-Type': 'text/csv' },
    body: content,
    signal,
  })
}

/** Valida el archivo y devuelve el informe sin guardar nada. */
export const auditImport = (
  params: Parameters<typeof importar>[1],
  signal?: AbortSignal,
): Promise<ImportReport> => importar('audit', params, signal)

/** Guarda lo aceptado y registra la carga. */
export const commitImport = (
  params: Parameters<typeof importar>[1],
  signal?: AbortSignal,
): Promise<ImportReport> => importar('commit', params, signal)

export function getImportLogs(apiKey: string, signal?: AbortSignal): Promise<ImportLog[]> {
  return request<ImportLog[]>(`/api/import/logs${query({ limit: 20 })}`, {
    headers: conClave(apiKey),
    signal,
  })
}

/** Acumulado por estación. Los acumulados de estaciones distintas no se suman. */
export function getAccumulated(
  params: {
    from: string
    to: string
    zone?: string
    station_id?: number
    category?: DataCategory
  },
  signal?: AbortSignal,
): Promise<AccumulatedOut> {
  const { from, to, zone, station_id, category } = params
  return request<AccumulatedOut>(
    `/api/rainfall/accumulated${query({ from, to, zone, station_id, category })}`,
    { signal },
  )
}

/** Parte pluvial de una o más estaciones. Los acumulados de estaciones distintas no se suman. */
export function getReport(
  params: { stationIds: number[]; from: string; to: string; category?: DataCategory },
  signal?: AbortSignal,
): Promise<Report> {
  const { stationIds, from, to, category } = params
  return request<Report>('/api/reports/summary', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ station_ids: stationIds, from, to, category }),
    signal,
  })
}

/** Estaciones activas, en silencio y sin datos, calculadas contra la fecha de corte. */
export function getNetworkHealth(
  params: { silentAfterDays?: number } = {},
  signal?: AbortSignal,
): Promise<NetworkHealth> {
  return request<NetworkHealth>(
    `/api/network/health${query({ silent_after_days: params.silentAfterDays })}`,
    { signal },
  )
}
