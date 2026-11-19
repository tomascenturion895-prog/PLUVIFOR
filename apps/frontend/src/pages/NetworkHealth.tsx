import { getNetworkHealth } from '../api/client'
import type { NetworkState, StationHealth } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import { useAsync } from '../hooks/useAsync'
import { fechaLegible, formatoMm, TEXTO_ESTADO } from './network-health-datos'

const SIMBOLO: Record<NetworkState, string> = { activa: '●', en_silencio: '◐', sin_datos: '○' }

function UltimaLectura({ estacion }: { estacion: StationHealth }) {
  if (estacion.last_reading_date === null || estacion.last_reading_mm === null) {
    return <>Sin lecturas</>
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
  const { estado, reintentar } = useAsync((signal) => getNetworkHealth({}, signal), [])

  return (
    <section>
      <h2>Salud de la red</h2>
      <p>
        Qué estaciones siguen reportando y cuáles dejaron de hacerlo. Una estación en silencio no
        tiene «0 mm»: tiene sin dato.
      </p>
      {estado.tipo === 'cargando' && <Cargando />}
      {estado.tipo === 'error' && (
        <ErrorEstado mensaje={estado.mensaje} onReintentar={reintentar} />
      )}
      {estado.tipo === 'listo' &&
        (estado.datos.stations.length === 0 ? (
          <Vacio>No hay estaciones cargadas.</Vacio>
        ) : (
          <>
            <ul className="resumen" aria-label="Resumen de la red">
              <li>
                <strong>{estado.datos.active}</strong> activas
              </li>
              <li>
                <strong>{estado.datos.silent}</strong> en silencio
              </li>
              <li>
                <strong>{estado.datos.no_data}</strong> sin datos
              </li>
            </ul>
            <p className="nota">
              Se marca «en silencio» a la estación cuya última lectura con valor es de hace más de{' '}
              {estado.datos.silent_after_days} días respecto de la fecha de corte (
              {fechaLegible(estado.datos.data_cutoff_date)}). Son datos observados: no se mezclan
              con referencias ni estimados.
            </p>
            <table className="tabla-dias">
              <caption className="nota">Estado de cada estación</caption>
              <thead>
                <tr>
                  <th scope="col">Estación</th>
                  <th scope="col">Zona</th>
                  <th scope="col">Estado</th>
                  <th scope="col">Última lectura</th>
                </tr>
              </thead>
              <tbody>
                {estado.datos.stations.map((s) => (
                  <tr key={s.station_id}>
                    <th scope="row">
                      {s.name} ({s.code})
                    </th>
                    <td>{s.zone ?? 'Sin dato'}</td>
                    <td>
                      <span aria-hidden="true">{SIMBOLO[s.state]} </span>
                      {TEXTO_ESTADO[s.state]}
                    </td>
                    <td>
                      <UltimaLectura estacion={s} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </>
        ))}
    </section>
  )
}
