/**
 * SCRUM-50 · Pantalla Mapa provincial
 *
 * Muestra acumulados de lluvia por estación sobre un mapa Leaflet de Formosa.
 * Reglas que no se rompen:
 *   - Un hueco no es 0 mm: se muestra como «sin dato».
 *   - Observado, referencia y estimado van separados: el selector no mezcla categorías.
 *   - No se inventan coordenadas: las estaciones sin lat/lon no se trazan.
 *   - Fecha de corte: FECHA_CORTE (31/10/2026).
 */
import 'leaflet/dist/leaflet.css'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { CircleMarker, GeoJSON, MapContainer, Popup, TileLayer, useMap } from 'react-leaflet'
import type { GeoJSONProps } from 'react-leaflet'
import { Link } from 'react-router-dom'
import type { FeatureCollection } from 'geojson'
import { ApiError, getAccumulated, getStations } from '../api/client'
import type { AccumulatedOut, AccumulatedStation, DataCategory, Station } from '../api/types'
import { Cargando, ErrorEstado } from '../components/Estados'
import { InsigniaAdvertencia, InsigniaCategoria } from '../components/Insignias'
import { FECHA_CORTE } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { colorMm, radiusMm, textoMmMapa } from './map-helpers'

const LIMITE_ESTACIONES = 200
const SIN_ESTACIONES: Station[] = []

// ---------------------------------------------------------------------------
// Fecha inicial
// ---------------------------------------------------------------------------

function restarDias(fecha: string, dias: number): string {
  const d = new Date(`${fecha}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() - dias)
  return d.toISOString().slice(0, 10)
}

const DESDE_INICIAL = restarDias(FECHA_CORTE, 29)

type StationWithCoordinates = Station & { lat: number; lon: number }

function tieneCoordenadas(station: Station): station is StationWithCoordinates {
  return station.lat != null && station.lon != null
}

function esFeatureCollection(value: unknown): value is FeatureCollection {
  if (typeof value !== 'object' || value === null) return false
  const collection = value as { type?: unknown; features?: unknown }
  return collection.type === 'FeatureCollection' && Array.isArray(collection.features)
}

async function cargarEstaciones(signal: AbortSignal): Promise<Station[]> {
  const primeraPagina = await getStations({ limit: LIMITE_ESTACIONES, offset: 0 }, signal)
  const estaciones = [...primeraPagina.items]
  let offset = estaciones.length

  while (offset < primeraPagina.total) {
    const pagina = await getStations({ limit: LIMITE_ESTACIONES, offset }, signal)
    if (pagina.items.length === 0) {
      throw new ApiError(
        0,
        'incomplete_station_page',
        'No se pudieron cargar todas las estaciones.',
      )
    }
    estaciones.push(...pagina.items)
    offset += pagina.items.length
  }

  return estaciones
}

function normalizarDepartamento(nombre: string): string {
  return nombre
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .trim()
    .toLowerCase()
}

function obtenerMaximosDepartamentales(
  estaciones: Station[],
  acumulados: Map<number, AccumulatedStation>,
): Map<string, number | null> {
  const maximos = new Map<string, number | null>()
  for (const station of estaciones) {
    if (!station.department) continue
    const key = normalizarDepartamento(station.department)
    const mm = acumulados.get(station.id)?.accumulated_mm
    const actual = maximos.get(key)
    if (!maximos.has(key) || (mm != null && (actual == null || mm > actual))) {
      maximos.set(key, mm ?? null)
    }
  }
  return maximos
}

// ---------------------------------------------------------------------------
// Popup de estación
// ---------------------------------------------------------------------------

interface PopupEstacionProps {
  station: Station
  acumulado: AccumulatedStation | undefined
  category: DataCategory
}

function PopupEstacion({ station, acumulado, category }: PopupEstacionProps) {
  return (
    <div className="mapa-popup">
      <strong>{station.name}</strong>
      <br />
      <InsigniaCategoria categoria={category} />
      <dl>
        <dt>Acumulado</dt>
        <dd>{textoMmMapa(acumulado?.accumulated_mm)}</dd>
        <dt>Fuente</dt>
        <dd>{station.source.name}</dd>
        <dt>Días con dato</dt>
        <dd>
          {acumulado != null
            ? `${acumulado.days_with_data} de ${acumulado.days_with_data + acumulado.days_without_data}`
            : '—'}
        </dd>
      </dl>
      {acumulado?.warnings.map((w) => (
        <InsigniaAdvertencia key={w.code} codigo={w.code} mensaje={w.message} />
      ))}
      <Link to={`/estacion/${station.id}`}>Ver serie completa →</Link>
    </div>
  )
}

interface ResumenDepartamentoProps {
  nombre: string
  estaciones: Station[]
  acumulados: Map<number, AccumulatedStation>
  category: DataCategory
  onCerrar: () => void
}

function ResumenDepartamento({
  nombre,
  estaciones,
  acumulados,
  category,
  onCerrar,
}: ResumenDepartamentoProps) {
  const relacionadas = estaciones.filter(
    (station) =>
      station.department &&
      normalizarDepartamento(station.department) === normalizarDepartamento(nombre),
  )
  const maximo = relacionadas.reduce<number | null>((actual, station) => {
    const mm = acumulados.get(station.id)?.accumulated_mm
    return mm != null && (actual == null || mm > actual) ? mm : actual
  }, null)

  return (
    <section
      className="mapa-resumen-departamento"
      aria-label={`Resumen del departamento ${nombre}`}
    >
      <div className="mapa-resumen-encabezado">
        <h3>Departamento: {nombre}</h3>
        <button type="button" onClick={onCerrar} aria-label="Cerrar resumen del departamento">
          Cerrar
        </button>
      </div>
      {relacionadas.length === 0 ? (
        <p className="nota">No hay estaciones con departamento verificado en el catálogo.</p>
      ) : (
        <>
          <p>
            <InsigniaCategoria categoria={category} /> Máximo individual entre estaciones con dato:{' '}
            <strong>{textoMmMapa(maximo)}</strong>. No es un total departamental.
          </p>
          <ul>
            {relacionadas.map((station) => {
              const acumulado = acumulados.get(station.id)
              return (
                <li key={station.id}>
                  <Link to={`/estacion/${station.id}`}>{station.name}</Link>
                  {' — '}
                  <InsigniaCategoria categoria={category} />
                  {' · Fuente: '}
                  {station.source.name}
                  {' · '}
                  {textoMmMapa(acumulado?.accumulated_mm)}
                  {acumulado?.warnings.map((warning) => (
                    <InsigniaAdvertencia
                      key={`${station.id}-${warning.code}`}
                      codigo={warning.code}
                      mensaje={warning.message}
                    />
                  ))}
                </li>
              )
            })}
          </ul>
        </>
      )}
    </section>
  )
}

// ---------------------------------------------------------------------------
// Capas GeoJSON de Formosa
// ---------------------------------------------------------------------------

interface CapaGeoJsonProps {
  path: string
  style: GeoJSONProps['style']
  onError: (path: string) => void
  onEachFeature?: GeoJSONProps['onEachFeature']
}

function CapaGeoJson({ path, style, onError, onEachFeature }: CapaGeoJsonProps) {
  const [data, setData] = useState<FeatureCollection | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetch(path, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`No se pudo cargar ${path}.`)
        return response.json()
      })
      .then((value: unknown) => {
        if (!esFeatureCollection(value)) throw new Error(`La capa ${path} no es válida.`)
        setData(value)
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === 'AbortError') return
        onError(path)
      })
    return () => controller.abort()
  }, [onError, path])

  return data ? (
    <GeoJSON key={path} data={data} style={style} onEachFeature={onEachFeature} />
  ) : null
}

const ESTILO_PROVINCIA = {
  color: '#0b4f8a',
  weight: 2,
  fillColor: '#e6f0fa',
  fillOpacity: 0.08,
}

const ESTILO_CURSOS_PERENNES = {
  color: '#1976d2',
  weight: 1.5,
  fillOpacity: 0,
}

const ESTILO_CURSOS_INTERMITENTES = {
  color: '#64b5f6',
  weight: 1,
  dashArray: '4 5',
  fillOpacity: 0,
}

interface CapasFormosaProps {
  onError: (path: string) => void
  estiloDepartamentos: GeoJSONProps['style']
  onSeleccionarDepartamento: NonNullable<GeoJSONProps['onEachFeature']>
}

function CapasFormosa({
  onError,
  estiloDepartamentos,
  onSeleccionarDepartamento,
}: CapasFormosaProps) {
  const map = useMap()

  useEffect(() => {
    map.setView([-24.5, -60.0], 6)
  }, [map])

  return (
    <>
      <CapaGeoJson
        path="/geo/formosa_provincia.geojson"
        style={ESTILO_PROVINCIA}
        onError={onError}
      />
      <CapaGeoJson
        path="/geo/formosa_departamentos.geojson"
        style={estiloDepartamentos}
        onError={onError}
        onEachFeature={onSeleccionarDepartamento}
      />
      <CapaGeoJson
        path="/geo/formosa_cursos_agua_perennes.geojson"
        style={ESTILO_CURSOS_PERENNES}
        onError={onError}
      />
      <CapaGeoJson
        path="/geo/formosa_cursos_agua_intermitentes.geojson"
        style={ESTILO_CURSOS_INTERMITENTES}
        onError={onError}
      />
    </>
  )
}

// ---------------------------------------------------------------------------
// Leyenda
// ---------------------------------------------------------------------------

function MapaLeyenda() {
  const entradas: { color: string; label: string; dashed?: boolean }[] = [
    { color: colorMm(null), label: 'Sin dato (trazo discontinuo; hueco ≠ 0 mm)', dashed: true },
    { color: colorMm(0), label: '0 mm (dato real)' },
    { color: colorMm(5), label: '< 10 mm' },
    { color: colorMm(20), label: '10–30 mm' },
    { color: colorMm(45), label: '30–60 mm' },
    { color: colorMm(80), label: '60–100 mm' },
    { color: colorMm(120), label: '≥ 100 mm' },
  ]
  return (
    <div className="mapa-leyenda" aria-label="Leyenda del mapa">
      {entradas.map(({ color, label, dashed }) => (
        <span key={label} className="mapa-leyenda-item">
          <span
            className={`mapa-leyenda-color${dashed ? ' mapa-leyenda-color-sin-dato' : ''}`}
            style={{ background: color }}
            aria-hidden="true"
          />
          {label}
        </span>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Pantalla principal
// ---------------------------------------------------------------------------

const CATEGORIAS: DataCategory[] = ['observado', 'referencia', 'estimado']
const LABEL_CATEGORIA: Record<DataCategory, string> = {
  observado: 'Observado',
  referencia: 'Referencia',
  estimado: 'Estimado',
}

export function Mapa() {
  const [desde, setDesde] = useState(DESDE_INICIAL)
  const [hasta, setHasta] = useState(FECHA_CORTE)
  const [category, setCategory] = useState<DataCategory>('observado')
  const [capasConError, setCapasConError] = useState<string[]>([])
  const [departamentoSeleccionado, setDepartamentoSeleccionado] = useState<string | null>(null)
  const informarErrorGeoJson = useCallback((path: string) => {
    setCapasConError((current) => (current.includes(path) ? current : [...current, path]))
  }, [])
  const seleccionarDepartamento = useCallback<NonNullable<GeoJSONProps['onEachFeature']>>(
    (feature, layer) => {
      const nombre = feature.properties?.nombre
      if (typeof nombre === 'string') {
        layer.on('click', () => setDepartamentoSeleccionado(nombre))
      }
    },
    [],
  )

  const { estado: estadoEstaciones, reintentar: reintEstaciones } = useAsync(
    (signal) => cargarEstaciones(signal),
    [],
  )

  const rangoValido = desde !== '' && hasta !== '' && desde <= hasta && hasta <= FECHA_CORTE
  const { estado: estadoAcum, reintentar: reintAcum } = useAsync<AccumulatedOut | null>(
    (signal) =>
      rangoValido
        ? getAccumulated({ from: desde, to: hasta, category }, signal)
        : Promise.resolve(null),
    [desde, hasta, category],
  )

  const acumulados = estadoAcum.tipo === 'listo' ? estadoAcum.datos : null
  const acumPorId = useMemo(
    () =>
      new Map<number, AccumulatedStation>(acumulados?.stations.map((s) => [s.station_id, s]) ?? []),
    [acumulados],
  )

  const listaEstaciones = estadoEstaciones.tipo === 'listo' ? estadoEstaciones.datos : null
  const estaciones = listaEstaciones ?? SIN_ESTACIONES
  const conCoordenadas = estaciones.filter(tieneCoordenadas)
  const sinCoordenadas = estaciones.filter((s) => !tieneCoordenadas(s))
  const maximosDepartamentales = useMemo(
    () => obtenerMaximosDepartamentales(estaciones, acumPorId),
    [acumPorId, estaciones],
  )
  const estiloDepartamentos: NonNullable<GeoJSONProps['style']> = useCallback(
    (feature) => {
      const nombre = feature?.properties?.nombre
      const maximo =
        typeof nombre === 'string'
          ? (maximosDepartamentales.get(normalizarDepartamento(nombre)) ?? null)
          : null
      return {
        color: '#455a64',
        weight: 1,
        fillColor: colorMm(maximo),
        fillOpacity: maximo == null ? 0.3 : 0.75,
        dashArray: maximo == null ? '3 3' : undefined,
      }
    },
    [maximosDepartamentales],
  )

  const isLoading =
    estadoEstaciones.tipo === 'cargando' || (rangoValido && estadoAcum.tipo === 'cargando')
  const errorMsg =
    estadoEstaciones.tipo === 'error'
      ? estadoEstaciones.mensaje
      : estadoAcum.tipo === 'error'
        ? estadoAcum.mensaje
        : null

  return (
    <section>
      <h2>Mapa provincial</h2>

      <form
        className="mapa-controles"
        onSubmit={(e) => e.preventDefault()}
        aria-label="Parámetros del mapa"
      >
        <label>
          Desde
          <input
            type="date"
            value={desde}
            max={hasta}
            onChange={(e) => setDesde(e.target.value)}
            aria-label="Fecha desde"
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            value={hasta}
            min={desde}
            max={FECHA_CORTE}
            onChange={(e) => setHasta(e.target.value)}
            aria-label="Fecha hasta"
          />
        </label>
        <label>
          Categoría
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as DataCategory)}
            aria-label="Categoría de dato"
          >
            {CATEGORIAS.map((c) => (
              <option key={c} value={c}>
                {LABEL_CATEGORIA[c]}
              </option>
            ))}
          </select>
        </label>
      </form>

      {!rangoValido && (
        <ErrorEstado
          mensaje={`Elegí un período válido: «Desde» no puede ser posterior a «Hasta» y ninguna fecha puede pasar del ${FECHA_CORTE}.`}
        />
      )}
      {isLoading && <Cargando />}
      {errorMsg && !isLoading && (
        <ErrorEstado
          mensaje={errorMsg}
          onReintentar={() => {
            reintEstaciones()
            reintAcum()
          }}
        />
      )}

      {acumulados?.clipped_to_cutoff && (
        <p className="nota" role="note">
          El período fue recortado a la fecha de corte ({acumulados.data_cutoff_date}).
        </p>
      )}

      <div
        className="mapa-contenedor"
        style={{ height: '500px', width: '100%' }}
        data-testid="mapa-contenedor"
      >
        <MapContainer
          center={[-24.5, -60.0]}
          zoom={6}
          style={{ height: '100%', width: '100%' }}
          scrollWheelZoom={false}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <CapasFormosa
            onError={informarErrorGeoJson}
            estiloDepartamentos={estiloDepartamentos}
            onSeleccionarDepartamento={seleccionarDepartamento}
          />

          {rangoValido &&
            conCoordenadas.map((station) => {
              const acum = acumPorId.get(station.id)
              const mm = acum?.accumulated_mm
              return (
                <CircleMarker
                  key={station.id}
                  center={[station.lat, station.lon]}
                  radius={radiusMm(mm)}
                  pathOptions={{
                    color: '#37474f',
                    weight: mm == null ? 2 : 1,
                    dashArray: mm == null ? '2 4' : undefined,
                    fillColor: colorMm(mm),
                    fillOpacity: mm == null ? 0.35 : 0.85,
                  }}
                  aria-label={`Estación ${station.name}: ${textoMmMapa(mm)}`}
                >
                  <Popup>
                    <PopupEstacion station={station} acumulado={acum} category={category} />
                  </Popup>
                </CircleMarker>
              )
            })}
        </MapContainer>
      </div>

      {capasConError.length > 0 && (
        <p className="nota" role="alert">
          No se pudieron cargar estas capas geográficas:{' '}
          {capasConError
            .map((path) => path.replace('/geo/', '').replace('.geojson', ''))
            .join(', ')}
          . El mapa de estaciones sigue disponible.
        </p>
      )}

      <MapaLeyenda />
      <p className="nota">
        El color de cada departamento representa el máximo acumulado individual de sus estaciones
        con dato; no es un total departamental. Los departamentos con trazo discontinuo no tienen
        acumulados disponibles.
      </p>

      {departamentoSeleccionado && (
        <ResumenDepartamento
          nombre={departamentoSeleccionado}
          estaciones={estaciones}
          acumulados={acumPorId}
          category={category}
          onCerrar={() => setDepartamentoSeleccionado(null)}
        />
      )}

      {estadoEstaciones.tipo === 'listo' && estaciones.length === 0 && (
        <p className="nota" role="status">
          No hay estaciones disponibles para mostrar.
        </p>
      )}

      {sinCoordenadas.length > 0 && (
        <details className="mapa-pendientes" data-testid="pendientes">
          <summary>
            {sinCoordenadas.length} estación{sinCoordenadas.length !== 1 ? 'es' : ''} sin
            coordenadas verificadas (no se muestran en el mapa)
          </summary>
          <ul>
            {sinCoordenadas.map((s) => {
              const acum = acumPorId.get(s.id)
              return (
                <li key={s.id}>
                  <Link to={`/estacion/${s.id}`}>{s.name}</Link>
                  {' — '}
                  <span className="nota">coordenadas pendientes</span>
                  {acum && (
                    <>
                      {' — '}
                      <InsigniaCategoria categoria={category} />
                      {' · Fuente: '}
                      {s.source.name}
                      {' · '}
                      {textoMmMapa(acum.accumulated_mm)}
                    </>
                  )}
                </li>
              )
            })}
          </ul>
        </details>
      )}

      {acumulados?.not_evaluated && acumulados.not_evaluated.length > 0 && (
        <p className="nota" role="note">
          No evaluadas en este período: {acumulados.not_evaluated.join(', ')}.
        </p>
      )}
    </section>
  )
}
