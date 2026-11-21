import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getNetworkHealth, getRainfall, getStations } from '../api/client'
import type { Series } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import { InsigniaAdvertencia, InsigniaCategoria, InsigniaEstado } from '../components/Insignias'
import { textoMm } from '../components/insignias-datos'
import Destacados from '../components/Destacados'
import Recurrencia from '../components/Recurrencia'
import EstimacionesHuecos from '../components/EstimacionesHuecos'
import SerieDiaria from '../components/SerieDiaria'
import { FECHA_CORTE } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { useIdioma } from '../i18n/usar-idioma'

function restarDias(fecha: string, dias: number): string {
  const d = new Date(`${fecha}T00:00:00Z`)
  d.setUTCDate(d.getUTCDate() - dias)
  return d.toISOString().slice(0, 10)
}

const DIAS_PERIODO = 90
const DESDE_INICIAL = restarDias(FECHA_CORTE, DIAS_PERIODO - 1)

/**
 * Cuando el período no tiene ni un día con dato, ofrece ir al último período que sí lo tiene.
 * La fecha sale de la última lectura de la estación; si no hay, no se inventa ninguna.
 */
function UltimoDato({
  stationId,
  onIr,
}: {
  stationId: number
  onIr: (desde: string, hasta: string) => void
}) {
  const salud = useAsync((signal) => getNetworkHealth({}, signal), [])
  if (salud.estado.tipo !== 'listo') return null
  const ultima = salud.estado.datos.stations.find((s) => s.station_id === stationId)
  if (!ultima?.last_reading_date) {
    return <p className="nota">Esta estación no tiene ninguna lectura cargada.</p>
  }
  const hasta = ultima.last_reading_date
  return (
    <p className="nota">
      Sin dato en este período: no significa 0 mm. La última lectura de esta estación es del {hasta}
      .{' '}
      <button type="button" onClick={() => onIr(restarDias(hasta, DIAS_PERIODO - 1), hasta)}>
        Ver el último período con dato
      </button>
    </p>
  )
}

export function Resumen({ serie }: { serie: Series }) {
  const { t } = useIdioma()
  const { summary } = serie
  return (
    <dl className="resumen">
      <div>
        <dt>{t('estacion.acumuladoPeriodo')}</dt>
        <dd>{textoMm(summary.accumulated_mm)}</dd>
      </div>
      <div>
        <dt>{t('estacion.diasConDato')}</dt>
        <dd>
          {summary.days_with_data} {t('comun.de')} {summary.days_in_period}
        </dd>
      </div>
      <div>
        <dt>{t('estacion.sinDatoSinFila')}</dt>
        <dd>{summary.days_sin_fila}</dd>
      </div>
      <div>
        <dt>{t('estacion.filaSinValor')}</dt>
        <dd>{summary.days_fila_sin_valor}</dd>
      </div>
      <div>
        <dt>{t('comun.cobertura')}</dt>
        <dd>{Math.round(summary.coverage * 100)} %</dd>
      </div>
    </dl>
  )
}

function Serie({
  serie,
  desde,
  hasta,
  onIrAlPeriodo,
}: {
  serie: Series
  desde: string
  hasta: string
  onIrAlPeriodo: (desde: string, hasta: string) => void
}) {
  const { t } = useIdioma()
  return (
    <>
      <h3>{serie.station_name}</h3>
      <p className="metadatos">
        <InsigniaCategoria categoria={serie.category} />{' '}
        <span>
          {t('comun.fuente')}: {serie.source.name} ({serie.source.network})
        </span>
      </p>
      {serie.clipped_to_cutoff && (
        <p className="nota">
          El período se recortó a la fecha de corte ({serie.data_cutoff_date}).
        </p>
      )}
      <Resumen serie={serie} />
      {serie.summary.days_with_data === 0 && (
        <UltimoDato stationId={serie.station_id} onIr={onIrAlPeriodo} />
      )}
      {serie.warnings.length > 0 && (
        <section aria-labelledby="advertencias">
          <h4 id="advertencias">{t('estacion.advertenciasCalidad')}</h4>
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
        <summary>{t('estacion.verTablaDias')}</summary>
        <table className="tabla-dias">
          <thead>
            <tr>
              <th scope="col">{t('comun.fecha')}</th>
              <th scope="col">{t('comun.lluvia')}</th>
              <th scope="col">{t('comun.estado')}</th>
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
      <Destacados stationId={serie.station_id} desde={desde} hasta={hasta} />
      <Recurrencia stationId={serie.station_id} />
      <EstimacionesHuecos stationId={serie.station_id} desde={desde} hasta={hasta} />
    </>
  )
}

export default function Estacion() {
  const { t } = useIdioma()
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
      <h2>{t('nav.estacion')}</h2>
      <form className="filtros" onSubmit={(e) => e.preventDefault()}>
        <label>
          {t('comun.estacion')}
          <select
            value={stationId ?? ''}
            onChange={(e) => navigate(e.target.value ? `/estacion/${e.target.value}` : '/estacion')}
            disabled={estaciones.estado.tipo !== 'listo'}
          >
            <option value="">{t('comun.elegirEstacion')}</option>
            {estaciones.estado.tipo === 'listo' &&
              estaciones.estado.datos.items.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name} ({s.code})
                </option>
              ))}
          </select>
        </label>
        <label>
          {t('comun.desde')}
          <input
            type="date"
            value={desde}
            max={FECHA_CORTE}
            onChange={(e) => setDesde(e.target.value)}
          />
        </label>
        <label>
          {t('comun.hasta')}
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
        <Serie
          serie={serie.estado.datos}
          desde={desde}
          hasta={hasta}
          onIrAlPeriodo={(d, h) => {
            setDesde(d)
            setHasta(h)
          }}
        />
      )}
    </section>
  )
}
