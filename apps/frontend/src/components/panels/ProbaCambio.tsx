import type { AccumulatedStation, Station } from '../../api/types'
import { Cargando, ErrorEstado } from '../Estados'
import { textoMm } from '../insignias-datos'
import { diferencias } from '../maqueta/maqueta-datos'

export interface Variante {
  desde: string
  hasta: string
  /** Estación extra que se suma a la selección, si hay. */
  extra: number | null
  etiqueta: string
}

interface Props {
  base: Map<number, AccumulatedStation>
  idsBase: number[]
  variante: Variante | null
  varianteDatos: Map<number, AccumulatedStation> | null
  cargando: boolean
  error: string | null
  candidatas: Station[]
  estaciones: Station[]
  onProbar: (accion: 'anterior' | 'ultimos7' | 'ultimos30') => void
  onSumar: (id: number | null) => void
  onLimpiar: () => void
}

function formatoDelta(d: number | null): string {
  if (d === null) return 'no comparable'
  const signo = d > 0 ? '+' : ''
  return `${signo}${d.toLocaleString('es-AR', { maximumFractionDigits: 1 })} mm`
}

export default function ProbaCambio({
  base,
  idsBase,
  variante,
  varianteDatos,
  cargando,
  error,
  candidatas,
  estaciones,
  onProbar,
  onSumar,
  onLimpiar,
}: Props) {
  const ids = variante?.extra != null ? [...idsBase, variante.extra] : idsBase
  const filas = varianteDatos ? diferencias(base, varianteDatos, ids) : []
  const nombre = (id: number) => estaciones.find((s) => s.id === id)?.name ?? `Estación ${id}`
  return (
    <section className="panel" aria-labelledby="panel-cambio">
      <h3 id="panel-cambio">3 · Probá un cambio</h3>
      <div className="acciones">
        <button type="button" onClick={() => onProbar('anterior')}>
          Período anterior
        </button>
        <button type="button" onClick={() => onProbar('ultimos7')}>
          Últimos 7 días
        </button>
        <button type="button" onClick={() => onProbar('ultimos30')}>
          Últimos 30 días
        </button>
      </div>
      <label>
        Sumar una estación
        <select
          value={variante?.extra ?? ''}
          onChange={(e) => onSumar(e.target.value === '' ? null : Number(e.target.value))}
        >
          <option value="">Ninguna</option>
          {candidatas.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name}
            </option>
          ))}
        </select>
      </label>
      {variante && (
        <button type="button" onClick={onLimpiar}>
          Volver a mi selección
        </button>
      )}
      {cargando && <Cargando texto="Calculando la diferencia…" />}
      {error && <ErrorEstado mensaje={error} />}
      {variante && varianteDatos && !cargando && (
        <div
          className="tabla-scroll"
          role="region"
          aria-label="Tabla de la diferencia con el cambio"
          tabIndex={0}
        >
          <table className="tabla-dias">
            <caption className="nota">
              Con el cambio: {variante.etiqueta} ({variante.desde} al {variante.hasta}). La
              diferencia resta dos valores de la API; si a alguno le falta el dato, no se compara.
            </caption>
            <thead>
              <tr>
                <th scope="col">Estación</th>
                <th scope="col">Antes</th>
                <th scope="col">Con el cambio</th>
                <th scope="col">Diferencia</th>
              </tr>
            </thead>
            <tbody>
              {filas.map((f) => (
                <tr key={f.stationId}>
                  <th scope="row">{nombre(f.stationId)}</th>
                  <td>{f.stationId === variante.extra ? '—' : textoMm(f.base)}</td>
                  <td>{textoMm(f.variante)}</td>
                  <td>
                    {f.stationId === variante.extra ? 'estación nueva' : formatoDelta(f.delta)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
