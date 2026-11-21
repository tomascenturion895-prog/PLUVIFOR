import { getNetworkHealth } from '../api/client'
import { useAsync } from '../hooks/useAsync'
import { restarDias } from './fechas'

/**
 * Avisa cuando el período elegido empieza después de la última lectura de toda la red: ahí no
 * puede haber dato, y «sin dato» no es 0 mm. Ofrece ir al último período con dato.
 * La fecha sale de la última lectura real; si no hay ninguna, no se muestra nada ni se inventa.
 */
export default function UltimoPeriodoConDato({
  desde,
  dias,
  onIr,
}: {
  desde: string
  /** Largo del período al que se salta, en días. */
  dias: number
  onIr: (desde: string, hasta: string) => void
}) {
  const salud = useAsync((signal) => getNetworkHealth({}, signal), [])
  if (salud.estado.tipo !== 'listo') return null
  const lecturas = salud.estado.datos.stations
    .map((s) => s.last_reading_date)
    .filter((f): f is string => f !== null)
  if (lecturas.length === 0) return null
  const ultima = lecturas.reduce((a, b) => (a > b ? a : b))
  if (desde <= ultima) return null
  return (
    <p className="nota" role="status">
      Ninguna estación tiene lecturas desde el {desde}: es «sin dato», no 0 mm. La última lectura de
      la red es del {ultima}.{' '}
      <button type="button" onClick={() => onIr(restarDias(ultima, dias - 1), ultima)}>
        Ver el último período con dato
      </button>
    </p>
  )
}
