import { getSensorReadings } from '../api/client'
import { fechaHoraArgentina, AVISO_SIMULADAS } from '../pages/sensores-datos'
import { formatoMm } from '../pages/network-health-datos'
import { useAsync } from '../hooks/useAsync'
import { Cargando, ErrorEstado, Vacio } from './Estados'
import { InsigniaSimulado } from './Insignias'

const CANTIDAD = 10

/** Últimas lecturas de dispositivos, siempre rotuladas como simuladas (SCRUM-94). */
export default function LecturasSimuladas() {
  const { estado, reintentar } = useAsync(
    (signal) => getSensorReadings({ limit: CANTIDAD }, signal),
    [],
  )

  return (
    <section aria-labelledby="titulo-sensores">
      <h3 id="titulo-sensores">Sensores (simulados)</h3>
      <p className="nota" role="note">
        {estado.tipo === 'listo' ? estado.datos.notice : AVISO_SIMULADAS}
      </p>
      {estado.tipo === 'cargando' && <Cargando />}
      {estado.tipo === 'error' && (
        <ErrorEstado mensaje={estado.mensaje} onReintentar={reintentar} />
      )}
      {estado.tipo === 'listo' &&
        (estado.datos.items.length === 0 ? (
          <Vacio>
            Todavía no llegó ninguna lectura de dispositivos. Para generarlas con el simulador, mirá
            «Demo» en docs/ingesta-sensores.md.
          </Vacio>
        ) : (
          <div
            className="tabla-scroll"
            role="region"
            aria-label="Tabla de lecturas simuladas"
            tabIndex={0}
          >
            <table className="tabla-dias">
              <caption className="nota">
                Últimas {estado.datos.items.length} de {estado.datos.total} lecturas (hora de
                Argentina)
              </caption>
              <thead>
                <tr>
                  <th scope="col">Dispositivo</th>
                  <th scope="col">Fecha y hora</th>
                  <th scope="col">Lluvia medida</th>
                  <th scope="col">Categoría</th>
                </tr>
              </thead>
              <tbody>
                {estado.datos.items.map((lectura) => (
                  <tr key={lectura.id}>
                    <th scope="row">{lectura.device_id}</th>
                    <td>{fechaHoraArgentina(lectura.read_at)}</td>
                    <td>{formatoMm(lectura.mm)}</td>
                    <td>
                      <InsigniaSimulado />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}
    </section>
  )
}
