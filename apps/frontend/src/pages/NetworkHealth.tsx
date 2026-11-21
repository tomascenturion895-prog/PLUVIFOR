import { getNetworkHealth } from '../api/client'
import type { StationHealth } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import LecturasSimuladas from '../components/LecturasSimuladas'
import { useAsync } from '../hooks/useAsync'
import { useIdioma } from '../i18n/usar-idioma'
import { fechaLegible, formatoMm, TEXTO_ESTADO } from './network-health-datos'

function UltimaLectura({ estacion }: { estacion: StationHealth }) {
  const { t } = useIdioma()
  if (estacion.last_reading_date === null || estacion.last_reading_mm === null) {
    return <>{t('salud.sinLecturas')}</>
  }
  const dias = estacion.days_since_last
  return (
    <>
      {fechaLegible(estacion.last_reading_date)} · {formatoMm(estacion.last_reading_mm)}
      {dias !== null && <span className="nota"> (hace {dias} días)</span>}
    </>
  )
}

export default function NetworkHealth() {
  const { t } = useIdioma()
  const { estado, reintentar } = useAsync((signal) => getNetworkHealth({}, signal), [])

  return (
    <section>
      <h2>{t('nav.salud')}</h2>
      <p>{t('salud.intro')}</p>
      {estado.tipo === 'cargando' && <Cargando />}
      {estado.tipo === 'error' && (
        <ErrorEstado mensaje={estado.mensaje} onReintentar={reintentar} />
      )}
      {estado.tipo === 'listo' &&
        (estado.datos.stations.length === 0 ? (
          <Vacio>{t('comun.sinEstaciones')}</Vacio>
        ) : (
          <>
            <ul className="resumen" aria-label={t('salud.resumenAria')}>
              <li>
                <strong>{estado.datos.active}</strong> {t('salud.activas')}
              </li>
              <li>
                <strong>{estado.datos.silent}</strong> {t('salud.enSilencio')}
              </li>
              <li>
                <strong>{estado.datos.no_data}</strong> {t('salud.sinDatos')}
              </li>
            </ul>
            <p className="nota">
              Se marca «en silencio» a la estación cuya última lectura con valor es de hace más de{' '}
              {estado.datos.silent_after_days} días respecto de la fecha de corte (
              {fechaLegible(estado.datos.data_cutoff_date)}). Son datos observados: no se mezclan
              con referencias ni estimados.
            </p>
            <div
              className="tabla-scroll"
              role="region"
              tabIndex={0}
              aria-label={t('salud.tablaCaption')}
            >
              <table className="tabla-dias">
                <caption className="nota">{t('salud.tablaCaption')}</caption>
                <thead>
                  <tr>
                    <th scope="col">{t('comun.estacion')}</th>
                    <th scope="col">{t('comun.zona')}</th>
                    <th scope="col">{t('comun.estado')}</th>
                    <th scope="col">{t('salud.ultimaLectura')}</th>
                  </tr>
                </thead>
                <tbody>
                  {estado.datos.stations.map((s) => (
                    <tr key={s.station_id}>
                      <th scope="row">
                        {s.name} ({s.code})
                      </th>
                      <td>{s.zone ?? t('comun.sinDato')}</td>
                      <td>
                        <span
                          className={`marca-estado marca-estado-${s.state}`}
                          aria-hidden="true"
                        />
                        {TEXTO_ESTADO[s.state]}
                      </td>
                      <td>
                        <UltimaLectura estacion={s} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ))}
      <LecturasSimuladas />
    </section>
  )
}
