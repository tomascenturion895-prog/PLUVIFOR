import { useState, type FormEvent } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { ApiError, getCompare, getStations } from '../api/client'
import type { SeriesCompare } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import { InsigniaAdvertencia, InsigniaCategoria } from '../components/Insignias'
import { textoMm } from '../components/insignias-datos'
import { esDaltonico } from '../components/tema/tema-colores'
import { FECHA_CORTE, MAX_ESTACIONES_COMPARADOR } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { useIdioma } from '../i18n/usar-idioma'
import { alinearSeries, claveDe, diferenciaCobertura } from './compare-datos'

const COLORES_BASE = ['#f05514', '#0284c7', '#16a34a', '#8b5cf6']
// Daltónico: Okabe-Ito; además cada serie tiene un trazo distinto (ver temas.css).
const COLORES_DALTONICO = ['#56b4e9', '#e69f00', '#cc79a7', '#f0e442']
const COLORES = {
  get length() {
    return COLORES_BASE.length
  },
  at(i: number) {
    return (esDaltonico() ? COLORES_DALTONICO : COLORES_BASE)[i]
  },
}

function restarDias(fecha: string, dias: number): string {
  const d = new Date(`${fecha}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() - dias)
  return d.toISOString().slice(0, 10)
}

function Resultado({ datos }: { datos: SeriesCompare }) {
  const { t } = useIdioma()
  const filas = alinearSeries(datos.stations)
  const dif = diferenciaCobertura(datos.stations)
  return (
    <article aria-label={t('comparador.resultadoAria')}>
      <p className="metadatos">
        <InsigniaCategoria categoria={datos.category} />{' '}
        <span>
          {datos.date_from} – {datos.date_to} · {datos.data_cutoff_date}
        </span>
      </p>
      {datos.comparability_warnings.length > 0 ? (
        <ul className="advertencias" aria-label={t('comparador.advertenciasAria')}>
          {datos.comparability_warnings.map((w) => (
            <li key={`${w.code}-${w.start_date ?? ''}`}>
              <InsigniaAdvertencia codigo={w.code} mensaje={w.message} />
            </li>
          ))}
        </ul>
      ) : (
        <p className="nota">{t('comparador.sinAdvertencias')}</p>
      )}
      {datos.not_evaluated.length > 0 && (
        <details>
          <summary>{t('comparador.noEvaluadas')}</summary>
          <ul>
            {datos.not_evaluated.map((n) => (
              <li key={n.code}>{n.reason}</li>
            ))}
          </ul>
        </details>
      )}
      <figure className="grafico">
        <figcaption>
          Lluvia diaria (mm) con escala común. Donde la línea se corta hay un día{' '}
          <strong>sin dato</strong>: no significa 0 mm.
        </figcaption>
        <div className="grafico-area" role="img" aria-label="Gráfico de líneas de las series">
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={filas} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="fecha" minTickGap={32} tick={{ fontSize: 11 }} />
              <YAxis width={36} tick={{ fontSize: 11 }} unit=" mm" />
              <Tooltip />
              <Legend />
              {datos.stations.map((e, i) => (
                <Line
                  key={e.station_id}
                  className={`serie-linea serie-linea-${i % COLORES.length}`}
                  type="linear"
                  dataKey={claveDe(e.station_id)}
                  name={e.station_name}
                  stroke={COLORES.at(i % COLORES.length)}
                  dot={false}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </figure>
      <table className="tabla-dias">
        <caption className="nota">
          Cobertura de cada estación (diferencia entre la mayor y la menor: {dif} puntos). Los
          acumulados no se suman entre estaciones.
        </caption>
        <thead>
          <tr>
            <th scope="col">Estación</th>
            <th scope="col">Acumulado</th>
            <th scope="col">Días con dato</th>
            <th scope="col">Sin dato</th>
            <th scope="col">Cobertura</th>
          </tr>
        </thead>
        <tbody>
          {datos.stations.map((e) => (
            <tr key={e.station_id}>
              <th scope="row">{e.station_name}</th>
              <td>{textoMm(e.summary.accumulated_mm)}</td>
              <td>
                {e.summary.days_with_data} de {e.summary.days_in_period}
              </td>
              <td>{e.summary.days_sin_fila + e.summary.days_fila_sin_valor}</td>
              <td>{Math.round(e.summary.coverage * 100)} %</td>
            </tr>
          ))}
        </tbody>
      </table>
    </article>
  )
}

export default function Compare() {
  const estaciones = useAsync((signal) => getStations({ limit: 200 }, signal), [])
  const [elegidas, setElegidas] = useState<number[]>([])
  const [desde, setDesde] = useState(restarDias(FECHA_CORTE, 89))
  const [hasta, setHasta] = useState(FECHA_CORTE)
  const [datos, setDatos] = useState<SeriesCompare | null>(null)
  const [cargando, setCargando] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const rangoValido = desde !== '' && hasta !== '' && desde <= hasta && hasta <= FECHA_CORTE
  const puede = elegidas.length >= 2 && rangoValido && !cargando

  function alternar(id: number) {
    setElegidas((a) =>
      a.includes(id)
        ? a.filter((x) => x !== id)
        : a.length < MAX_ESTACIONES_COMPARADOR
          ? [...a, id]
          : a,
    )
  }

  async function comparar(evento: FormEvent) {
    evento.preventDefault()
    if (!puede) return
    setCargando(true)
    setError(null)
    try {
      setDatos(await getCompare({ stationIds: elegidas, from: desde, to: hasta }))
    } catch (e) {
      setDatos(null)
      setError(e instanceof ApiError ? e.message : 'Ocurrió un error inesperado.')
    } finally {
      setCargando(false)
    }
  }

  return (
    <section>
      <h2>Comparador</h2>
      <p>
        Elegí de 2 a {MAX_ESTACIONES_COMPARADOR} estaciones y un período. Cada comparación trae sus
        advertencias: dos series no siempre se pueden comparar de igual a igual.
      </p>
      <form className="filtros" onSubmit={(e) => void comparar(e)}>
        <fieldset className="estaciones-lista">
          <legend>Estaciones (de 2 a {MAX_ESTACIONES_COMPARADOR})</legend>
          {estaciones.estado.tipo === 'cargando' && <Cargando />}
          {estaciones.estado.tipo === 'error' && (
            <ErrorEstado mensaje={estaciones.estado.mensaje} onReintentar={estaciones.reintentar} />
          )}
          {estaciones.estado.tipo === 'listo' &&
            (estaciones.estado.datos.items.length === 0 ? (
              <Vacio>No hay estaciones cargadas.</Vacio>
            ) : (
              estaciones.estado.datos.items.map((s) => (
                <label key={s.id} className="opcion">
                  <input
                    type="checkbox"
                    checked={elegidas.includes(s.id)}
                    onChange={() => alternar(s.id)}
                  />
                  {s.name} ({s.code})
                </label>
              ))
            ))}
        </fieldset>
        <label>
          Desde
          <input
            type="date"
            value={desde}
            max={FECHA_CORTE}
            onChange={(e) => setDesde(e.target.value)}
          />
        </label>
        <label>
          Hasta
          <input
            type="date"
            value={hasta}
            max={FECHA_CORTE}
            onChange={(e) => setHasta(e.target.value)}
          />
        </label>
        <div className="acciones">
          <button type="submit" disabled={!puede}>
            Comparar
          </button>
        </div>
      </form>
      {elegidas.length === 1 && (
        <p className="nota">Elegí al menos una estación más para comparar.</p>
      )}
      {!rangoValido && (
        <ErrorEstado
          mensaje={`Elegí un período válido: «Desde» no puede ser posterior a «Hasta» y ninguna fecha puede pasar del ${FECHA_CORTE}.`}
        />
      )}
      {cargando && <Cargando texto="Comparando…" />}
      {error && <ErrorEstado mensaje={error} />}
      {datos && <Resultado datos={datos} />}
    </section>
  )
}
