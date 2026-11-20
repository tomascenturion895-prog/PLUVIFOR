import type {
  AccumulatedOut,
  DataCategory,
  ImportKind,
  ImportLog,
  FieldReport,
  FieldReportIn,
  ClimateReferenceOut,
  EventsOut,
  GapEstimateList,
  AlertInbox,
  AlertOutboxList,
  AlertPreview,
  AlertSend,
  AlertSubscriptionStatus,
  RecurrenceOut,
  SensorDeviceList,
  SensorReadingList,
  ImportReport,
  NetworkHealth,
  Report,
  Series,
  SeriesCompare,
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

/** Series de 2 o más estaciones con las advertencias de comparabilidad de la API. */
export function getCompare(
  params: { stationIds: number[]; from: string; to: string; category?: DataCategory },
  signal?: AbortSignal,
): Promise<SeriesCompare> {
  const { stationIds, from, to, category } = params
  return request<SeriesCompare>(
    `/api/rainfall/compare${query({ station_ids: stationIds.join(','), from, to, category })}`,
    { signal },
  )
}

/** Carga un reporte de campo (policial). Entra como observado y sin validar. */
export function postFieldReport(
  apiKey: string,
  reporte: FieldReportIn,
  signal?: AbortSignal,
): Promise<FieldReport> {
  return request<FieldReport>('/api/field-reports', {
    method: 'POST',
    headers: { ...conClave(apiKey), 'Content-Type': 'application/json' },
    body: JSON.stringify(reporte),
    signal,
  })
}

/** Últimas lecturas de dispositivos. Siempre simuladas: no se suman a las series de lluvia. */
export function getSensorReadings(
  params: { deviceId?: string; limit?: number; offset?: number } = {},
  signal?: AbortSignal,
): Promise<SensorReadingList> {
  return request<SensorReadingList>(
    `/api/sensor-readings${query({ device_id: params.deviceId, limit: params.limit, offset: params.offset })}`,
    { signal },
  )
}

/** Dispositivos que enviaron lecturas, con la última de cada uno. Siempre simulados. */
export function getSensorDevices(
  params: { silentAfterDays?: number } = {},
  signal?: AbortSignal,
): Promise<SensorDeviceList> {
  return request<SensorDeviceList>(
    `/api/sensor-readings/devices${query({ silent_after_days: params.silentAfterDays })}`,
    { signal },
  )
}

/** Días sin dato rellenados con un valor ESTIMADO. Se muestran aparte: nunca entran en lo observado. */
export function getEstimates(
  params: { stationId?: number; from?: string; to?: string; limit?: number } = {},
  signal?: AbortSignal,
): Promise<GapEstimateList> {
  return request<GapEstimateList>(
    `/api/estimates${query({ station_id: params.stationId, from: params.from, to: params.to, limit: params.limit })}`,
    { signal },
  )
}

/** Días de 50 y 100 mm o más y rachas secas de una estación. Descriptivo: no es una alerta. */
export function getEvents(
  params: { stationId: number; from: string; to: string; minDryDays?: number },
  signal?: AbortSignal,
): Promise<EventsOut> {
  return request<EventsOut>(
    `/api/events${query({ station_id: params.stationId, from: params.from, to: params.to, min_dry_days: params.minDryDays })}`,
    { signal },
  )
}

/** Normal mensual de una estación. Es referencia: no se suma ni se promedia con lo observado. */
export function getClimateReference(
  stationId: number,
  signal?: AbortSignal,
): Promise<ClimateReferenceOut> {
  return request<ClimateReferenceOut>(`/api/climate-reference${query({ station_id: stationId })}`, {
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

function postJson<T>(path: string, cuerpo: unknown, signal?: AbortSignal): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cuerpo),
    signal,
  })
}

/** Pide avisos de lluvia: se «manda» un código por WhatsApp (simulado). El correo es opcional. */
export function suscribirseAvisos(
  phone: string,
  opciones: { email?: string; stationId?: number } = {},
  signal?: AbortSignal,
): Promise<AlertSubscriptionStatus> {
  return postJson(
    '/api/alerts/subscriptions',
    { phone, email: opciones.email || undefined, station_id: opciones.stationId },
    signal,
  )
}

export function confirmarAvisos(
  phone: string,
  code: string,
  signal?: AbortSignal,
): Promise<AlertSubscriptionStatus> {
  return postJson('/api/alerts/subscriptions/confirm', { phone, code }, signal)
}

export function bajaAvisos(phone: string, signal?: AbortSignal): Promise<AlertSubscriptionStatus> {
  return postJson('/api/alerts/subscriptions/unsubscribe', { phone }, signal)
}

/** Mensajes que se enviarían. Solo el personal, con la clave de administración. */
export function getBandejaAvisos(apiKey: string, signal?: AbortSignal): Promise<AlertOutboxList> {
  return request<AlertOutboxList>('/api/alerts/outbox?limit=20', {
    headers: conClave(apiKey),
    signal,
  })
}

/** Cada cuánto llovió 50 y 100 mm o más en una estación. Histórico y descriptivo, no es predicción. */
export function getRecurrence(
  params: { stationId: number; from: string; to: string },
  signal?: AbortSignal,
): Promise<RecurrenceOut> {
  return request<RecurrenceOut>(
    `/api/recurrence${query({ station_id: params.stationId, from: params.from, to: params.to })}`,
    { signal },
  )
}

/** Demostración: el celular y el correo (simulados) de quien se registró. Solo con ALERTS_DEMO. */
export function getInboxAvisos(phone: string, signal?: AbortSignal): Promise<AlertInbox> {
  return postJson('/api/alerts/inbox', { phone }, signal)
}

/** Qué avisaría el sistema para una estación y un día. Solo el personal. */
export function previsualizarAviso(
  apiKey: string,
  params: { stationId: number; date: string },
  signal?: AbortSignal,
): Promise<AlertPreview> {
  return request<AlertPreview>(
    `/api/alerts/preview${query({ station_id: params.stationId, date: params.date })}`,
    { headers: conClave(apiKey), signal },
  )
}

/** Entrega el aviso (simulado) a las suscripciones confirmadas. Solo el personal. */
export function enviarAviso(
  apiKey: string,
  params: { stationId: number; date: string },
  signal?: AbortSignal,
): Promise<AlertSend> {
  return request<AlertSend>(
    `/api/alerts/send${query({ station_id: params.stationId, date: params.date })}`,
    { method: 'POST', headers: conClave(apiKey), signal },
  )
}
