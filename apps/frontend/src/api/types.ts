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
