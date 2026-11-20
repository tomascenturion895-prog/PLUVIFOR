import { useEffect, useState } from 'react'
import {
  aplicarTema,
  almacenLocal,
  DESCRIPCION_TEMA,
  ETIQUETA_TEMA,
  guardarTema,
  leerTema,
  SIMBOLO_TEMA,
  TEMAS,
  type Tema,
} from './tema-datos'

/** Selector de tema (claro, oscuro, daltónico). La elección se guarda en este dispositivo. */
export default function SelectorTema() {
  const [tema, setTema] = useState<Tema>(() => leerTema(almacenLocal()))

  useEffect(() => {
    aplicarTema(document.documentElement, tema)
  }, [tema])

  function elegir(nuevo: Tema) {
    setTema(nuevo)
    guardarTema(almacenLocal(), nuevo)
  }

  return (
    <fieldset className="selector-tema">
      <legend className="sr-only">Tema de color</legend>
      {TEMAS.map((t) => (
        <label key={t} className="selector-tema-opcion" title={DESCRIPCION_TEMA[t]}>
          <input
            type="radio"
            name="tema-de-color"
            value={t}
            checked={tema === t}
            onChange={() => elegir(t)}
          />
          <span className="selector-tema-texto">
            <span aria-hidden="true">{SIMBOLO_TEMA[t]}</span> {ETIQUETA_TEMA[t]}
          </span>
        </label>
      ))}
    </fieldset>
  )
}
