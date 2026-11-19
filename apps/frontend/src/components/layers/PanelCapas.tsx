import { CAPAS, type CapaId } from './capas'
import { InsigniaCategoria } from '../Insignias'
import type { TotalCapa } from './capas'

/** Prende y apaga capas. Cada una dice su fuente y su leyenda; una sin datos explica por qué. */
export default function PanelCapas({
  activas,
  totales,
  alCambiar,
}: {
  activas: readonly CapaId[]
  totales: readonly TotalCapa[]
  alCambiar: (id: CapaId) => void
}) {
  return (
    <fieldset className="capas">
      <legend>Capas del mapa</legend>
      <ul>
        {CAPAS.map((capa) => {
          const total = totales.find((t) => t.categoria === capa.categoria)
          const idLeyenda = `capa-${capa.id}-leyenda`
          return (
            <li key={capa.id}>
              <label>
                <input
                  type="checkbox"
                  checked={activas.includes(capa.id)}
                  disabled={Boolean(capa.noDisponible)}
                  aria-describedby={idLeyenda}
                  onChange={() => alCambiar(capa.id)}
                />{' '}
                {capa.nombre}
              </label>{' '}
              {capa.categoria && <InsigniaCategoria categoria={capa.categoria} />}
              <p id={idLeyenda} className="nota">
                {capa.noDisponible ?? capa.leyenda} <br />
                Fuente: {capa.fuente}.
                {total && activas.includes(capa.id) && (
                  <>
                    {' '}
                    <strong>
                      {total.conDato} estación{total.conDato !== 1 ? 'es' : ''} con dato,{' '}
                      {total.sinDato} sin dato.
                    </strong>
                  </>
                )}
              </p>
            </li>
          )
        })}
      </ul>
      <p className="nota">
        Observado, referencia y estimado se muestran por separado: prender varias no las suma ni las
        promedia.
      </p>
    </fieldset>
  )
}
