import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getRainfall, getStations } from '../api/client'
import type { Series } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import { InsigniaAdvertencia, InsigniaCategoria, InsigniaEstado } from '../components/Insignias'
import { textoMm } from '../components/insignias-datos'
import SerieDiaria from '../components/SerieDiaria'
import { FECHA_CORTE } from '../constants'
import { useAsync } from '../hooks/useAsync'

function restarDias(fecha: string, dias: number): string {
  const d = new Date(`${fecha}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() - dias)
  return d.toISOString().slice(0, 10)
}

const DESDE_INICIAL = restarDias(FECHA_CORTE, 89)

export function Resumen({ serie }: { serie: Series }) {
  const { summary } = serie
  return (
    <dl className="resumen">
      <div>
        <dt>Acumulado del período</dt>
        <dd>{textoMm(summary.accumulated_mm)}</dd>
      </div>
      <div>
        <dt>Días con dato</dt>
        <dd>
          {summary.days_with_data} de {summary.days_in_period}
        </dd>
      </div>
      <div>
        <dt>Sin dato (sin fila)</dt>
        <dd>{summary.days_sin_fila}</dd>
      </div>
      <div>
        <dt>Fila sin valor</dt>
        <dd>{summary.days_fila_sin_valor}</dd>
      </div>
      <div>
        <dt>Cobertura</dt>
        <dd>{Math.round(summary.coverage * 100)} %</dd>
      </div>
    </dl>
  )
}

function Serie({ serie }: { serie: Series }) {
  return (
    <>
      <h3>{serie.station_name}</h3>
      <p className="metadatos">
        <InsigniaCategoria categoria={serie.category} />{' '}
        <span>
          Fuente: {serie.source.name} ({serie.source.network})
        </span>
      </p>
      {serie.clipped_to_cutoff && (
        <p className="nota">
          El período se recortó a la fecha de corte ({serie.data_cutoff_date}).
        </p>
      )}
      <Resumen serie={serie} />
      {serie.warnings.length > 0 && (
        <section aria-labelledby="advertencias">
          <h4 id="advertencias">Advertencias de calidad</h4>
          <ul className="advertencias">
            {serie.warnings.map((w) => (
              <li key={`${w.code}-${w.start_date ?? ''}`}>
                <InsigniaAdvertencia codigo={w.code} mensaje={w.message} />
                <p>{w.message}</p>
              </li>
            ))}
          </ul>
        </section>
      )}
      <SerieDiaria days={serie.days} />
      <details>
        <summary>Ver tabla de días</summary>
        <table className="tabla-dias">
          <thead>
            <tr>
              <th scope="col">Fecha</th>
              <th scope="col">Lluvia</th>
              <th scope="col">Estado</th>
            </tr>
          </thead>
          <tbody>
            {serie.days.map((d) => (
              <tr key={d.obs_date}>
                <td>{d.obs_date}</td>
                <td>{textoMm(d.state === 'dato' ? d.mm : null)}</td>
                <td>
                  <InsigniaEstado estado={d.state} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  )
}

export default function Estacion() {
  const { id } = useParams()
  const navigate = useNavigate()
  const stationId = id !== undefined && /^\d+$/.test(id) ? Number(id) : null
  const [desde, setDesde] = useState(DESDE_INICIAL)
  const [hasta, setHasta] = useState(FECHA_CORTE)

  const estaciones = useAsync((signal) => getStations({ limit: 200 }, signal), [])
  const rangoValido = desde !== '' && hasta !== '' && desde <= hasta && hasta <= FECHA_CORTE
  const serie = useAsync(
    (signal) =>
      stationId !== null && rangoValido
        ? getRainfall({ stationId, from: desde, to: hasta }, signal)
        : Promise.resolve(null),
    [stationId, desde, hasta, rangoValido],
  )

  return (
    <section>
      <h2>Estación</h2>
      <form className="filtros" onSubmit={(e) => e.preventDefault()}>
        <label>
          Estación
          <select
            value={stationId ?? ''}
            onChange={(e) => navigate(e.target.value ? `/estacion/${e.target.value}` : '/estacion')}
            disabled={estaciones.estado.tipo !== 'listo'}
          >
            <option value="">Elegí una estación</option>
            {estaciones.estado.tipo === 'listo' &&
              estaciones.estado.datos.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.code})
                </option>
              ))}
          </select>
        </label>
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
      </form>
      <p className="nota">Los datos llegan hasta el {FECHA_CORTE} (fecha de corte).</p>

      {estaciones.estado.tipo === 'error' && (
        <ErrorEstado mensaje={estaciones.estado.mensaje} onReintentar={estaciones.reintentar} />
      )}
      {!rangoValido && (
        <ErrorEstado
          mensaje={`Elegí un período válido: «Desde» no puede ser posterior a «Hasta» y ninguna fecha puede pasar del ${FECHA_CORTE}.`}
        />
      )}
      {rangoValido && stationId === null && <Vacio>Elegí una estación para ver su lluvia.</Vacio>}
      {rangoValido && stationId !== null && serie.estado.tipo === 'cargando' && <Cargando />}
      {rangoValido && stationId !== null && serie.estado.tipo === 'error' && (
        <ErrorEstado mensaje={serie.estado.mensaje} onReintentar={serie.reintentar} />
      )}
      {rangoValido && stationId !== null && serie.estado.tipo === 'listo' && serie.estado.datos && (
        <Serie serie={serie.estado.datos} />
      )}
    </section>
  )
}
