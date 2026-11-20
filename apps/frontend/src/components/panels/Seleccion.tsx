import type { DataCategory, Station } from '../../api/types'
import { FECHA_CORTE } from '../../constants'
import { useIdioma } from '../../i18n/usar-idioma'
import type { ClaveTraduccion } from '../../i18n/traducciones/es'
import { periodoValido, type SeleccionValor } from './panels-datos'

const CATEGORIAS: { valor: DataCategory; clave: ClaveTraduccion }[] = [
  { valor: 'observado', clave: 'insignia.categoria.observado' },
  { valor: 'referencia', clave: 'insignia.categoria.referencia' },
  { valor: 'estimado', clave: 'insignia.categoria.estimado' },
]

interface Props {
  valor: SeleccionValor
  estaciones: Station[]
  departamentos: string[]
  onCambiar: (v: SeleccionValor) => void
}

export default function Seleccion({ valor, estaciones, departamentos, onCambiar }: Props) {
  const { t } = useIdioma()
  const enZona = estaciones.filter((s) => valor.zona === '' || s.department === valor.zona)
  const set = (parcial: Partial<SeleccionValor>) => onCambiar({ ...valor, ...parcial })
  return (
    <section className="panel" aria-labelledby="panel-seleccion">
      <h3 id="panel-seleccion">{t('seleccion.titulo')}</h3>
      <label>
        {t('v3d.departamento')}
        <select value={valor.zona} onChange={(e) => set({ zona: e.target.value, estaciones: [] })}>
          <option value="">{t('seleccion.todaProvincia')}</option>
          {departamentos.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </label>
      <label>
        {t('comun.desde')}
        <input
          type="date"
          value={valor.desde}
          max={FECHA_CORTE}
          onChange={(e) => set({ desde: e.target.value })}
        />
      </label>
      <label>
        {t('comun.hasta')}
        <input
          type="date"
          value={valor.hasta}
          max={FECHA_CORTE}
          onChange={(e) => set({ hasta: e.target.value })}
        />
      </label>
      <label>
        {t('seleccion.categoria')}
        <select
          value={valor.category}
          onChange={(e) => set({ category: e.target.value as DataCategory })}
        >
          {CATEGORIAS.map((c) => (
            <option key={c.valor} value={c.valor}>
              {t(c.clave)}
            </option>
          ))}
        </select>
      </label>
      <fieldset>
        <legend>{t('seleccion.estacionesLeyenda')}</legend>
        {enZona.length === 0 && <p className="nota">{t('seleccion.sinEstacionesZona')}</p>}
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
