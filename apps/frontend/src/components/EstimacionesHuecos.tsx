import { getEstimates } from '../api/client'
import type { GapEstimate } from '../api/types'
import { useAsync } from '../hooks/useAsync'
import { Cargando, ErrorEstado } from './Estados'
import { InsigniaCategoria, InsigniaEstado } from './Insignias'

const NOMBRE_METODO: Record<string, string> = {
  vecinas_idw_v1: 'Vecinas cercanas ponderadas por distancia',
  chirps_v3_punto: 'CHIRPS v3 en el punto de la estación',
}

function nombreMetodo(metodo: string): string {
  return NOMBRE_METODO[metodo] ?? metodo
}

function formatoMm(mm: number): string {
  return `${mm.toLocaleString('es-AR', { maximumFractionDigits: 1 })} mm`
}

function Base({ e }: { e: GapEstimate }) {
  const vecinas = e.detail.vecinas ?? []
  if (vecinas.length === 0) return <>{nombreMetodo(e.method)}</>
  return (
    <>
      {nombreMetodo(e.method)}:{' '}
      {vecinas
        .map((v) => `${v.name} (${v.distance_km.toLocaleString('es-AR')} km, ${formatoMm(v.mm)})`)
        .join('; ')}
    </>
  )
}

/**
 * Días SIN DATO que tienen un valor estimado (SCRUM-93). Va separado de la serie observada: no se
 * suma al acumulado ni cambia el estado del día, que sigue siendo «sin dato».
 */
export default function EstimacionesHuecos({
  stationId,
  desde,
  hasta,
}: {
  stationId: number
  desde: string
  hasta: string
}) {
  const { estado, reintentar } = useAsync(
    (signal) => getEstimates({ stationId, from: desde, to: hasta, limit: 200 }, signal),
    [stationId, desde, hasta],
  )

  return (
    <section aria-labelledby="titulo-estimaciones">
      <h4 id="titulo-estimaciones">Días sin dato con valor estimado</h4>
      {estado.tipo === 'cargando' && <Cargando />}
      {estado.tipo === 'error' && (
        <ErrorEstado mensaje={estado.mensaje} onReintentar={reintentar} />
      )}
      {estado.tipo === 'listo' && (
        <>
          <p className="nota" role="note">
            {estado.datos.notice}
          </p>
          {estado.datos.items.length === 0 ? (
            <p className="nota">
              No hay días estimados en este período: los días sin dato siguen sin dato.
            </p>
          ) : (
            <div
              className="tabla-scroll"
              role="region"
              aria-label="Tabla de días estimados"
              tabIndex={0}
            >
              <table className="tabla-dias">
                <caption className="nota">
                  {estado.datos.items.length} de {estado.datos.total} días estimados (no suman al
                  acumulado observado)
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Fecha</th>
                    <th scope="col">Valor estimado</th>
                    <th scope="col">Día observado</th>
                    <th scope="col">Categoría</th>
                    <th scope="col">Base del cálculo</th>
                  </tr>
                </thead>
                <tbody>
                  {estado.datos.items.map((e) => (
                    <tr key={`${e.station_id}-${e.obs_date}`}>
                      <th scope="row">{e.obs_date}</th>
                      <td>{formatoMm(e.mm)}</td>
                      <td>
                        <InsigniaEstado estado={e.gap_state} />
                      </td>
                      <td>
                        <InsigniaCategoria categoria={e.category} />
                      </td>
                      <td>
                        <Base e={e} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  )
}
