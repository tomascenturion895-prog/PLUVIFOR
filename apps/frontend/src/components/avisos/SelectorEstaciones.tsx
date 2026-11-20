import type { EstacionRef } from '../../api/types'

/**
 * Elige las estaciones de interés con casillas. Sin ninguna marcada se reciben los avisos de
 * todas las estaciones.
 */
export default function SelectorEstaciones({
  estaciones,
  elegidas,
  onCambio,
  leyenda = 'Estaciones de interés (opcional)',
}: {
  estaciones: EstacionRef[]
  elegidas: number[]
  onCambio: (ids: number[]) => void
  leyenda?: string
}) {
  const alternar = (id: number) =>
    onCambio(elegidas.includes(id) ? elegidas.filter((x) => x !== id) : [...elegidas, id])
  return (
    <fieldset className="selector-estaciones">
      <legend>{leyenda}</legend>
      {estaciones.map((s) => (
        <label key={s.id} className="casilla">
          <input
            type="checkbox"
            checked={elegidas.includes(s.id)}
            onChange={() => alternar(s.id)}
          />
          {s.name} ({s.code})
        </label>
      ))}
      <p className="nota">
        {elegidas.length === 0
          ? 'Ninguna marcada: vas a recibir los avisos de todas las estaciones.'
          : `${elegidas.length} marcada${elegidas.length === 1 ? '' : 's'}.`}
      </p>
    </fieldset>
  )
}
