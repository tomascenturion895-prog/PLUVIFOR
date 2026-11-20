import { getRecurrence } from '../api/client'
import type { RecurrenceOut } from '../api/types'
import { FECHA_CORTE } from '../constants'
import { useAsync } from '../hooks/useAsync'
import { Cargando, ErrorEstado } from './Estados'
import { InsigniaAdvertencia, InsigniaCategoria } from './Insignias'

/** Los datos del SIGA/INTA empiezan en 2013: desde ahí se mira toda la historia disponible. */
export const HISTORIA_DESDE = '2013-01-01'

function anios(n: number): string {
  return `${n.toLocaleString('es-AR', { maximumFractionDigits: 1 })} ${n === 1 ? 'año' : 'años'}`
}

function Fila({
  umbral,
  eventos,
  cadaAnios,
  suficiente,
}: {
  umbral: number
  eventos: number
  cadaAnios: number | null
  suficiente: boolean
}) {
  let frecuencia = 'Sin eventos en el período observado'
  if (eventos > 0) {
    frecuencia =
      suficiente && cadaAnios !== null
        ? `En promedio, una vez cada ${anios(cadaAnios)}`
        : 'Historia insuficiente para calcular una frecuencia'
  }
  return (
    <tr>
      <th scope="row">{umbral} mm o más en un día</th>
      <td>{eventos}</td>
      <td>{frecuencia}</td>
    </tr>
  )
}

function Resultado({ r }: { r: RecurrenceOut }) {
  return (
    <>
      <p className="nota" role="note">
        {r.notice}
      </p>
      <p>
        Se miraron <strong>{r.valid_days.toLocaleString('es-AR')}</strong> días con dato válido (
        {anios(r.observed_years)}) entre {r.date_from} y {r.date_to}.{' '}
        <InsigniaCategoria categoria={r.category} />
      </p>
      {!r.sufficient_history && (
        <p role="status" className="nota">
          Hay menos de {anios(r.min_observed_years)} de dato válido: se informa cuántas veces
          ocurrió, pero <strong>no se calcula ninguna frecuencia</strong>.
        </p>
      )}
      {r.excluded_zero_run_days > 0 && (
        <p className="nota">
          {r.excluded_zero_run_days} días con dato quedaron afuera por estar dentro de una racha de
          ceros prolongada{' '}
          <InsigniaAdvertencia
            codigo="ceros_prolongados"
            mensaje="Puede ser un sensor sin registrar, no ausencia de lluvia. No se da por buena."
          />
          : pueden ser falsos ceros y no se cuentan.
        </p>
      )}
      <table className="tabla-dias">
        <caption className="nota">Días de lluvia intensa en el período observado</caption>
        <thead>
          <tr>
            <th scope="col">Umbral</th>
            <th scope="col">Veces</th>
            <th scope="col">Frecuencia pasada</th>
          </tr>
        </thead>
        <tbody>
          <Fila
            umbral={50}
            eventos={r.ge50}
            cadaAnios={r.ge50_every_years}
            suficiente={r.sufficient_history}
          />
          <Fila
            umbral={100}
            eventos={r.ge100}
            cadaAnios={r.ge100_every_years}
            suficiente={r.sufficient_history}
          />
        </tbody>
      </table>
      <p className="nota">
        {r.gap_days.toLocaleString('es-AR')} días sin dato en el período: no se cuentan como lluvia
        ni como días secos.
      </p>
      <details>
        <summary>Cantidad por año</summary>
        <table className="tabla-dias">
          <thead>
            <tr>
              <th scope="col">Año</th>
              <th scope="col">Días con dato</th>
              <th scope="col">≥ 50 mm</th>
              <th scope="col">≥ 100 mm</th>
            </tr>
          </thead>
          <tbody>
            {r.by_year.map((y) => (
              <tr key={y.year}>
                <th scope="row">{y.year}</th>
                <td>{y.valid_days}</td>
                <td>{y.ge50}</td>
                <td>{y.ge100}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </details>
    </>
  )
}

/** Cada cuánto llovió fuerte en la estación, mirando todo su histórico. No predice nada. */
export default function Recurrencia({ stationId }: { stationId: number }) {
  const { estado, reintentar } = useAsync(
    (signal) => getRecurrence({ stationId, from: HISTORIA_DESDE, to: FECHA_CORTE }, signal),
    [stationId],
  )
  return (
    <section aria-labelledby="titulo-recurrencia">
      <h3 id="titulo-recurrencia">Recurrencia histórica de lluvia intensa</h3>
      {estado.tipo === 'cargando' && <Cargando />}
      {estado.tipo === 'error' && (
        <ErrorEstado mensaje={estado.mensaje} onReintentar={reintentar} />
      )}
      {estado.tipo === 'listo' && <Resultado r={estado.datos} />}
    </section>
  )
}
