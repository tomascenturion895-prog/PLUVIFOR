import { useState } from 'react'
import { getSensorDevices, getSensorReadings } from '../api/client'
import type { SensorDevice } from '../api/types'
import { Cargando, ErrorEstado, Vacio } from '../components/Estados'
import { InsigniaSimulado } from '../components/Insignias'
import GraficoSensor from '../components/sensores/GraficoSensor'
import { useAsync } from '../hooks/useAsync'
import { useIdioma } from '../i18n/usar-idioma'
import { formatoMm } from './network-health-datos'
import { AVISO_SIMULADAS, fechaHoraArgentina } from './sensores-datos'

const POR_PAGINA = 10
/** Tope de la API: alcanza para unos 6 meses de una lectura diaria. */
const PARA_GRAFICO = 200

function TarjetaDispositivo({
  dispositivo,
  elegido,
  onElegir,
}: {
  dispositivo: SensorDevice
  elegido: boolean
  onElegir: () => void
}) {
  return (
    <li>
      <button
        type="button"
        className={`tarjeta-sensor${elegido ? ' tarjeta-sensor-activa' : ''}`}
        aria-pressed={elegido}
        onClick={onElegir}
      >
        <strong>{dispositivo.device_id}</strong> <InsigniaSimulado />
        <span className="nota">
          Última lectura: {fechaHoraArgentina(dispositivo.last_read_at)} ·{' '}
          {formatoMm(dispositivo.last_mm)}
        </span>
        <span className="nota">
          {dispositivo.readings} {dispositivo.readings === 1 ? 'lectura' : 'lecturas'}
        </span>
      </button>
    </li>
  )
}

function DetalleDispositivo({ dispositivo }: { dispositivo: SensorDevice }) {
  const [pagina, setPagina] = useState(0)
  const grafico = useAsync(
    (signal) => getSensorReadings({ deviceId: dispositivo.device_id, limit: PARA_GRAFICO }, signal),
    [dispositivo.device_id],
  )
  const tabla = useAsync(
    (signal) =>
      getSensorReadings(
        { deviceId: dispositivo.device_id, limit: POR_PAGINA, offset: pagina * POR_PAGINA },
        signal,
      ),
    [dispositivo.device_id, pagina],
  )

  return (
    <div aria-live="polite">
      <h3>{dispositivo.device_id}</h3>
      {grafico.estado.tipo === 'cargando' && <Cargando />}
      {grafico.estado.tipo === 'error' && (
        <ErrorEstado mensaje={grafico.estado.mensaje} onReintentar={grafico.reintentar} />
      )}
      {grafico.estado.tipo === 'listo' && (
        <>
          <GraficoSensor lecturas={grafico.estado.datos.items} />
          {grafico.estado.datos.total > grafico.estado.datos.items.length && (
            <p className="nota">
              El gráfico muestra las últimas {grafico.estado.datos.items.length} de{' '}
              {grafico.estado.datos.total} lecturas.
            </p>
          )}
        </>
      )}

      {tabla.estado.tipo === 'cargando' && <Cargando />}
      {tabla.estado.tipo === 'error' && (
        <ErrorEstado mensaje={tabla.estado.mensaje} onReintentar={tabla.reintentar} />
      )}
      {tabla.estado.tipo === 'listo' && (
        <>
          <div
            className="tabla-scroll"
            role="region"
            aria-label="Tabla de lecturas del dispositivo"
            tabIndex={0}
          >
            <table className="tabla-dias">
              <caption className="nota">
                Lecturas {pagina * POR_PAGINA + 1} a{' '}
                {pagina * POR_PAGINA + tabla.estado.datos.items.length} de{' '}
                {tabla.estado.datos.total} (hora de Argentina)
              </caption>
              <thead>
                <tr>
                  <th scope="col">Fecha y hora</th>
                  <th scope="col">Lluvia medida</th>
                  <th scope="col">Categoría</th>
                </tr>
              </thead>
              <tbody>
                {tabla.estado.datos.items.map((l) => (
                  <tr key={l.id}>
                    <th scope="row">{fechaHoraArgentina(l.read_at)}</th>
                    <td>{formatoMm(l.mm)}</td>
                    <td>
                      <InsigniaSimulado />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="paginacion">
            <button type="button" disabled={pagina === 0} onClick={() => setPagina(pagina - 1)}>
              Anterior
            </button>
            <button
              type="button"
              disabled={(pagina + 1) * POR_PAGINA >= tabla.estado.datos.total}
              onClick={() => setPagina(pagina + 1)}
            >
              Siguiente
            </button>
          </div>
        </>
      )}
    </div>
  )
}

/** Dispositivos simulados: una tarjeta cada uno, con su gráfico y sus lecturas (SCRUM-94). */
export default function Sensores() {
  const { t } = useIdioma()
  const [elegido, setElegido] = useState<string | null>(null)
  const { estado, reintentar } = useAsync((signal) => getSensorDevices(signal), [])

  return (
    <section>
      <h2>{t('nav.sensores')}</h2>
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
          <>
            <ul className="lista-sensores" aria-label="Dispositivos">
              {estado.datos.items.map((d) => (
                <TarjetaDispositivo
                  key={d.device_id}
                  dispositivo={d}
                  elegido={(elegido ?? estado.datos.items[0].device_id) === d.device_id}
                  onElegir={() => setElegido(d.device_id)}
                />
              ))}
            </ul>
            <DetalleDispositivo
              key={elegido ?? estado.datos.items[0].device_id}
              dispositivo={
                estado.datos.items.find((d) => d.device_id === elegido) ?? estado.datos.items[0]
              }
            />
          </>
        ))}
    </section>
  )
}
