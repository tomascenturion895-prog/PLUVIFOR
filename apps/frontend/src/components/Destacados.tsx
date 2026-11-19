import { getClimateReference, getEvents } from '../api/client'
import type { ClimateReferenceOut, DryStreak, EventsStation } from '../api/types'
import { useAsync } from '../hooks/useAsync'
import { Cargando, ErrorEstado } from './Estados'
import { InsigniaAdvertencia, InsigniaCategoria } from './Insignias'

const MESES = [
  'enero',
  'febrero',
  'marzo',
  'abril',
  'mayo',
  'junio',
  'julio',
  'agosto',
  'septiembre',
  'octubre',
  'noviembre',
  'diciembre',
]

function dias(n: number): string {
  return `${n} día${n === 1 ? '' : 's'}`
}

function mm(valor: number): string {
  return `${valor.toLocaleString('es-AR', { maximumFractionDigits: 1 })} mm`
}

function Racha({ racha }: { racha: DryStreak }) {
  return (
    <>
      {dias(racha.days)} seguidos con dato y 0 mm ({racha.start_date} al {racha.end_date})
      {racha.zero_run_warning && (
        <>
          {' '}
          <InsigniaAdvertencia
            codigo="ceros_prolongados"
            mensaje="Puede ser un sensor sin registrar, no ausencia de lluvia. No se da por buena."
          />
        </>
      )}
    </>
  )
}

/** Lo que llama la atención del período, solo descriptivo. Un día sin dato no es un día seco. */
export function ResumenDestacados({ e }: { e: EventsStation }) {
  return (
    <ul className="destacados-lista">
      <li>
        <strong>50 mm o más:</strong> {dias(e.days_50mm_or_more.length)}
        {e.days_50mm_or_more.length > 0 && (
          <details>
            <summary>Ver fechas</summary>
            <ul>
              {e.days_50mm_or_more.map((d) => (
                <li key={d.obs_date}>
                  {d.obs_date}: {mm(d.mm)}
                </li>
              ))}
            </ul>
          </details>
        )}
      </li>
      <li>
        <strong>100 mm o más:</strong> {dias(e.days_100mm_or_more.length)}
        {e.days_100mm_or_more.length > 0 && (
          <details>
            <summary>Ver fechas</summary>
            <ul>
              {e.days_100mm_or_more.map((d) => (
                <li key={d.obs_date}>
                  {d.obs_date}: {mm(d.mm)}
                </li>
              ))}
            </ul>
          </details>
        )}
      </li>
      <li>
        <strong>Racha seca más larga:</strong>{' '}
        {e.longest_dry_streak ? (
          <Racha racha={e.longest_dry_streak} />
        ) : (
          'ninguna con dato en el período'
        )}
      </li>
    </ul>
  )
}

function Normal({ r }: { r: ClimateReferenceOut }) {
  if (r.normals.length === 0) {
    return (
      <p className="nota">
        No hay normal mensual cargada para esta estación (no es 0 mm: es que falta la fuente).
      </p>
    )
  }
  return (
    <>
      {r.normals.map((n) => (
        <div
          key={n.period}
          className="tabla-scroll"
          role="region"
          tabIndex={0}
          aria-label={`Normal ${n.period}`}
        >
          <table className="tabla-dias">
            <caption className="nota">
              Normal mensual {n.period} <InsigniaCategoria categoria="referencia" />.{' '}
              {n.source_note}
            </caption>
            <thead>
              <tr>
                <th scope="col">Mes</th>
                <th scope="col">Normal</th>
              </tr>
            </thead>
            <tbody>
              {n.months.map((m) => (
                <tr key={m.month}>
                  <th scope="row">{MESES[m.month - 1] ?? m.month}</th>
                  <td>{mm(m.normal_mm)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
      <p className="nota">{r.notice}</p>
    </>
  )
}

export default function Destacados({
  stationId,
  desde,
  hasta,
  compacto = false,
}: {
  stationId: number
  desde: string
  hasta: string
  /** En el popup del mapa: solo el resumen, sin la normal mensual. */
  compacto?: boolean
}) {
  const { estado, reintentar } = useAsync(
    (signal) => getEvents({ stationId, from: desde, to: hasta }, signal),
    [stationId, desde, hasta],
  )
  const normal = useAsync(
    (signal) => (compacto ? Promise.resolve(null) : getClimateReference(stationId, signal)),
    [stationId, compacto],
  )

  return (
    <section aria-labelledby={compacto ? undefined : 'titulo-destacados'} className="destacados">
      {compacto ? (
        <strong>Destacados del período</strong>
      ) : (
        <h4 id="titulo-destacados">Destacados del período</h4>
      )}
      <p className="nota" role="note">
        Descriptivo: cuenta lo que pasó, no es una alerta ni dice qué va a pasar. Un día sin dato no
        cuenta como seco.
      </p>
      {estado.tipo === 'cargando' && <Cargando />}
      {estado.tipo === 'error' && (
        <ErrorEstado mensaje={estado.mensaje} onReintentar={reintentar} />
      )}
      {estado.tipo === 'listo' &&
        (estado.datos.stations[0] ? (
          <ResumenDestacados e={estado.datos.stations[0]} />
        ) : (
          <p className="nota">Sin datos para este período.</p>
        ))}
      {!compacto && normal.estado.tipo === 'listo' && normal.estado.datos && (
        <Normal r={normal.estado.datos} />
      )}
      {!compacto && normal.estado.tipo === 'error' && (
        <p className="nota">No se pudo cargar la normal mensual. {normal.estado.mensaje}</p>
      )}
    </section>
  )
}
