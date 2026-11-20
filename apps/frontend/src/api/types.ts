/** Tipos que devuelve la API (apps/backend/app/schemas). Los nombres de campos son los de la API. */

export type RainState = 'dato' | 'fila_sin_valor' | 'sin_fila'
export type DataCategory = 'observado' | 'referencia' | 'estimado'
export type CoordsStatus = 'verificada' | 'pendiente'
export type Severity = 'aviso' | 'alerta'

export interface Source {
  code: string
  name: string
  network: string
  category: DataCategory
  day_cutoff_local: string | null
}

export interface Station {
  id: number
  code: string
  internal_code: string | null
  name: string
  kind: string | null
  locality: string | null
  department: string | null
  zone: string | null
  /** Vacíos cuando están pendientes: nunca se inventan. */
  lat: number | null
  lon: number | null
  elevation_m: number | null
  coords_status: CoordsStatus
  active_from: string | null
  active_to: string | null
  source: Source
}

export interface StationList {
  items: Station[]
  total: number
  limit: number
  offset: number
}

export interface Day {
  obs_date: string
  state: RainState
  /** null = sin dato. Nunca es 0 para un hueco. */
  mm: number | null
  category: DataCategory
  source: string
  flags: string[]
}

export interface Summary {
  days_in_period: number
  days_with_data: number
  days_sin_fila: number
  days_fila_sin_valor: number
  coverage: number
  accumulated_mm: number | null
}

export interface Warning {
  code: string
  message: string
  severity: Severity
  start_date: string | null
  end_date: string | null
}

export interface Series {
  station_id: number
  station_name: string
  source: Source
  category: DataCategory
  date_from: string
  date_to: string
  data_cutoff_date: string
  clipped_to_cutoff: boolean
  summary: Summary
  warnings: Warning[]
  days: Day[]
  notice: string
}

export interface ApiErrorBody {
  error: { code: string; message: string; details?: { field: string; message: string }[] }
}

export type ImportKind = 'rainfall' | 'stations'

export interface Rejection {
  line: number
  reason: string
  message: string
}

export interface ImportReport {
  filename: string
  sha256: string
  mode: 'audit' | 'commit'
  saved: boolean
  rows_read: number
  rows_accepted: number
  rows_rejected: number
  rejections_by_reason: Record<string, number>
  rejections: Rejection[]
  rejections_truncated: boolean
  inserted: number
  updated: number
}

export interface ImportLog {
  id: number
  source: string
  mode: string
  status: string
  filename: string
  sha256: string
  rows_read: number
  rows_accepted: number
  rows_rejected: number
  rejections_by_reason: Record<string, number>
  cutoff_applied: string
  started_at: string
}

export interface IntenseEvent {
  obs_date: string
  mm: number
  level_mm: number
}

export interface StationReport {
  station_id: number
  station_name: string
  source: Source
  category: DataCategory
  summary: Summary
  intense_events: IntenseEvent[]
  warnings: Warning[]
}

export interface AccumulatedStation {
  station_id: number
  station_name: string
  /** null = ningún día con dato. Nunca es 0 para un hueco. */
  accumulated_mm: number | null
  days_with_data: number
  days_without_data: number
  coverage: number
  warnings: Warning[]
}

export interface AccumulatedOut {
  /** Los acumulados de estaciones distintas no se suman. */
  category: DataCategory
  date_from: string
  date_to: string
  data_cutoff_date: string
  clipped_to_cutoff: boolean
  days_in_period: number
  stations: AccumulatedStation[]
  not_evaluated: string[]
  notice: string
}

export interface Report {
  category: DataCategory
  date_from: string
  date_to: string
  data_cutoff_date: string
  clipped_to_cutoff: boolean
  stations: StationReport[]
  comparability_warnings: Warning[]
  not_evaluated: { code: string; reason: string }[]
  text: string
  notice: string
}

export interface SeriesCompareStation {
  station_id: number
  station_name: string
  source: Source
  category: DataCategory
  summary: Summary
  warnings: Warning[]
  days: Day[]
}

export interface SeriesCompare {
  category: DataCategory
  date_from: string
  date_to: string
  data_cutoff_date: string
  clipped_to_cutoff: boolean
  stations: SeriesCompareStation[]
  comparability_warnings: Warning[]
  not_evaluated: { code: string; reason: string }[]
  notice: string
}

export type LocationSource = 'dispositivo' | 'manual'

export interface FieldReportIn {
  obs_date: string
  mm: number
  place: string
  reporter: string
  lat?: number
  lon?: number
  location_source?: LocationSource
}

export interface FieldReport {
  id: number
  obs_date: string
  mm: number
  place: string
  reporter: string
  lat: number | null
  lon: number | null
  location_status: 'informada' | 'pendiente'
  location_source: LocationSource | null
  category: DataCategory
  validation: 'validado' | 'sin_validar'
  source: string
  created_at: string
}

/** Lectura de un dispositivo. Hoy no hay sensores reales: la categoría siempre es «simulado». */
export interface SensorReading {
  id: number
  device_id: string
  read_at: string
  mm: number
  lat: number | null
  lon: number | null
  category: 'simulado'
  source: string
  created_at: string
}

/** Un dispositivo con su última lectura. Hoy todo es simulado. */
export interface SensorDevice {
  device_id: string
  readings: number
  first_read_at: string
  last_read_at: string
  /** Milímetros de la última lectura; puede ser un 0 real («midió y no llovió»). */
  last_mm: number
  category: 'simulado'
  /** Contra la fecha de corte de los datos. Un silencio no es 0 mm: `last_mm` sigue siendo el último valor real. */
  state: 'activa' | 'en_silencio'
  last_read_date: string
  days_since_last: number
}

export interface SensorDeviceList {
  items: SensorDevice[]
  total: number
  notice: string
  data_cutoff_date: string
  silent_after_days: number
  active: number
  silent: number
}

export interface SensorReadingList {
  items: SensorReading[]
  total: number
  notice: string
}

/** Cómo se calculó un día estimado y con qué vecinas. El objeto `detail` depende del método. */
export interface GapEstimate {
  station_id: number
  obs_date: string
  mm: number
  category: 'estimado'
  /** Cómo era el día original: sin fila o fila sin valor. Sigue siendo un hueco en lo observado. */
  gap_state: 'sin_fila' | 'fila_sin_valor'
  method: string
  detail: {
    vecinas?: { station_id: number; name: string; distance_km: number; mm: number }[]
    parametros?: { max_km?: number }
  }
  created_at: string
}

export interface GapEstimateList {
  category: 'estimado'
  notice: string
  items: GapEstimate[]
  total: number
  limit: number
  offset: number
}

export interface IntenseDay {
  obs_date: string
  mm: number
}

export interface DryStreak {
  start_date: string
  end_date: string
  days: number
  /** Toca un período con la advertencia de ceros prolongados: puede ser un sensor sin registrar. */
  zero_run_warning: boolean
}

export interface EventsStation {
  station_id: number
  station_name: string
  summary: Summary
  /** Incluye los días de 100 mm o más. */
  days_50mm_or_more: IntenseDay[]
  days_100mm_or_more: IntenseDay[]
  dry_streaks: DryStreak[]
  longest_dry_streak: DryStreak | null
  warnings: Warning[]
}

export interface EventsOut {
  category: DataCategory
  date_from: string
  date_to: string
  min_dry_days: number
  stations: EventsStation[]
  notice: string
  description: string
}

export interface ClimateReferenceOut {
  station_id: number
  station_name: string
  category: 'referencia'
  /** Vacío = no hay normal cargada para esta estación (no es 0). */
  normals: { period: string; source_note: string; months: { month: number; normal_mm: number }[] }[]
  notice: string
}

export type NetworkState = 'activa' | 'en_silencio' | 'sin_datos'

export interface StationHealth {
  station_id: number
  code: string
  name: string
  zone: string | null
  department: string | null
  source: string
  network: string
  state: NetworkState
  last_reading_date: string | null
  /** Milímetros de la última lectura con valor. Vacío si la estación nunca tuvo datos. */
  last_reading_mm: number | null
  days_since_last: number | null
}

export interface NetworkHealth {
  category: DataCategory
  data_cutoff_date: string
  silent_after_days: number
  active: number
  silent: number
  no_data: number
  stations: StationHealth[]
}

/** Estado de una suscripción a avisos. El canal es simulado: no sale ningún mensaje real. */
export interface AlertSubscriptionStatus {
  status: 'pendiente' | 'confirmada' | 'baja'
  notice: string
}

/** Mensaje que se enviaría (canal simulado). */
export interface AlertMessage {
  id: number
  subscription_id: number
  kind: 'codigo' | 'aviso'
  body: string
  category: string
  created_at: string
}

export interface AlertOutboxList {
  items: AlertMessage[]
  total: number
  notice: string
}
