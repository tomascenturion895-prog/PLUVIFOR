import { useEffect, useState } from 'react'
import type { Mes } from './timeline-datos'
import { siguiente } from './timeline-datos'

const MS_POR_MES = 1200

/** Barra de tiempo con reproducir y pausa. Cada paso es un mes con sus datos reales. */
export default function BarraTiempo({
  meses,
  indice,
  cargando,
  alCambiar,
}: {
  meses: readonly Mes[]
  indice: number
  cargando: boolean
  alCambiar: (indice: number) => void
}) {
  const [reproduciendo, setReproduciendo] = useState(false)
  const ultimo = meses.length - 1

  const enMarcha = reproduciendo && indice < ultimo

  useEffect(() => {
    // Espera a que lleguen los datos del mes antes de pasar al siguiente.
    if (!enMarcha || cargando) return
    const paso = siguiente(indice, meses.length)
    const t = setTimeout(() => {
      alCambiar(paso.indice)
      if (paso.termino) setReproduciendo(false)
    }, MS_POR_MES)
    return () => clearTimeout(t)
  }, [enMarcha, cargando, indice, meses.length, alCambiar])

  if (meses.length === 0) return null
  const actual = meses[Math.min(indice, ultimo)]

  return (
    <section className="barra-tiempo" aria-label="Reproducción mes a mes">
      <button
        type="button"
        onClick={() => {
          if (enMarcha) {
            setReproduciendo(false)
            return
          }
          if (indice >= ultimo) alCambiar(0)
          setReproduciendo(true)
        }}
      >
        {enMarcha ? 'Pausar' : 'Reproducir'}
      </button>
      <label>
        Mes
        <input
          type="range"
          min={0}
          max={ultimo}
          value={Math.min(indice, ultimo)}
          aria-valuetext={`${actual.clave}, del ${actual.desde} al ${actual.hasta}`}
          onChange={(e) => {
            setReproduciendo(false)
            alCambiar(Number(e.target.value))
          }}
        />
      </label>
      <output aria-live="polite">
        {actual.clave} ({indice + 1} de {meses.length})
      </output>
    </section>
  )
}
