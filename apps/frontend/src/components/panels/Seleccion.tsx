import type { DataCategory, Station } from '../../api/types'
import { FECHA_CORTE } from '../../constants'
import { periodoValido, type SeleccionValor } from './panels-datos'

const CATEGORIAS: { valor: DataCategory; nombre: string }[] = [
  { valor: 'observado', nombre: 'Observado' },
  { valor: 'referencia', nombre: 'Referencia' },
  { valor: 'estimado', nombre: 'Estimado' },
]

interface Props {
  valor: SeleccionValor
  estaciones: Station[]
  departamentos: string[]
  onCambiar: (v: SeleccionValor) => void
}

export default function Seleccion({ valor, estaciones, departamentos, onCambiar }: Props) {
  const enZona = estaciones.filter((s) => valor.zona === '' || s.department === valor.zona)
  const set = (parcial: Partial<SeleccionValor>) => onCambiar({ ...valor, ...parcial })
  return (
    <section className="panel" aria-labelledby="panel-seleccion">
      <h3 id="panel-seleccion">1 · Tu selección</h3>
      <label>
        Departamento
        <select value={valor.zona} onChange={(e) => set({ zona: e.target.value, estaciones: [] })}>
          <option value="">Toda la provincia</option>
          {departamentos.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </label>
      <label>
        Desde
        <input
          type="date"
          value={valor.desde}
          max={FECHA_CORTE}
          onChange={(e) => set({ desde: e.target.value })}
        />
      </label>
      <label>
        Hasta
        <input
          type="date"
          value={valor.hasta}
          max={FECHA_CORTE}
          onChange={(e) => set({ hasta: e.target.value })}
        />
      </label>
      <label>
        Categoría
        <select
          value={valor.category}
          onChange={(e) => set({ category: e.target.value as DataCategory })}
        >
          {CATEGORIAS.map((c) => (
            <option key={c.valor} value={c.valor}>
              {c.nombre}
            </option>
          ))}
        </select>
      </label>
      <fieldset>
        <legend>Estaciones (ninguna marcada = todas las de la zona)</legend>
        {enZona.length === 0 && <p className="nota">No hay estaciones en esta zona.</p>}
        {enZona.map((s) => (
          <label key={s.id} className="opcion">
            <input
              type="checkbox"
              checked={valor.estaciones.includes(s.id)}
              onChange={(e) =>
                set({
                  estaciones: e.target.checked
                    ? [...valor.estaciones, s.id]
                    : valor.estaciones.filter((x) => x !== s.id),
                })
              }
            />
            {s.name}
          </label>
        ))}
      </fieldset>
      {!periodoValido(valor) && (
        <p role="alert" className="estado estado-error">
          Elegí un período válido: «Desde» no puede ser posterior a «Hasta» y ninguna fecha puede
          pasar del {FECHA_CORTE}.
        </p>
      )}
    </section>
  )
}
