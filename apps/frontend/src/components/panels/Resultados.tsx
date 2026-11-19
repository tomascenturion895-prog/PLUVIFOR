import type { AccumulatedOut, AccumulatedStation, Station } from '../../api/types'
import { InsigniaAdvertencia, InsigniaCategoria } from '../Insignias'
import { textoMm } from '../insignias-datos'

interface Props {
  datos: AccumulatedOut
  estaciones: Station[]
  acumulados: Map<number, AccumulatedStation>
}

/** Lo que la API calculó para las estaciones elegidas. Este panel no calcula lluvia. */
export default function Resultados({ datos, estaciones, acumulados }: Props) {
  return (
    <section className="panel" aria-labelledby="panel-resultados">
      <h3 id="panel-resultados">2 · Resultados</h3>
      <p className="metadatos">
        <InsigniaCategoria categoria={datos.category} />{' '}
        <span>
          Del {datos.date_from} al {datos.date_to} ({datos.days_in_period} días) · corte{' '}
          {datos.data_cutoff_date}
        </span>
      </p>
      {estaciones.length === 0 ? (
        <p className="estado estado-vacio">No hay estaciones para esta selección.</p>
      ) : (
        <table className="tabla-dias">
          <caption className="nota">
            Un acumulado por estación; no se suman entre estaciones. Un día sin dato se cuenta
            aparte: no es 0 mm.
          </caption>
          <thead>
            <tr>
              <th scope="col">Estación</th>
              <th scope="col">Acumulado</th>
              <th scope="col">Con dato</th>
              <th scope="col">Sin dato</th>
              <th scope="col">Fuente</th>
              <th scope="col">Advertencias</th>
            </tr>
          </thead>
          <tbody>
            {estaciones.map((s) => {
              const a = acumulados.get(s.id)
              return (
                <tr key={s.id}>
                  <th scope="row">{s.name}</th>
                  <td>{a ? textoMm(a.accumulated_mm) : 'sin dato'}</td>
                  <td>{a ? a.days_with_data : '—'}</td>
                  <td>{a ? a.days_without_data : '—'}</td>
                  <td>{s.source.name}</td>
                  <td>
                    {a?.warnings.length ? (
                      a.warnings.map((w) => (
                        <InsigniaAdvertencia key={w.code} codigo={w.code} mensaje={w.message} />
                      ))
                    ) : (
                      <span className="nota">Ninguna</span>
                    )}
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )}
    </section>
  )
}
